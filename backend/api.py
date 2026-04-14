"""
FastAPI backend para COLDEX Sectorial Dashboard.
Ejecutar: uvicorn backend.api:app --reload --port 8000
"""

from fastapi import FastAPI, Query, UploadFile, File, HTTPException
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

app = FastAPI(title="COLDEX Sectorial API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


_state = {"df": None, "filename": None}


def load_data():
    df = _state["df"]
    if df is None:
        raise HTTPException(status_code=400, detail="No se ha cargado ningun archivo Excel.")
    return df


def safe_mean(series):
    vals = series.dropna()
    return round(float(vals.mean()), 2) if len(vals) > 0 else None


# ─── Endpoints ──────────────────────────────────────────────────────────────────


@app.get("/api/filters")
def get_filters():
    """Opciones de filtro disponibles."""
    return {
        "sectors": [{"code": k, "name": v} for k, v in SECTOR_MAP.items()],
        "types": [{"code": k, "short": v} for k, v in TYPE_MAP.items()],
    }


@app.get("/api/summary")
def get_summary(sector: str = Query(...), type: str = Query(...)):
    """Metricas resumen para un sector y tipo."""
    df = load_data()
    dfs = df[(df["IDCategory"] == sector) & (df["IDType"] == type)]

    if dfs.empty:
        return {"empty": True}

    companies = sorted(dfs["CompanyNameTo"].unique().tolist())
    evaluators = int(dfs["CompanyNameFrom"].nunique())

    return {
        "empty": False,
        "records": len(dfs),
        "companies": len(companies),
        "evaluators": evaluators,
        "average": round(float(dfs["Calification"].mean()), 2),
        "companyList": companies,
    }


@app.get("/api/subcategories")
def get_subcategories(sector: str = Query(...), type: str = Query(...)):
    """Promedio por subcategoria (para barras y resumen)."""
    df = load_data()
    dfs = df[(df["IDCategory"] == sector) & (df["IDType"] == type)]

    if dfs.empty:
        return []

    companies = sorted(dfs["CompanyNameTo"].unique().tolist())
    present = [s for s in SUBCATEGORY_ORDER if s in dfs["PollDesc2"].unique()]
    for s in sorted(dfs["PollDesc2"].unique()):
        if s not in present:
            present.append(s)

    result = []
    for subcat in present:
        df_sub = dfs[dfs["PollDesc2"] == subcat]
        row = {"name": subcat, "average": safe_mean(df_sub["Calification"]), "companies": {}}
        for comp in companies:
            val = safe_mean(df_sub[df_sub["CompanyNameTo"] == comp]["Calification"])
            if val is not None:
                row["companies"][comp] = val
        result.append(row)

    return result


@app.get("/api/pivot")
def get_pivot(sector: str = Query(...), type: str = Query(...), subcategories: str = Query(default="")):
    """Tabla pivote jerarquica."""
    df = load_data()
    dfs = df[(df["IDCategory"] == sector) & (df["IDType"] == type)]

    if dfs.empty:
        return {"companies": [], "rows": []}

    if subcategories:
        selected = subcategories.split(",")
        dfs = dfs[dfs["PollDesc2"].isin(selected)]

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


@app.get("/api/ranking")
def get_ranking(sector: str = Query(...), type: str = Query(...)):
    """Ranking de empresas."""
    df = load_data()
    dfs = df[(df["IDCategory"] == sector) & (df["IDType"] == type)]

    if dfs.empty:
        return []

    companies = sorted(dfs["CompanyNameTo"].unique().tolist())

    present = [s for s in SUBCATEGORY_ORDER if s in dfs["PollDesc2"].unique()]
    for s in sorted(dfs["PollDesc2"].unique()):
        if s not in present:
            present.append(s)

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


@app.get("/api/radar")
def get_radar(sector: str = Query(...), type: str = Query(...), top: int = Query(default=5)):
    """Datos radar para top N empresas."""
    df = load_data()
    dfs = df[(df["IDCategory"] == sector) & (df["IDType"] == type)]

    if dfs.empty:
        return {"companies": [], "subcategories": [], "data": []}

    ranking = get_ranking(sector=sector, type=type)
    top_companies = [r["company"] for r in ranking[:top]]

    present = [s for s in SUBCATEGORY_ORDER if s in dfs["PollDesc2"].unique()]
    for s in sorted(dfs["PollDesc2"].unique()):
        if s not in present:
            present.append(s)

    data = []
    for comp in top_companies:
        values = []
        for subcat in present:
            df_sub = dfs[(dfs["PollDesc2"] == subcat) & (dfs["CompanyNameTo"] == comp)]
            val = safe_mean(df_sub["Calification"])
            values.append(val if val is not None else 0)
        data.append({"company": comp, "values": values})

    return {"companies": top_companies, "subcategories": present, "data": data}


@app.get("/api/evaluators")
def get_evaluators(sector: str = Query(...), type: str = Query(...)):
    """Conteo de evaluadores y matriz."""
    df = load_data()
    dfs = df[(df["IDCategory"] == sector) & (df["IDType"] == type)]

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

    matrix_data = {
        "from": matrix.index.tolist(),
        "to": matrix.columns.tolist(),
        "values": matrix.where(pd.notna(matrix), None).values.tolist(),
    }

    return {
        "counts": counts.to_dict(orient="records"),
        "matrix": matrix_data,
    }


@app.get("/api/heatmap")
def get_heatmap(sector: str = Query(...), type: str = Query(...)):
    """Heatmap subcategoria x empresa."""
    df = load_data()
    dfs = df[(df["IDCategory"] == sector) & (df["IDType"] == type)]

    if dfs.empty:
        return {"subcategories": [], "companies": [], "values": []}

    companies = sorted(dfs["CompanyNameTo"].unique().tolist())
    present = [s for s in SUBCATEGORY_ORDER if s in dfs["PollDesc2"].unique()]
    for s in sorted(dfs["PollDesc2"].unique()):
        if s not in present:
            present.append(s)

    values = []
    for subcat in present:
        df_sub = dfs[dfs["PollDesc2"] == subcat]
        row = []
        for comp in companies:
            val = safe_mean(df_sub[df_sub["CompanyNameTo"] == comp]["Calification"])
            row.append(val)
        values.append(row)

    return {"subcategories": present, "companies": companies, "values": values}


@app.get("/api/status")
def get_status():
    """Indica si hay un archivo cargado."""
    return {"loaded": _state["df"] is not None, "filename": _state["filename"]}


@app.post("/api/upload")
async def upload_excel(file: UploadFile = File(...)):
    """Carga un archivo Excel en memoria como fuente de datos."""
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx o .xls")
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name=0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el Excel: {e}")

    required = {"CompanyNameFrom", "CompanyNameTo", "IDCategory", "IDType", "Calification", "PollDesc2"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan columnas en el Excel: {sorted(missing)}")

    df = df[df["CompanyNameFrom"] != df["CompanyNameTo"]].copy()
    _state["df"] = df
    _state["filename"] = file.filename
    return {"loaded": True, "filename": file.filename, "records": len(df)}


@app.post("/api/export")
def export_excel():
    """Genera y descarga el Excel procesado a partir del archivo cargado."""
    df = load_data()
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    generate_workbook(df, Path(tmp.name))
    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Procesamiento_COLDEX_Sectorial_2025.xlsx",
    )
