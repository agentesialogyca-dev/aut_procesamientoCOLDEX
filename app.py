"""
COLDEX Sectorial - Dashboard de Resultados
Ejecutar: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from procesar_coldex import (
    main as generar_excel,
    OUTPUT_FILE,
    SECTOR_MAP,
    TYPE_MAP,
    SUBCATEGORY_ORDER,
    read_input_excel,
)

# ─── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="COLDEX Sectorial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Theme & CSS ────────────────────────────────────────────────────────────────

COLORS = {
    "primary": "#0066CC",
    "primary_light": "#E8F4FD",
    "accent": "#44B3E1",
    "green": "#47D359",
    "green_light": "#E8F8EA",
    "bg": "#F7F9FC",
    "card": "#FFFFFF",
    "text": "#1A1A2E",
    "text_secondary": "#6B7280",
    "border": "#E5E7EB",
    "danger": "#EF4444",
}

st.markdown(f"""
<style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {{
        background-color: {COLORS['bg']};
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0A1628 0%, #132D5E 100%);
        border-right: none;
    }}
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] label {{
        color: #FFFFFF !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox label {{
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }}

    /* ── Hide default header/footer ── */
    #MainMenu, header, footer {{ visibility: hidden; }}

    /* ── Cards ── */
    .metric-card {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        text-align: center;
        transition: box-shadow 0.2s;
    }}
    .metric-card:hover {{
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}
    .metric-card .value {{
        font-size: 2rem;
        font-weight: 700;
        color: {COLORS['text']};
        line-height: 1.2;
    }}
    .metric-card .label {{
        font-size: 0.8rem;
        color: {COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 0.3rem;
        font-weight: 500;
    }}
    .metric-card.accent .value {{ color: {COLORS['primary']}; }}
    .metric-card.green .value {{ color: #16A34A; }}

    /* ── Section headers ── */
    .section-header {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {COLORS['text']};
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid {COLORS['accent']};
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* ── Data tables ── */
    .stDataFrame {{
        border-radius: 10px;
        overflow: hidden;
    }}

    /* ── Ranking table ── */
    .ranking-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 10px;
        overflow: hidden;
        font-size: 0.9rem;
    }}
    .ranking-table th {{
        background: {COLORS['primary']};
        color: white;
        padding: 0.75rem 1rem;
        text-align: left;
        font-weight: 600;
    }}
    .ranking-table td {{
        padding: 0.65rem 1rem;
        border-bottom: 1px solid {COLORS['border']};
    }}
    .ranking-table tr.top {{
        background: {COLORS['green_light']};
    }}
    .ranking-table tr.top td:first-child {{
        font-weight: 700;
        color: #16A34A;
    }}
    .ranking-table tr.rest {{
        background: {COLORS['primary_light']};
    }}
    .ranking-table tr.rest td:first-child {{
        color: {COLORS['primary']};
        font-weight: 600;
    }}
    .ranking-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        font-weight: 700;
        font-size: 0.8rem;
    }}
    .badge-gold {{ background: #FCD34D; color: #92400E; }}
    .badge-silver {{ background: #D1D5DB; color: #374151; }}
    .badge-bronze {{ background: #FDBA74; color: #9A3412; }}
    .badge-default {{ background: {COLORS['border']}; color: {COLORS['text_secondary']}; }}

    /* ── Evaluator cards ── */
    .eval-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.75rem;
    }}
    .eval-card {{
        background: white;
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }}
    .eval-card .name {{
        font-weight: 600;
        color: {COLORS['text']};
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .eval-card .count {{
        font-size: 1.5rem;
        font-weight: 700;
        color: {COLORS['primary']};
    }}

    /* ── Nav styling ── */
    .nav-link {{
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }}

    /* ── Heatmap tooltip ── */
    .subcategory-bar {{
        background: white;
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 1rem;
    }}

    /* ── Download button ── */
    section[data-testid="stSidebar"] .stDownloadButton > button {{
        background: linear-gradient(135deg, {COLORS['green']} 0%, #2ECC71 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 0.6rem 1rem !important;
    }}
    section[data-testid="stSidebar"] .stDownloadButton > button:hover {{
        opacity: 0.9 !important;
    }}

    /* ── Empty state ── */
    .empty-state {{
        text-align: center;
        padding: 3rem;
        color: {COLORS['text_secondary']};
    }}
    .empty-state .icon {{ font-size: 3rem; margin-bottom: 1rem; }}

    div[data-testid="stHorizontalBlock"] > div {{
        padding: 0 0.25rem;
    }}
</style>
""", unsafe_allow_html=True)


# ─── Data Loading ───────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    return read_input_excel()


def safe_mean(series):
    vals = series.dropna()
    return vals.mean() if len(vals) > 0 else None


# ─── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem;">
        <div style="font-size: 2rem;">📊</div>
        <div style="font-size: 1.3rem; font-weight: 700; color: white; letter-spacing: -0.02em;">
            COLDEX Sectorial
        </div>
        <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 0.2rem;">
            Dashboard de Resultados 2025
        </div>
    </div>
    <hr style="border-color: rgba(255,255,255,0.1); margin: 1rem 0;">
    """, unsafe_allow_html=True)

    sector_options = list(SECTOR_MAP.items())
    sector_labels = [v for _, v in sector_options]
    sector_codes = [k for k, _ in sector_options]

    selected_sector_label = st.selectbox(
        "SECTOR",
        sector_labels,
        index=0,
    )
    id_category = sector_codes[sector_labels.index(selected_sector_label)]

    selected_type = st.selectbox(
        "TIPO DE EMPRESA",
        ["INDUSTRIAL", "CADENA"],
        format_func=lambda x: f"{'🏭' if x == 'INDUSTRIAL' else '🏬'} {x}",
    )
    type_short = TYPE_MAP[selected_type]

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 1.5rem 0 1rem;'>", unsafe_allow_html=True)

    # Exportar
    st.markdown("""
    <div style="color: rgba(255,255,255,0.5); font-size: 0.75rem; text-transform: uppercase;
                letter-spacing: 0.05em; font-weight: 600; margin-bottom: 0.5rem;">
        Exportar
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚙️  Generar Excel completo", use_container_width=True):
        with st.spinner("Generando..."):
            generar_excel()
        with open(OUTPUT_FILE, "rb") as f:
            st.download_button(
                "⬇  Descargar Excel",
                data=f.read(),
                file_name="Procesamiento_COLDEX_Sectorial_2025.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    st.markdown("""
    <div style="position: fixed; bottom: 1rem; padding: 0.5rem; width: inherit;">
        <div style="font-size: 0.65rem; color: rgba(255,255,255,0.3); text-align: center;">
            LOGYCA &middot; COLDEX Sectorial 2025
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Load & filter ──────────────────────────────────────────────────────────────

df = load_data()
df_sector = df[(df["IDCategory"] == id_category) & (df["IDType"] == selected_type)].copy()

# ─── Header ─────────────────────────────────────────────────────────────────────

icon = "🏭" if selected_type == "INDUSTRIAL" else "🏬"
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.25rem;">
    <div style="font-size: 1.8rem; font-weight: 700; color: {COLORS['text']}; letter-spacing: -0.02em;">
        {selected_sector_label}
    </div>
    <div style="background: {COLORS['primary_light']}; color: {COLORS['primary']}; padding: 0.25rem 0.75rem;
                border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
        {icon} {selected_type}
    </div>
</div>
""", unsafe_allow_html=True)

if df_sector.empty:
    st.markdown(f"""
    <div class="empty-state">
        <div class="icon">📭</div>
        <div style="font-size: 1.1rem; font-weight: 600;">Sin datos</div>
        <div>No hay registros para {selected_sector_label} - {selected_type}</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

companies = sorted(df_sector["CompanyNameTo"].unique())
evaluators = df_sector["CompanyNameFrom"].nunique()
avg_general = df_sector["Calification"].mean()

# ─── Metric Cards ───────────────────────────────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="value">{len(df_sector):,}</div>
        <div class="label">Registros</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card accent">
        <div class="value">{len(companies)}</div>
        <div class="label">Empresas evaluadas</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
        <div class="value">{evaluators}</div>
        <div class="label">Evaluadores</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card green">
        <div class="value">{avg_general:.2f}</div>
        <div class="label">Promedio general</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

# ─── Navigation ─────────────────────────────────────────────────────────────────

selected_tab = option_menu(
    menu_title=None,
    options=["Resumen", "Tabla Pivote", "Ranking", "Evaluadores"],
    icons=["bar-chart-fill", "table", "trophy-fill", "people-fill"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {
            "padding": "0",
            "background-color": "white",
            "border-radius": "10px",
            "border": f"1px solid {COLORS['border']}",
        },
        "icon": {"font-size": "0.85rem"},
        "nav-link": {
            "font-size": "0.85rem",
            "font-weight": "500",
            "padding": "0.7rem 1rem",
            "border-radius": "8px",
            "margin": "0.25rem",
            "--hover-color": COLORS["primary_light"],
        },
        "nav-link-selected": {
            "background-color": COLORS["primary"],
            "font-weight": "600",
        },
    },
)

st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)


# ─── TAB: Resumen ──────────────────────────────────────────────────────────────

if selected_tab == "Resumen":

    # Subcategory summary data
    present_subcats = [s for s in SUBCATEGORY_ORDER if s in df_sector["PollDesc2"].unique()]
    for s in sorted(df_sector["PollDesc2"].unique()):
        if s not in present_subcats:
            present_subcats.append(s)

    subcat_data = []
    for subcat in present_subcats:
        df_sub = df_sector[df_sector["PollDesc2"] == subcat]
        avg = safe_mean(df_sub["Calification"])
        if avg is not None:
            subcat_data.append({"Subcategoria": subcat, "Promedio": round(avg, 2)})

    df_subcat_chart = pd.DataFrame(subcat_data)

    # Horizontal bar chart
    st.markdown('<div class="section-header">📈 Promedio por subcategoria</div>', unsafe_allow_html=True)

    if not df_subcat_chart.empty:
        df_subcat_chart = df_subcat_chart.sort_values("Promedio", ascending=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df_subcat_chart["Subcategoria"],
            x=df_subcat_chart["Promedio"],
            orientation="h",
            marker=dict(
                color=df_subcat_chart["Promedio"],
                colorscale=[[0, "#E8F4FD"], [0.5, "#44B3E1"], [1, "#0066CC"]],
                cornerradius=6,
            ),
            text=df_subcat_chart["Promedio"].apply(lambda x: f"{x:.2f}"),
            textposition="outside",
            textfont=dict(size=12, color=COLORS["text"]),
            hovertemplate="<b>%{y}</b><br>Promedio: %{x:.2f}<extra></extra>",
        ))
        fig.update_layout(
            height=max(350, len(df_subcat_chart) * 38),
            margin=dict(l=0, r=40, t=10, b=10),
            xaxis=dict(
                range=[0, 10.5],
                showgrid=True,
                gridcolor="#F0F0F0",
                title=None,
            ),
            yaxis=dict(title=None, tickfont=dict(size=12)),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Heatmap: subcategoría × empresa
    st.markdown('<div class="section-header">🔥 Mapa de calor por empresa</div>', unsafe_allow_html=True)

    heat_data = []
    for subcat in present_subcats:
        df_sub = df_sector[df_sector["PollDesc2"] == subcat]
        for comp in companies:
            val = safe_mean(df_sub[df_sub["CompanyNameTo"] == comp]["Calification"])
            heat_data.append({
                "Subcategoria": subcat,
                "Empresa": comp,
                "Promedio": round(val, 2) if val is not None else None,
            })

    df_heat = pd.DataFrame(heat_data)
    df_heat_pivot = df_heat.pivot(index="Subcategoria", columns="Empresa", values="Promedio")
    # Reorder
    ordered_subcats = [s for s in present_subcats if s in df_heat_pivot.index]
    df_heat_pivot = df_heat_pivot.reindex(ordered_subcats)

    fig_heat = go.Figure(data=go.Heatmap(
        z=df_heat_pivot.values,
        x=df_heat_pivot.columns.tolist(),
        y=df_heat_pivot.index.tolist(),
        colorscale=[
            [0, "#FEE2E2"],
            [0.3, "#FEF3C7"],
            [0.5, "#FEF9C3"],
            [0.7, "#D1FAE5"],
            [1, "#47D359"],
        ],
        zmin=0,
        zmax=10,
        text=df_heat_pivot.values,
        texttemplate="%{text:.1f}",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>%{x}<br>Promedio: %{z:.2f}<extra></extra>",
        colorbar=dict(
            title="Puntaje",
            titlefont=dict(size=11),
            tickfont=dict(size=10),
            len=0.8,
        ),
    ))
    fig_heat.update_layout(
        height=max(400, len(ordered_subcats) * 36),
        margin=dict(l=0, r=0, t=10, b=10),
        xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=11), autorange="reversed"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif"),
    )
    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})


# ─── TAB: Tabla Pivote ─────────────────────────────────────────────────────────

elif selected_tab == "Tabla Pivote":

    st.markdown('<div class="section-header">📋 Calificaciones promedio por empresa y pregunta</div>', unsafe_allow_html=True)

    # Filtro de subcategoría
    all_subcats = sorted(df_sector["PollDesc2"].unique())
    selected_subcats = st.multiselect(
        "Filtrar por subcategoria",
        options=all_subcats,
        default=all_subcats,
        placeholder="Selecciona subcategorias...",
    )

    if selected_subcats:
        df_filtered = df_sector[df_sector["PollDesc2"].isin(selected_subcats)]
    else:
        df_filtered = df_sector

    # Build pivot
    pivot = df_filtered.pivot_table(
        values="Calification",
        index=["PollLevel1", "PollDesc1", "PollLevel2", "PollDesc2", "PollLevel3", "PollDesc3"],
        columns="CompanyNameTo",
        aggfunc="mean",
    ).round(2)

    rows = []
    prev_l1 = prev_l2 = None

    for (lvl1, desc1, lvl2, desc2, lvl3, desc3) in pivot.index:
        if desc1 != prev_l1:
            df_l1 = df_filtered[df_filtered["PollDesc1"] == desc1]
            row = {"Nivel": "●", "Pregunta": desc1}
            for comp in companies:
                val = safe_mean(df_l1[df_l1["CompanyNameTo"] == comp]["Calification"])
                row[comp] = round(val, 2) if val is not None else None
            vals_all = [v for v in row.values() if isinstance(v, (int, float)) and v is not None]
            row["Total"] = round(safe_mean(df_l1["Calification"]), 2) if safe_mean(df_l1["Calification"]) else None
            rows.append(row)
            prev_l1 = desc1
            prev_l2 = None

        if desc2 != prev_l2:
            df_l2 = df_filtered[(df_filtered["PollDesc1"] == desc1) & (df_filtered["PollDesc2"] == desc2)]
            row = {"Nivel": "  ◆", "Pregunta": desc2}
            for comp in companies:
                val = safe_mean(df_l2[df_l2["CompanyNameTo"] == comp]["Calification"])
                row[comp] = round(val, 2) if val is not None else None
            row["Total"] = round(safe_mean(df_l2["Calification"]), 2) if safe_mean(df_l2["Calification"]) else None
            rows.append(row)
            prev_l2 = desc2

        desc3_short = str(desc3)[:90] + "..." if len(str(desc3)) > 90 else str(desc3)
        row_data = pivot.loc[(lvl1, desc1, lvl2, desc2, lvl3, desc3)]
        row = {"Nivel": "    ○", "Pregunta": desc3_short}
        vals_list = []
        for comp in companies:
            val = row_data.get(comp, None)
            if pd.notna(val):
                row[comp] = round(val, 2)
                vals_list.append(val)
            else:
                row[comp] = None
        row["Total"] = round(np.mean(vals_list), 2) if vals_list else None
        rows.append(row)

    df_pivot = pd.DataFrame(rows)

    # Style: bold for level 1 and 2
    def style_pivot(df_display):
        styles = pd.DataFrame("", index=df_display.index, columns=df_display.columns)
        for idx, row in df_display.iterrows():
            nivel = str(row.get("Nivel", ""))
            if "●" in nivel:
                styles.loc[idx, :] = "font-weight: 700; background-color: #EFF6FF;"
            elif "◆" in nivel:
                styles.loc[idx, :] = "font-weight: 600; background-color: #F8FAFC;"
        return styles

    if not df_pivot.empty:
        styled = (
            df_pivot.style
            .apply(style_pivot, axis=None)
            .format(precision=2, na_rep="", subset=[c for c in df_pivot.columns if c not in ["Nivel", "Pregunta"]])
        )
        st.dataframe(
            styled,
            use_container_width=True,
            height=650,
            hide_index=True,
        )
    else:
        st.info("Selecciona al menos una subcategoria para ver datos.")


# ─── TAB: Ranking ──────────────────────────────────────────────────────────────

elif selected_tab == "Ranking":

    st.markdown('<div class="section-header">🏆 Ranking de empresas</div>', unsafe_allow_html=True)

    # Calculate general averages
    present_subcats = [s for s in SUBCATEGORY_ORDER if s in df_sector["PollDesc2"].unique()]
    for s in sorted(df_sector["PollDesc2"].unique()):
        if s not in present_subcats:
            present_subcats.append(s)

    company_vals = {comp: [] for comp in companies}
    for subcat in present_subcats:
        df_sub = df_sector[df_sector["PollDesc2"] == subcat]
        for comp in companies:
            val = safe_mean(df_sub[df_sub["CompanyNameTo"] == comp]["Calification"])
            if val is not None:
                company_vals[comp].append(val)

    general_avgs = {}
    for comp in companies:
        if company_vals[comp]:
            general_avgs[comp] = round(np.mean(company_vals[comp]), 2)

    eval_counts = (
        df_sector.groupby("CompanyNameTo")["CompanyNameFrom"]
        .nunique()
        .to_dict()
    )

    ranking = sorted(general_avgs.items(), key=lambda x: x[1], reverse=True)
    top_n = min(7, len(ranking))

    if ranking:
        # Chart: top companies
        left, right = st.columns([3, 2])

        with left:
            df_rank = pd.DataFrame([
                {"Empresa": comp, "Puntaje": score, "Puesto": i + 1}
                for i, (comp, score) in enumerate(ranking)
            ])
            df_rank_chart = df_rank.head(15).sort_values("Puntaje", ascending=True)

            colors = []
            for _, r in df_rank_chart.iterrows():
                if r["Puesto"] <= top_n:
                    colors.append(COLORS["green"])
                else:
                    colors.append(COLORS["accent"])

            fig_rank = go.Figure()
            fig_rank.add_trace(go.Bar(
                y=df_rank_chart["Empresa"],
                x=df_rank_chart["Puntaje"],
                orientation="h",
                marker=dict(color=colors, cornerradius=6),
                text=df_rank_chart["Puntaje"].apply(lambda x: f"{x:.2f}"),
                textposition="outside",
                textfont=dict(size=12, color=COLORS["text"]),
                hovertemplate="<b>%{y}</b><br>Puntaje: %{x:.2f}<extra></extra>",
            ))
            fig_rank.update_layout(
                height=max(350, len(df_rank_chart) * 35),
                margin=dict(l=0, r=50, t=10, b=10),
                xaxis=dict(range=[0, 10.5], showgrid=True, gridcolor="#F0F0F0", title=None),
                yaxis=dict(title=None, tickfont=dict(size=11)),
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar": False})

        with right:
            # HTML table
            table_html = '<table class="ranking-table"><thead><tr>'
            table_html += "<th>#</th><th>Empresa</th><th>Puntaje</th><th>Evaluadores</th>"
            table_html += "</tr></thead><tbody>"

            for i, (comp, score) in enumerate(ranking):
                puesto = i + 1
                row_class = "top" if puesto <= top_n else "rest"

                if puesto == 1:
                    badge = '<span class="ranking-badge badge-gold">1</span>'
                elif puesto == 2:
                    badge = '<span class="ranking-badge badge-silver">2</span>'
                elif puesto == 3:
                    badge = '<span class="ranking-badge badge-bronze">3</span>'
                else:
                    badge = f'<span class="ranking-badge badge-default">{puesto}</span>'

                n_eval = eval_counts.get(comp, 0)
                table_html += f'<tr class="{row_class}">'
                table_html += f"<td>{badge}</td><td>{comp}</td><td><b>{score:.2f}</b></td><td>{n_eval}</td>"
                table_html += "</tr>"

            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

        # Radar chart for top 5
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🎯 Perfil comparativo (Top 5)</div>', unsafe_allow_html=True)

        top5 = [comp for comp, _ in ranking[:5]]

        radar_data = []
        for comp in top5:
            for subcat in present_subcats:
                df_sub = df_sector[(df_sector["PollDesc2"] == subcat) & (df_sector["CompanyNameTo"] == comp)]
                val = safe_mean(df_sub["Calification"])
                radar_data.append({
                    "Empresa": comp,
                    "Subcategoria": subcat,
                    "Promedio": round(val, 2) if val is not None else 0,
                })

        df_radar = pd.DataFrame(radar_data)

        fig_radar = go.Figure()
        palette = px.colors.qualitative.Set2
        for i, comp in enumerate(top5):
            df_comp = df_radar[df_radar["Empresa"] == comp]
            fig_radar.add_trace(go.Scatterpolar(
                r=df_comp["Promedio"].tolist() + [df_comp["Promedio"].iloc[0]],
                theta=df_comp["Subcategoria"].tolist() + [df_comp["Subcategoria"].iloc[0]],
                name=comp,
                line=dict(color=palette[i % len(palette)], width=2),
                fill="toself",
                opacity=0.15,
                hovertemplate="<b>%{theta}</b><br>%{fullData.name}: %{r:.2f}<extra></extra>",
            ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(range=[0, 10], showticklabels=True, tickfont=dict(size=9)),
                angularaxis=dict(tickfont=dict(size=10)),
            ),
            height=500,
            margin=dict(l=80, r=80, t=30, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
            ),
            paper_bgcolor="white",
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

    else:
        st.info("No hay datos suficientes para generar el ranking.")


# ─── TAB: Evaluadores ──────────────────────────────────────────────────────────

elif selected_tab == "Evaluadores":

    st.markdown('<div class="section-header">👥 Evaluadores por empresa</div>', unsafe_allow_html=True)

    eval_counts = (
        df_sector.groupby("CompanyNameTo")["CompanyNameFrom"]
        .nunique()
        .reset_index()
        .rename(columns={"CompanyNameFrom": "Evaluadores", "CompanyNameTo": "Empresa"})
        .sort_values("Evaluadores", ascending=False)
    )

    # Cards grid
    cards_html = '<div class="eval-grid">'
    for _, row in eval_counts.iterrows():
        cards_html += f"""
        <div class="eval-card">
            <div class="name" title="{row['Empresa']}">{row['Empresa']}</div>
            <div class="count">{row['Evaluadores']}</div>
            <div style="font-size: 0.7rem; color: {COLORS['text_secondary']};">evaluadores</div>
        </div>
        """
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # Donut chart
    fig_donut = go.Figure(data=[go.Pie(
        labels=eval_counts["Empresa"],
        values=eval_counts["Evaluadores"],
        hole=0.55,
        marker=dict(
            colors=px.colors.qualitative.Pastel,
            line=dict(color="white", width=2),
        ),
        textinfo="label+value",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>Evaluadores: %{value}<extra></extra>",
    )])
    fig_donut.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif"),
        legend=dict(font=dict(size=10)),
        annotations=[dict(
            text=f"<b>{eval_counts['Evaluadores'].sum()}</b><br>total",
            x=0.5, y=0.5,
            font_size=18,
            showarrow=False,
            font=dict(color=COLORS["text"]),
        )],
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    # Quién evalúa a quién
    st.markdown('<div class="section-header">🔗 Matriz de evaluacion</div>', unsafe_allow_html=True)

    matrix = df_sector.pivot_table(
        values="Calification",
        index="CompanyNameFrom",
        columns="CompanyNameTo",
        aggfunc="mean",
    ).round(2)

    fig_matrix = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
        colorscale=[
            [0, "#FEE2E2"],
            [0.3, "#FEF3C7"],
            [0.5, "#FEF9C3"],
            [0.7, "#D1FAE5"],
            [1, "#47D359"],
        ],
        zmin=0,
        zmax=10,
        text=np.where(pd.isna(matrix.values), "", matrix.values.astype(str)),
        texttemplate="%{text}",
        textfont=dict(size=9),
        hovertemplate="<b>%{y}</b> evalua a <b>%{x}</b><br>Promedio: %{z:.2f}<extra></extra>",
        colorbar=dict(title="Puntaje", titlefont=dict(size=11), tickfont=dict(size=10)),
    ))
    fig_matrix.update_layout(
        height=max(400, len(matrix) * 30 + 100),
        margin=dict(l=0, r=0, t=10, b=10),
        xaxis=dict(title="Empresa evaluada", tickangle=-45, tickfont=dict(size=10), side="bottom"),
        yaxis=dict(title="Evaluador", tickfont=dict(size=10), autorange="reversed"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif"),
    )
    st.plotly_chart(fig_matrix, use_container_width=True, config={"displayModeBar": False})
