"""
Automatización del Procesamiento de Resultados COLDEX Sectorial.
Genera un Excel con una hoja por cada combinación Sector × Tipo (IND/CAD).
"""

import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from pathlib import Path

# ─── Configuración ──────────────────────────────────────────────────────────────

DATA_DIR = Path("data")
OUTPUT_FILE = DATA_DIR / "Procesamiento_Resultados_Coldex_Sectorial_2025.xlsx"


def find_input_file():
    """Busca el primer archivo .xlsx en data/ que no sea el de salida."""
    xlsx_files = [
        f for f in sorted(DATA_DIR.glob("*.xlsx"))
        if f != OUTPUT_FILE and not f.name.startswith("~$")
    ]
    if not xlsx_files:
        raise FileNotFoundError(f"No se encontró ningún archivo .xlsx en {DATA_DIR}/")
    return xlsx_files[0]


def read_input_excel(path=None):
    """Lee el archivo de entrada usando la primera hoja disponible."""
    path = path or find_input_file()
    return pd.read_excel(path, sheet_name=0)

SECTOR_MAP = {
    "TXT": "Textil",
    "ELT": "Electro",
    "CNS": "Consumo",
    "HGR": "Hogar",
    "SLD": "Salud",
    "SLDI": "Salud Insumos",
}

TYPE_MAP = {
    "INDUSTRIAL": "IND",
    "CADENA": "CAD",
}

# Orden deseado de subcategorías (PollDesc2)
SUBCATEGORY_ORDER = [
    "Gestión Comercial",
    "Relacionamiento y Comunicación",
    "Calidad de Datos",
    "Estándares",
    "Gestión de Devoluciones",
    "Gestión de Pedidos",
    "Gestión Logística",
    "Operadores Logísticos",
    "Omnicanalidad",
    "Gestión de Indicadores",
    "Gestión de la Demanda",
    "Gestión de Punto de Venta",
    "Sostenibilidad",
]

# ─── Estilos ────────────────────────────────────────────────────────────────────

FONT_BASE = Font(name="Aptos Narrow", size=11)
FONT_BOLD = Font(name="Aptos Narrow", size=11, bold=True)
FONT_HEADER = Font(name="Aptos Narrow", size=11, bold=True)

FILL_HEADER = PatternFill(start_color="C0E6F5", end_color="C0E6F5", fill_type="solid")
FILL_GREEN = PatternFill(start_color="47D359", end_color="47D359", fill_type="solid")
FILL_CELESTE = PatternFill(start_color="C0E6F5", end_color="C0E6F5", fill_type="solid")

BORDER_THIN_BLUE = Border(
    left=Side(style="thin", color="44B3E1"),
    right=Side(style="thin", color="44B3E1"),
    top=Side(style="thin", color="44B3E1"),
    bottom=Side(style="thin", color="44B3E1"),
)

NUMBER_FORMAT = "0.00"


def set_cell(ws, row, col, value, font=None, fill=None, border=None, number_format=None, alignment=None):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = font or FONT_BASE
    if fill:
        cell.fill = fill
    if border:
        cell.border = border
    if number_format and value is not None and not (isinstance(value, float) and np.isnan(value)):
        cell.number_format = number_format
    if alignment:
        cell.alignment = alignment
    return cell


def apply_row_style(ws, row, max_col, font=None, fill=None, border=None):
    for col in range(1, max_col + 1):
        cell = ws.cell(row=row, column=col)
        if font:
            cell.font = font
        if fill:
            cell.fill = fill
        if border:
            cell.border = border


def safe_mean(series):
    vals = series.dropna()
    return vals.mean() if len(vals) > 0 else None


