"""
FastAPI backend para COLDEX Sectorial Dashboard (stateless, serverless-ready).

Pure Python + openpyxl (sin pandas/numpy) para caber en el lambda de Vercel.

Endpoints:
  POST /api/process  -> recibe el Excel, devuelve todo el JSON procesado.
  POST /api/export   -> recibe el Excel, devuelve el .xlsx formateado.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import io
import math
import tempfile
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from procesar_coldex import (
    generate_workbook,
    read_xlsx_records,
    filter_rows,
    unique_sorted,
    unique_values,
    nunique,
    mean_col,
    round2,
    group_nunique,
    pivot_mean,
    ordered_subcategories,
    is_num,
    SECTOR_MAP,
    TYPE_MAP,
)

app = FastAPI(title="COLDEX Sectorial API", version="2.1.0")

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


def clean_nan(obj):
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def parse_excel(contents: bytes, filename: str):
    if not filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx o .xls")
    try:
        rows = read_xlsx_records(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el Excel: {e}")

    if not rows:
        raise HTTPException(status_code=400, detail="El Excel esta vacio.")

    missing = REQUIRED_COLUMNS - set(rows[0].keys())
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan columnas: {sorted(missing)}")

    return [r for r in rows if r.get("CompanyNameFrom") != r.get("CompanyNameTo")]


# ─── Compute (sobre lista de dicts) ─────────────────────────────────────────

def compute_summary(rows):
    if not rows:
        return {"empty": True}
    companies = unique_sorted(rows, "CompanyNameTo")
    return {
        "empty": False,
        "records": len(rows),
        "companies": len(companies),
        "evaluators": nunique(rows, "CompanyNameFrom"),
        "average": round2(mean_col(rows, "Calification")),
        "companyList": companies,
    }


def compute_subcategories(rows):
    if not rows:
        return []
    companies = unique_sorted(rows, "CompanyNameTo")
    result = []
    for subcat in ordered_subcategories(rows):
        df_sub = filter_rows(rows, PollDesc2=subcat)
        row = {"name": subcat, "average": round2(mean_col(df_sub, "Calification")), "companies": {}}
        for comp in companies:
            val = round2(mean_col(filter_rows(df_sub, CompanyNameTo=comp), "Calification"))
            if val is not None:
                row["companies"][comp] = val
        result.append(row)
    return result


def compute_pivot(rows):
    if not rows:
        return {"companies": [], "rows": []}

    companies = unique_sorted(rows, "CompanyNameTo")

    hierarchy_keys = sorted(
        {(
            r["PollLevel1"], r["PollDesc1"],
            r["PollLevel2"], r["PollDesc2"],
            r["PollLevel3"], r["PollDesc3"],
        ) for r in rows},
        key=lambda t: (t[0], t[2], t[4]),
    )

    pivot = pivot_mean(
        rows,
        ["PollLevel1", "PollDesc1", "PollLevel2", "PollDesc2", "PollLevel3", "PollDesc3"],
        "CompanyNameTo",
        "Calification",
    )

    result_rows = []
    prev_l1 = prev_l2 = None

    for (lvl1, desc1, lvl2, desc2, lvl3, desc3) in hierarchy_keys:
        if desc1 != prev_l1:
            df_l1 = filter_rows(rows, PollDesc1=desc1)
            r = {"level": 1, "label": desc1, "values": {}}
            for comp in companies:
                val = round2(mean_col(filter_rows(df_l1, CompanyNameTo=comp), "Calification"))
                if val is not None:
                    r["values"][comp] = val
            r["total"] = round2(mean_col(df_l1, "Calification"))
            result_rows.append(r)
            prev_l1 = desc1
            prev_l2 = None

        if desc2 != prev_l2:
            df_l2 = filter_rows(rows, PollDesc1=desc1, PollDesc2=desc2)
            r = {"level": 2, "label": desc2, "values": {}}
            for comp in companies:
                val = round2(mean_col(filter_rows(df_l2, CompanyNameTo=comp), "Calification"))
                if val is not None:
                    r["values"][comp] = val
            r["total"] = round2(mean_col(df_l2, "Calification"))
            result_rows.append(r)
            prev_l2 = desc2

        desc3_short = str(desc3)[:100] + "..." if len(str(desc3)) > 100 else str(desc3)
        key = (lvl1, desc1, lvl2, desc2, lvl3, desc3)
        row_map = pivot.get(key, {})
        r = {"level": 3, "label": desc3_short, "values": {}}
        vals_list = []
        for comp in companies:
            val = row_map.get(comp)
            if is_num(val):
                r["values"][comp] = round2(val)
                vals_list.append(val)
        r["total"] = round2(sum(vals_list) / len(vals_list)) if vals_list else None
        result_rows.append(r)

    return {"companies": companies, "rows": result_rows}


def compute_ranking(rows):
    if not rows:
        return []
    companies = unique_sorted(rows, "CompanyNameTo")
    present = ordered_subcategories(rows)

    company_vals = {comp: [] for comp in companies}
    for subcat in present:
        df_sub = filter_rows(rows, PollDesc2=subcat)
        for comp in companies:
            val = mean_col(filter_rows(df_sub, CompanyNameTo=comp), "Calification")
            if val is not None:
                company_vals[comp].append(val)

    eval_counts = group_nunique(rows, "CompanyNameTo", "CompanyNameFrom")

    ranking = []
    for comp in companies:
        vals = company_vals[comp]
        if vals:
            ranking.append({
                "company": comp,
                "score": round2(sum(vals) / len(vals)),
                "evaluators": int(eval_counts.get(comp, 0)),
            })
    ranking.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(ranking):
        r["rank"] = i + 1
    return ranking


def compute_radar(rows, ranking, top=5):
    if not rows:
        return {"companies": [], "subcategories": [], "data": []}
    top_companies = [r["company"] for r in ranking[:top]]
    present = ordered_subcategories(rows)

    data = []
    for comp in top_companies:
        values = []
        for subcat in present:
            df_sub = filter_rows(rows, PollDesc2=subcat, CompanyNameTo=comp)
            val = mean_col(df_sub, "Calification")
            values.append(round2(val) if val is not None else 0)
        data.append({"company": comp, "values": values})
    return {"companies": top_companies, "subcategories": present, "data": data}


def compute_evaluators(rows):
    if not rows:
        return {"counts": [], "matrix": {"from": [], "to": [], "values": []}}

    eval_dict = group_nunique(rows, "CompanyNameTo", "CompanyNameFrom")
    counts = sorted(
        [{"company": comp, "count": cnt} for comp, cnt in eval_dict.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    from_companies = sorted(unique_values(rows, "CompanyNameFrom"))
    to_companies = sorted(unique_values(rows, "CompanyNameTo"))

    matrix_buckets = {}
    for r in rows:
        f = r.get("CompanyNameFrom")
        t = r.get("CompanyNameTo")
        v = r.get("Calification")
        if f is None or t is None or not is_num(v):
            continue
        matrix_buckets.setdefault((f, t), []).append(v)

    values = []
    for f in from_companies:
        row = []
        for t in to_companies:
            bucket = matrix_buckets.get((f, t))
            row.append(round2(sum(bucket) / len(bucket)) if bucket else None)
        values.append(row)

    return {
        "counts": counts,
        "matrix": {"from": from_companies, "to": to_companies, "values": values},
    }


def compute_heatmap(rows):
    if not rows:
        return {"subcategories": [], "companies": [], "values": []}
    companies = unique_sorted(rows, "CompanyNameTo")
    present = ordered_subcategories(rows)

    values = []
    for subcat in present:
        df_sub = filter_rows(rows, PollDesc2=subcat)
        row = []
        for comp in companies:
            val = mean_col(filter_rows(df_sub, CompanyNameTo=comp), "Calification")
            row.append(round2(val) if val is not None else None)
        values.append(row)
    return {"subcategories": present, "companies": companies, "values": values}


def process_all(rows):
    result = {
        "filters": {
            "sectors": [{"code": k, "name": v} for k, v in SECTOR_MAP.items()],
            "types": [{"code": k, "short": v} for k, v in TYPE_MAP.items()],
        },
        "views": {},
    }

    for sector in SECTOR_MAP:
        for type_code in TYPE_MAP:
            sub = filter_rows(rows, IDCategory=sector, IDType=type_code)
            key = f"{sector}|{type_code}"
            summary = compute_summary(sub)
            if summary.get("empty"):
                result["views"][key] = {"summary": summary}
                continue
            ranking = compute_ranking(sub)
            result["views"][key] = {
                "summary": summary,
                "subcategories": compute_subcategories(sub),
                "pivot": compute_pivot(sub),
                "ranking": ranking,
                "radar": compute_radar(sub, ranking),
                "evaluators": compute_evaluators(sub),
                "heatmap": compute_heatmap(sub),
            }
    return result


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/process")
async def process_excel(file: UploadFile = File(...)):
    contents = await file.read()
    rows = parse_excel(contents, file.filename)
    data = process_all(rows)
    data["filename"] = file.filename
    data["records"] = len(rows)
    return clean_nan(data)


@app.post("/api/export")
async def export_excel(file: UploadFile = File(...)):
    contents = await file.read()
    rows = parse_excel(contents, file.filename)

    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    generate_workbook(rows, Path(tmp.name))
    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Procesamiento_LOGYCA_COLDEX_Sectorial.xlsx",
    )
