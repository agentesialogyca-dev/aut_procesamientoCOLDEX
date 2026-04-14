"""
FastAPI backend para COLDEX Sectorial Dashboard (stateless, serverless-ready).

Dos endpoints:
  POST /api/process  -> recibe el Excel, devuelve todo el JSON procesado.
  POST /api/export   -> recibe el Excel, devuelve el .xlsx formateado.

Local dev: uvicorn backend.api:app --reload --port 8000
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import numpy as np
from pathlib import Path
import io
import tempfile
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procesar_coldex import (
    generate_workbook,
    SECTOR_MAP,
    TYPE_MAP,
    SUBCATEGORY_ORDER,
)

app = FastAPI(title="COLDEX Sectorial API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_COLUMNS = {
    "CompanyNameFrom", "CompanyNameTo", "IDCategory", "IDType",
    "Calification", "PollDesc1", "PollDesc2", "PollDesc3",
    "PollLevel1", "PollLevel2", "PollLevel3",
}


def safe_mean(series):
    vals = series.dropna()
    return round(float(vals.mean()), 2) if len(vals) > 0 else None


def clean_nan(obj):
    """Reemplaza NaN por None recursivamente para que sea JSON-compliant."""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj


def parse_excel(contents: bytes, filename: str) -> pd.DataFrame:
    if not filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx o .xls")
    try:
        df = pd.read_excel(io.BytesIO(contents), sheet_name=0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el Excel: {e}")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan columnas: {sorted(missing)}")

    return df[df["CompanyNameFrom"] != df["CompanyNameTo"]].copy()


# ─── Compute functions (puras, reciben DataFrame) ────────────────────────────

def compute_summary(dfs):
    if dfs.empty:
        return {"empty": True}
    companies = sorted(dfs["CompanyNameTo"].unique().tolist())
    return {
        "empty": False,
        "records": len(dfs),
        "companies": len(companies),
        "evaluators": int(dfs["CompanyNameFrom"].nunique()),
        "average": round(float(dfs["Calification"].mean()), 2),
        "companyList": companies,
    }


def ordered_subcategories(dfs):
    unique = dfs["PollDesc2"].unique()
    present = [s for s in SUBCATEGORY_ORDER if s in unique]
    for s in sorted(unique):
        if s not in present:
            present.append(s)
    return present


def compute_subcategories(dfs):
    if dfs.empty:
        return []
    companies = sorted(dfs["CompanyNameTo"].unique().tolist())
    result = []
    for subcat in ordered_subcategories(dfs):
        df_sub = dfs[dfs["PollDesc2"] == subcat]
        row = {"name": subcat, "average": safe_mean(df_sub["Calification"]), "companies": {}}
        for comp in companies:
            val = safe_mean(df_sub[df_sub["CompanyNameTo"] == comp]["Calification"])
            if val is not None:
                row["companies"][comp] = val
        result.append(row)
    return result


def compute_pivot(dfs):
    if dfs.empty:
        return {"companies": [], "rows": []}

    companies = sorted(dfs["CompanyNameTo"].unique().tolist())
    pivot = dfs.pivot_table(
        values="Calification",
        index=["PollLevel1", "PollDesc1", "PollLevel2", "PollDesc2", "PollLevel3", "PollDesc3"],
        columns="CompanyNameTo",
        aggfunc="mean",
    ).round(2)

    rows = []
    prev_l1 = prev_l2 = None
    for (lvl1, desc1, lvl2, desc2, lvl3, desc3) in pivot.index:
        if desc1 != prev_l1:
            df_l1 = dfs[dfs["PollDesc1"] == desc1]
            r = {"level": 1, "label": desc1, "values": {}}
            for comp in companies:
                val = safe_mean(df_l1[df_l1["CompanyNameTo"] == comp]["Calification"])
                if val is not None:
                    r["values"][comp] = val
            r["total"] = safe_mean(df_l1["Calification"])
            rows.append(r)
            prev_l1 = desc1
            prev_l2 = None

        if desc2 != prev_l2:
            df_l2 = dfs[(dfs["PollDesc1"] == desc1) & (dfs["PollDesc2"] == desc2)]
            r = {"level": 2, "label": desc2, "values": {}}
            for comp in companies:
                val = safe_mean(df_l2[df_l2["CompanyNameTo"] == comp]["Calification"])
                if val is not None:
                    r["values"][comp] = val
            r["total"] = safe_mean(df_l2["Calification"])
            rows.append(r)
            prev_l2 = desc2

        desc3_short = str(desc3)[:100] + "..." if len(str(desc3)) > 100 else str(desc3)
        row_data = pivot.loc[(lvl1, desc1, lvl2, desc2, lvl3, desc3)]
        r = {"level": 3, "label": desc3_short, "values": {}}
        vals_list = []
        for comp in companies:
            val = row_data.get(comp, None)
            if pd.notna(val):
                r["values"][comp] = round(float(val), 2)
                vals_list.append(float(val))
        r["total"] = round(float(np.mean(vals_list)), 2) if vals_list else None
        rows.append(r)

    return {"companies": companies, "rows": rows}


def compute_ranking(dfs):
    if dfs.empty:
        return []
    companies = sorted(dfs["CompanyNameTo"].unique().tolist())
    present = ordered_subcategories(dfs)

    company_vals = {comp: [] for comp in companies}
    for subcat in present:
        df_sub = dfs[dfs["PollDesc2"] == subcat]
        for comp in companies:
            val = safe_mean(df_sub[df_sub["CompanyNameTo"] == comp]["Calification"])
            if val is not None:
                company_vals[comp].append(val)

    eval_counts = dfs.groupby("CompanyNameTo")["CompanyNameFrom"].nunique().to_dict()

    ranking = []
    for comp in companies:
        if company_vals[comp]:
            ranking.append({
                "company": comp,
                "score": round(float(np.mean(company_vals[comp])), 2),
                "evaluators": int(eval_counts.get(comp, 0)),
            })
    ranking.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(ranking):
        r["rank"] = i + 1
    return ranking


def compute_radar(dfs, ranking, top=5):
    if dfs.empty:
        return {"companies": [], "subcategories": [], "data": []}
    top_companies = [r["company"] for r in ranking[:top]]
    present = ordered_subcategories(dfs)

    data = []
    for comp in top_companies:
        values = []
        for subcat in present:
            df_sub = dfs[(dfs["PollDesc2"] == subcat) & (dfs["CompanyNameTo"] == comp)]
            val = safe_mean(df_sub["Calification"])
            values.append(val if val is not None else 0)
        data.append({"company": comp, "values": values})
    return {"companies": top_companies, "subcategories": present, "data": data}


def compute_evaluators(dfs):
    if dfs.empty:
        return {"counts": [], "matrix": {"from": [], "to": [], "values": []}}

    counts = (
        dfs.groupby("CompanyNameTo")["CompanyNameFrom"]
        .nunique()
        .reset_index()
        .rename(columns={"CompanyNameFrom": "count", "CompanyNameTo": "company"})
        .sort_values("count", ascending=False)
    )

    matrix = dfs.pivot_table(
        values="Calification",
        index="CompanyNameFrom",
        columns="CompanyNameTo",
        aggfunc="mean",
    ).round(2)

    return {
        "counts": counts.to_dict(orient="records"),
        "matrix": {
            "from": matrix.index.tolist(),
            "to": matrix.columns.tolist(),
            "values": matrix.where(pd.notna(matrix), None).values.tolist(),
        },
    }


def compute_heatmap(dfs):
    if dfs.empty:
        return {"subcategories": [], "companies": [], "values": []}
    companies = sorted(dfs["CompanyNameTo"].unique().tolist())
    present = ordered_subcategories(dfs)

    values = []
    for subcat in present:
        df_sub = dfs[dfs["PollDesc2"] == subcat]
        row = []
        for comp in companies:
            val = safe_mean(df_sub[df_sub["CompanyNameTo"] == comp]["Calification"])
            row.append(val)
        values.append(row)
    return {"subcategories": present, "companies": companies, "values": values}


def process_all(df):
    """Calcula todas las vistas para todas las combinaciones sector x tipo."""
    result = {
        "filters": {
            "sectors": [{"code": k, "name": v} for k, v in SECTOR_MAP.items()],
            "types": [{"code": k, "short": v} for k, v in TYPE_MAP.items()],
        },
        "views": {},
    }

    for sector in SECTOR_MAP:
        for type_code in TYPE_MAP:
            dfs = df[(df["IDCategory"] == sector) & (df["IDType"] == type_code)]
            key = f"{sector}|{type_code}"
            summary = compute_summary(dfs)
            if summary.get("empty"):
                result["views"][key] = {"summary": summary}
                continue
            ranking = compute_ranking(dfs)
            result["views"][key] = {
                "summary": summary,
                "subcategories": compute_subcategories(dfs),
                "pivot": compute_pivot(dfs),
                "ranking": ranking,
                "radar": compute_radar(dfs, ranking),
                "evaluators": compute_evaluators(dfs),
                "heatmap": compute_heatmap(dfs),
            }
    return result


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/process")
async def process_excel(file: UploadFile = File(...)):
    """Recibe el Excel y devuelve todo el dataset procesado."""
    contents = await file.read()
    df = parse_excel(contents, file.filename)
    data = process_all(df)
    data["filename"] = file.filename
    data["records"] = len(df)
    return clean_nan(data)


@app.post("/api/export")
async def export_excel(file: UploadFile = File(...)):
    """Recibe el Excel y devuelve el .xlsx formateado."""
    contents = await file.read()
    df = parse_excel(contents, file.filename)

    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    generate_workbook(df, Path(tmp.name))
    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Procesamiento_COLDEX_Sectorial_2025.xlsx",
    )