def build_sheet(wb, df_sector, id_poll, id_category, id_type, sector_name, type_short):
    """Construye una hoja de procesamiento para una combinación sector × tipo."""
    sheet_name = f"Proc {sector_name} {type_short}"
    if len(sheet_name) > 31:
        sheet_name = sheet_name[:31]
    ws = wb.create_sheet(title=sheet_name)

    if df_sector.empty:
        set_cell(ws, 1, 1, "Sin datos para esta combinación")
        return

    # ─── Sección A: Encabezado ──────────────────────────────────────────────
    set_cell(ws, 1, 1, "IDPoll", font=FONT_BOLD)
    set_cell(ws, 1, 2, id_poll)
    set_cell(ws, 2, 1, "IDCategory", font=FONT_BOLD)
    set_cell(ws, 2, 2, id_category)
    set_cell(ws, 3, 1, "IDType", font=FONT_BOLD)
    set_cell(ws, 3, 2, id_type)

    # Empresas evaluadas (columnas de la pivote), orden alfabético
    companies = sorted(df_sector["CompanyNameTo"].unique())
    num_companies = len(companies)
    total_cols = num_companies + 2  # col A (etiquetas) + empresas + Total general

    # ─── Sección B: Tabla Pivote de Calificaciones ──────────────────────────
    ROW_PIVOT_TITLE = 5
    ROW_PIVOT_HEADER = 6
    ROW_PIVOT_START = 7

    set_cell(ws, ROW_PIVOT_TITLE, 1, "Promedio de Calification", font=FONT_HEADER, fill=FILL_HEADER)
    set_cell(ws, ROW_PIVOT_TITLE, 2, "Etiquetas de columna", font=FONT_HEADER, fill=FILL_HEADER)
    for i in range(3, total_cols + 1):
        set_cell(ws, ROW_PIVOT_TITLE, i, None, fill=FILL_HEADER)

    # Header row: Etiquetas de fila | empresa1 | empresa2 | ... | Total general
    set_cell(ws, ROW_PIVOT_HEADER, 1, "Etiquetas de fila", font=FONT_HEADER, fill=FILL_HEADER)
    for ci, comp in enumerate(companies):
        set_cell(ws, ROW_PIVOT_HEADER, ci + 2, comp, font=FONT_HEADER, fill=FILL_HEADER)
    set_cell(ws, ROW_PIVOT_HEADER, num_companies + 2, "Total general", font=FONT_HEADER, fill=FILL_HEADER)

    # Construir la estructura jerárquica
    # Agrupar por PollDesc1 → PollDesc2 → PollDesc3
    hierarchy = (
        df_sector.groupby(["PollLevel1", "PollDesc1", "PollLevel2", "PollDesc2", "PollLevel3", "PollDesc3"])
        .size()
        .reset_index(name="_count")
        .sort_values(["PollLevel1", "PollLevel2", "PollLevel3"])
    )

    # Pivot: promedio de calificación por PollDesc3 × CompanyNameTo
    pivot = df_sector.pivot_table(
        values="Calification",
        index=["PollLevel1", "PollDesc1", "PollLevel2", "PollDesc2", "PollLevel3", "PollDesc3"],
        columns="CompanyNameTo",
        aggfunc="mean",
    )

    # Guardar referencia de filas para la sección C
    subcategory_rows = {}  # PollDesc2 -> list of row numbers (nivel 3)

    current_row = ROW_PIVOT_START
    prev_level1 = None
    prev_level2 = None

    for (lvl1, desc1, lvl2, desc2, lvl3, desc3) in pivot.index:
        # Nivel 1
        if desc1 != prev_level1:
            set_cell(ws, current_row, 1, desc1, font=FONT_BOLD)
            apply_row_style(ws, current_row, total_cols, border=BORDER_THIN_BLUE)
            ws.cell(row=current_row, column=1).font = FONT_BOLD
            # Promedio nivel 1 por empresa
            df_level1 = df_sector[df_sector["PollDesc1"] == desc1]
            for ci, comp in enumerate(companies):
                val = safe_mean(df_level1[df_level1["CompanyNameTo"] == comp]["Calification"])
                if val is not None:
                    set_cell(ws, current_row, ci + 2, round(val, 2), font=FONT_BOLD, number_format=NUMBER_FORMAT)
            # Total general nivel 1
            val = safe_mean(df_level1["Calification"])
            if val is not None:
                set_cell(ws, current_row, num_companies + 2, round(val, 2), font=FONT_BOLD, number_format=NUMBER_FORMAT)
            current_row += 1
            prev_level1 = desc1
            prev_level2 = None

        # Nivel 2
        if desc2 != prev_level2:
            set_cell(ws, current_row, 1, f"  {desc2}", font=FONT_BOLD)
            apply_row_style(ws, current_row, total_cols, border=BORDER_THIN_BLUE)
            ws.cell(row=current_row, column=1).font = FONT_BOLD
            # Promedio nivel 2 por empresa
            df_level2 = df_sector[(df_sector["PollDesc1"] == desc1) & (df_sector["PollDesc2"] == desc2)]
            for ci, comp in enumerate(companies):
                val = safe_mean(df_level2[df_level2["CompanyNameTo"] == comp]["Calification"])
                if val is not None:
                    set_cell(ws, current_row, ci + 2, round(val, 2), font=FONT_BOLD, number_format=NUMBER_FORMAT)
            # Total general nivel 2
            val = safe_mean(df_level2["Calification"])
            if val is not None:
                set_cell(ws, current_row, num_companies + 2, round(val, 2), font=FONT_BOLD, number_format=NUMBER_FORMAT)
            current_row += 1
            prev_level2 = desc2
            if desc2 not in subcategory_rows:
                subcategory_rows[desc2] = []

        # Nivel 3: pregunta individual
        # Truncar texto largo para que quepa
        desc3_display = desc3 if len(str(desc3)) <= 120 else str(desc3)[:117] + "..."
        set_cell(ws, current_row, 1, f"    {desc3_display}")

        row_data = pivot.loc[(lvl1, desc1, lvl2, desc2, lvl3, desc3)]
        company_vals = []
        for ci, comp in enumerate(companies):
            val = row_data.get(comp, None)
            if pd.notna(val):
                set_cell(ws, current_row, ci + 2, round(val, 2), number_format=NUMBER_FORMAT)
                company_vals.append(val)
            else:
                company_vals.append(None)

        # Total general para esta pregunta
        valid_vals = [v for v in company_vals if v is not None]
        if valid_vals:
            total_val = np.mean(valid_vals)
            set_cell(ws, current_row, num_companies + 2, round(total_val, 2), number_format=NUMBER_FORMAT)

        subcategory_rows[desc2].append(current_row)
        current_row += 1

    # Fila Total General
    row_total_general = current_row
    set_cell(ws, row_total_general, 1, "Total general", font=FONT_BOLD, fill=FILL_HEADER)
    for ci, comp in enumerate(companies):
        val = safe_mean(df_sector[df_sector["CompanyNameTo"] == comp]["Calification"])
        if val is not None:
            set_cell(ws, row_total_general, ci + 2, round(val, 2), font=FONT_BOLD, number_format=NUMBER_FORMAT, fill=FILL_HEADER)
    val = safe_mean(df_sector["Calification"])
    if val is not None:
        set_cell(ws, row_total_general, num_companies + 2, round(val, 2), font=FONT_BOLD, number_format=NUMBER_FORMAT, fill=FILL_HEADER)

    current_row = row_total_general + 3

    # ─── Sección C: Resumen por Subcategoría ────────────────────────────────
    ROW_RESUMEN_HEADER = current_row
    set_cell(ws, ROW_RESUMEN_HEADER, 1, "Subcategoría", font=FONT_HEADER, fill=FILL_HEADER)
    for ci, comp in enumerate(companies):
        set_cell(ws, ROW_RESUMEN_HEADER, ci + 2, comp, font=FONT_HEADER, fill=FILL_HEADER)
    set_cell(ws, ROW_RESUMEN_HEADER, num_companies + 2, "Total general", font=FONT_HEADER, fill=FILL_HEADER)

    current_row = ROW_RESUMEN_HEADER + 1

    # Calcular promedios por subcategoría directamente de los datos
    subcategory_avgs = {}  # comp -> promedio general
    company_subcat_vals = {comp: [] for comp in companies}

    present_subcats = [s for s in SUBCATEGORY_ORDER if s in df_sector["PollDesc2"].unique()]
    # Agregar cualquier subcategoría no listada
    for s in sorted(df_sector["PollDesc2"].unique()):
        if s not in present_subcats:
            present_subcats.append(s)

    for subcat in present_subcats:
        set_cell(ws, current_row, 1, subcat, font=FONT_BASE)
        df_sub = df_sector[df_sector["PollDesc2"] == subcat]

        all_subcat_vals = []
        for ci, comp in enumerate(companies):
            val = safe_mean(df_sub[df_sub["CompanyNameTo"] == comp]["Calification"])
            if val is not None:
                set_cell(ws, current_row, ci + 2, round(val, 2), number_format=NUMBER_FORMAT)
                company_subcat_vals[comp].append(val)
                all_subcat_vals.append(val)

        if all_subcat_vals:
            set_cell(ws, current_row, num_companies + 2, round(np.mean(all_subcat_vals), 2), number_format=NUMBER_FORMAT)

        current_row += 1

    # Fila promedio general subcategorías
    row_avg_subcat = current_row
    set_cell(ws, row_avg_subcat, 1, "Total general", font=FONT_BOLD, fill=FILL_HEADER)
    company_general_avg = {}
    for ci, comp in enumerate(companies):
        vals = company_subcat_vals[comp]
        if vals:
            avg = np.mean(vals)
            company_general_avg[comp] = round(avg, 2)
            set_cell(ws, row_avg_subcat, ci + 2, round(avg, 2), font=FONT_BOLD, number_format=NUMBER_FORMAT, fill=FILL_HEADER)

    all_avgs = [v for v in company_general_avg.values()]
    if all_avgs:
        set_cell(ws, row_avg_subcat, num_companies + 2, round(np.mean(all_avgs), 2), font=FONT_BOLD, number_format=NUMBER_FORMAT, fill=FILL_HEADER)

    current_row = row_avg_subcat + 3

    # ─── Sección E: Conteo de Evaluadores (antes del ranking para poder usarlo) ─
    evaluator_counts = (
        df_sector.groupby("CompanyNameTo")["CompanyNameFrom"]
        .nunique()
        .reset_index()
        .rename(columns={"CompanyNameFrom": "num_evaluadores"})
    )
    eval_dict = dict(zip(evaluator_counts["CompanyNameTo"], evaluator_counts["num_evaluadores"]))

    # ─── Sección D: Ranking de Empresas ─────────────────────────────────────
    ROW_RANKING_TITLE = current_row
    set_cell(ws, ROW_RANKING_TITLE, 2, "EMPRESA", font=FONT_HEADER, fill=FILL_HEADER)
    set_cell(ws, ROW_RANKING_TITLE, 3, "PUNTAJE", font=FONT_HEADER, fill=FILL_HEADER)
    set_cell(ws, ROW_RANKING_TITLE, 4, "PUESTO", font=FONT_HEADER, fill=FILL_HEADER)
    set_cell(ws, ROW_RANKING_TITLE, 5, "CANT EVALUADORES", font=FONT_HEADER, fill=FILL_HEADER)

    # Ordenar por puntaje descendente
    ranking_data = sorted(company_general_avg.items(), key=lambda x: x[1], reverse=True)

    current_row = ROW_RANKING_TITLE + 1
    top_n = min(7, len(ranking_data))

    for rank, (comp, score) in enumerate(ranking_data, 1):
        # Determinar estilo
        if rank <= top_n:
            fill = FILL_GREEN
            font = Font(name="Aptos Narrow", size=11, bold=True, color="000000")
        else:
            fill = FILL_CELESTE
            font = Font(name="Aptos Narrow", size=11, color="FF0000")

        set_cell(ws, current_row, 2, comp, font=font, fill=fill)
        set_cell(ws, current_row, 3, score, font=font, fill=fill, number_format=NUMBER_FORMAT)
        set_cell(ws, current_row, 4, rank, font=font, fill=fill)
        set_cell(ws, current_row, 5, eval_dict.get(comp, 0), font=font, fill=fill)
        current_row += 1

    current_row += 2

    # ─── Sección E: Conteo de Evaluadores ───────────────────────────────────
    ROW_EVAL_TITLE = current_row
    set_cell(ws, ROW_EVAL_TITLE, 1, "Etiquetas de fila", font=FONT_HEADER, fill=FILL_HEADER)
    set_cell(ws, ROW_EVAL_TITLE, 2, "# Empresas que lo evaluaron", font=FONT_HEADER, fill=FILL_HEADER)

    current_row = ROW_EVAL_TITLE + 1
    for _, row in evaluator_counts.sort_values("CompanyNameTo").iterrows():
        set_cell(ws, current_row, 1, row["CompanyNameTo"])
        set_cell(ws, current_row, 2, int(row["num_evaluadores"]))
        current_row += 1

    # ─── Ajustar anchos de columna ──────────────────────────────────────────
    ws.column_dimensions["A"].width = 45
    for ci in range(2, total_cols + 1):
        ws.column_dimensions[get_column_letter(ci)].width = 18


def generate_workbook(df, output_path):
    """Construye el workbook a partir de un DataFrame ya cargado y lo guarda."""
    wb = Workbook()
    wb.remove(wb.active)

    for id_category, sector_name in SECTOR_MAP.items():
        for id_type, type_short in TYPE_MAP.items():
            df_filtered = df[
                (df["IDCategory"] == id_category) & (df["IDType"] == id_type)
            ].copy()
            id_poll = df_filtered["IDPoll"].iloc[0] if not df_filtered.empty else "DV"
            build_sheet(wb, df_filtered, id_poll, id_category, id_type, sector_name, type_short)

    wb.save(output_path)
    return output_path


def main():
    print("Leyendo archivo fuente...")
    df = read_input_excel()
    auto_eval = len(df[df["CompanyNameFrom"] == df["CompanyNameTo"]])
    df = df[df["CompanyNameFrom"] != df["CompanyNameTo"]].copy()
    print(f"  Filas totales: {len(df)} (excluidas {auto_eval} auto-evaluaciones)")
    print(f"\nGuardando resultado en: {OUTPUT_FILE}")
    generate_workbook(df, OUTPUT_FILE)
    print("Listo!")


if __name__ == "__main__":
    main()
