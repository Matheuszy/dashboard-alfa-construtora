# -*- coding: utf-8 -*-
"""Dashboard Dash — Alfa Construtora."""
from __future__ import annotations
from pathlib import Path

from dash import Dash, Input, Output, State, ctx, dash_table, dcc, html, no_update
import pandas as pd
import plotly.express as px
from data_transformer import DATA_DIR, load_all
import base64, os

# ─────────────────────────────────────────────────────────────────────────────
# TEMA
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {
    "bg":     "#0E1117", "panel":  "#1A1C24", "red":    "#C41E3A",
    "text":   "#F5F5F5", "muted":  "#A7A9B0", "orange": "#FB8C00",
    "green":  "#4CAF50", "blue":   "#2196F3",
}
PLOT_LAYOUT = {
    "paper_bgcolor": COLORS["panel"], "plot_bgcolor": COLORS["panel"],
    "font_color":    COLORS["text"],
    "margin":        {"l": 40, "r": 20, "t": 40, "b": 40},
    "autosize":      True,
}
AGING_LABELS = ["Antecipado", "No prazo", "Atraso ate 30d", "Atraso >30d"]
AGING_BINS   = [-9999, -1, 7, 30, 9999]
AGING_COLORS = {
    "Antecipado": "#4CAF50", "No prazo": "#8BC34A",
    "Atraso ate 30d": "#FB8C00", "Atraso >30d": "#F44336",
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def empty_figure(title: str = ""):
    fig = px.scatter(title=title)
    fig.update_layout(**PLOT_LAYOUT, xaxis={"visible": False}, yaxis={"visible": False})
    fig.add_annotation(text="Sem dados para os filtros selecionados",
                        showarrow=False, font={"color": COLORS["muted"]})
    return fig

def card(label, value, note=""):
    return html.Div([
        html.Div(label, className="metric-label"),
        html.Div(value, className="metric-value"),
        html.Small(note, className="metric-note"),
    ], className="metric-card")

def insight(title, text):
    return html.Div([html.Strong(title), html.Span(text)], className="insight")

def graph(gid):
    # responsive=True garante que o Plotly redimensiona junto com o container
    return dcc.Graph(id=gid, config={"displaylogo": False, "responsive": True},
                     style={"minHeight": "320px"})

def get_logo_src():
    p = "alfa_logo.png"
    if os.path.exists(p):
        with open(p, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return ""

def checklist(cid, options, value):
    return dcc.Checklist(
        id=cid,
        options=[{"label": o, "value": o} for o in options],
        value=value,
        inline=True,
        className="pill-checklist",
        labelClassName="pill-item",
        inputClassName="pill-input",
    )

# ─────────────────────────────────────────────────────────────────────────────
# DADOS — carregados uma vez no startup
# ─────────────────────────────────────────────────────────────────────────────
data      = load_all(DATA_DIR)
financial = data["financeiro"]
if not financial.empty:
    financial["Faixa_Aging"] = pd.cut(
        financial["Aging_dias"], AGING_BINS, labels=AGING_LABELS
    ).astype("string")

advances = data["adiantamentos"]

months      = financial["Mes"].drop_duplicates().tolist()  if not financial.empty else []
departments = sorted(financial["Departamento"].unique())   if not financial.empty else []
statuses    = sorted(financial["Status"].unique())         if not financial.empty else []
roles       = sorted(advances["Funcao"].unique())          if not advances.empty  else []
obras_rh    = sorted(advances["Obra"].unique()) if (
    not advances.empty and "Obra" in advances.columns
) else []

# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    title="Alfa Construtora | Analytics",
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1"}],
)

# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
app.layout = html.Div(className="page", children=[

    # ── Header ───────────────────────────────────────────────────────────────
    html.Header([
        html.Div([
            html.Img(src=get_logo_src(), className="header-logo"),
            html.Div([
                html.H1("Alfa Construtora"),
                html.P("Painel Analitico: Financeiro e RH"),
            ]),
        ], className="header-brand"),
        html.Div(
            f"Fontes: {len(list(Path(DATA_DIR).glob('*.xlsx')))} arquivos Excel",
            className="source-note",
        ),
    ]),

    # ── Tabs ─────────────────────────────────────────────────────────────────
    dcc.Tabs(id="module", value="financeiro", children=[
        dcc.Tab(label="Financeiro", value="financeiro"),
        dcc.Tab(label="RH",         value="rh"),
    ]),

    dcc.Store(id="chart-filters", data={}),

    # ── Toolbar ──────────────────────────────────────────────────────────────
    html.Div(className="toolbar", children=[
        html.Div(id="active-chart-filter", className="source-note"),
        html.Button("Limpar filtros", id="clear-chart-filters",
                    n_clicks=0, className="clear-button"),
    ]),

    # ── Filtros Financeiro ────────────────────────────────────────────────────
    html.Div(id="finance-filters", className="finance-filters", children=[
        html.Div([
            html.Span("Mes", className="filter-label"),
            checklist("months", months, months),
        ], className="filter-group"),
        html.Div([
            html.Span("Departamento", className="filter-label"),
            checklist("departments", departments, departments),
        ], className="filter-group"),
        html.Div([
            html.Span("Status", className="filter-label"),
            checklist("statuses", statuses, statuses),
        ], className="filter-group"),
        html.Div([
            html.Span("Pontualidade", className="filter-label"),
            checklist("aging-filter", AGING_LABELS, AGING_LABELS),
        ], className="filter-group"),
        html.Div([
            html.Span("Pgtos futuros", className="filter-label"),
            dcc.Checklist(
                id="future-horizon",
                options=[
                    {"label": "Prox. 7 dias",  "value": 7},
                    {"label": "Prox. 30 dias", "value": 30},
                    {"label": "Prox. 90 dias", "value": 90},
                ],
                value=[30], inline=True,
                className="pill-checklist",
                labelClassName="pill-item",
                inputClassName="pill-input",
            ),
        ], className="filter-group"),
    ]),

    # ── Filtros RH ────────────────────────────────────────────────────────────
    html.Div(id="rh-filters", className="finance-filters", children=[
        html.Div([
            html.Span("Obra", className="filter-label"),
            checklist("rh-obras", obras_rh, obras_rh),
        ], className="filter-group"),
        html.Div([
            html.Span("Funcao", className="filter-label"),
            checklist("roles", roles, roles),
        ], className="filter-group"),
    ]),

    # ── Secao Financeiro ──────────────────────────────────────────────────────
    html.Section(id="finance-section", children=[
        html.Div(id="finance-kpis",     className="cards"),
        html.Div(id="finance-insights", className="insights"),
        html.Div(className="grid-2", children=[
            graph("financial-month-chart"),
            graph("financial-dept-chart"),
        ]),
        html.Div(className="grid-2", children=[
            graph("financial-top-chart"),
            graph("financial-aging-chart"),
        ]),
        html.Div(className="grid-2", children=[
            graph("financial-fonte-chart"),
            graph("financial-future-chart"),
        ]),
        html.H3("Lancamentos que exigem atencao", className="table-title"),
        dash_table.DataTable(
            id="finance-table", page_size=12,
            style_table={"overflowX": "auto", "minWidth": "100%"},
            style_header={"backgroundColor": "#30333D", "color": "white",
                           "fontWeight": "600", "whiteSpace": "normal"},
            style_data={"backgroundColor": COLORS["panel"], "color": "white"},
            style_cell={"padding": "8px 12px", "fontSize": "0.85rem",
                         "border": "1px solid #2C2F3A"},
            style_data_conditional=[
                {"if": {"row_index": "odd"},
                 "backgroundColor": "#161922"},
            ],
        ),
    ]),

    # ── Secao RH ──────────────────────────────────────────────────────────────
    html.Section(id="rh-section", children=[
        html.H2("Operacao de RH — Adiantamentos e Custos com Pessoal"),
        html.P("Analise por colaborador, funcao e obra."),
        html.Div(id="rh-kpis", className="cards"),
        html.Div(className="grid-2", children=[
            graph("rh-role-chart"),
            graph("rh-pareto-chart"),
        ]),
        html.Div(className="grid-2", children=[
            graph("rh-employee-chart"),
            graph("rh-distribution-chart"),
        ]),
    ]),
])

# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

@app.callback(
    Output("finance-filters", "style"),
    Output("rh-filters",      "style"),
    Output("finance-section", "style"),
    Output("rh-section",      "style"),
    Input("module", "value"),
)
def switch_module(module):
    show, hide = {"display": "block"}, {"display": "none"}
    return (
        show if module == "financeiro" else hide,
        show if module == "rh"         else hide,
        show if module == "financeiro" else hide,
        show if module == "rh"         else hide,
    )


@app.callback(
    Output("chart-filters", "data"),
    Input("clear-chart-filters", "n_clicks"),
    State("chart-filters", "data"),
    prevent_initial_call=True,
)
def clear_filters(n, current):
    return {}


@app.callback(
    Output("active-chart-filter", "children"),
    Input("chart-filters", "data"),
)
def show_filters(filters):
    if not filters:
        return "Dashboard pronto."
    return "Filtros ativos: " + " | ".join(f"{k}: {v}" for k, v in filters.items())


# ── FINANCEIRO ────────────────────────────────────────────────────────────────
@app.callback(
    Output("finance-kpis",           "children"),
    Output("finance-insights",       "children"),
    Output("financial-month-chart",  "figure"),
    Output("financial-dept-chart",   "figure"),
    Output("financial-top-chart",    "figure"),
    Output("financial-aging-chart",  "figure"),
    Output("financial-fonte-chart",  "figure"),
    Output("financial-future-chart", "figure"),
    Output("finance-table",          "data"),
    Output("finance-table",          "columns"),
    Input("months",         "value"),
    Input("departments",    "value"),
    Input("statuses",       "value"),
    Input("aging-filter",   "value"),
    Input("future-horizon", "value"),
    Input("chart-filters",  "data"),
)
def update_financial(sel_months, sel_depts, sel_statuses,
                     sel_aging, future_horizon, chart_filters):
    empties = ([], [], empty_figure(), empty_figure(), empty_figure(),
               empty_figure(), empty_figure(), empty_figure(), [], [])
    if financial.empty:
        return empties

    df = financial[
        financial["Mes"].isin(sel_months or []) &
        financial["Departamento"].isin(sel_depts or []) &
        financial["Status"].isin(sel_statuses or [])
    ].copy()

    if sel_aging and len(sel_aging) < len(AGING_LABELS):
        df = df[df["Faixa_Aging"].isna() | df["Faixa_Aging"].isin(sel_aging)]

    if df.empty:
        return empties

    total      = df["Valor"].sum()
    paid       = df.loc[df["Pago"], "Valor"].sum()
    open_value = df.loc[~df["Pago"], "Valor"].sum()
    overdue    = df[(~df["Pago"]) & (df["Vencimento"] < pd.Timestamp.today())]["Valor"].sum()

    trend      = df.groupby("Mes", sort=False)["Valor"].sum().reset_index()
    by_dept    = df.groupby("Departamento")["Valor"].sum().sort_values().reset_index()
    top        = df.groupby("Despesa")["Valor"].sum().nlargest(10).reset_index()
    aging_df   = df.dropna(subset=["Aging_dias"]).copy()
    aging_df["Faixa"] = pd.cut(aging_df["Aging_dias"], AGING_BINS, labels=AGING_LABELS)
    aging_summ = aging_df.groupby("Faixa", observed=True)["Valor"].sum().reset_index()

    # Fonte
    by_fonte = (df.groupby(["Fonte", "Status"])["Valor"].sum()
                  .reset_index().query("Valor > 0")
                  .sort_values("Valor", ascending=True))
    if not by_fonte.empty:
        fonte_fig = px.bar(by_fonte, x="Valor", y="Fonte", color="Status",
                            orientation="h", title="Gasto por recebedor",
                            color_discrete_map={"PAGO": COLORS["green"],
                                                "EM ABERTO": COLORS["red"]})
        fonte_fig.update_layout(**PLOT_LAYOUT, yaxis={"autorange": "reversed"})
        fonte_fig.update_layout(legend=dict(orientation="h", yanchor="bottom",
                                            y=1.02, bgcolor="rgba(0,0,0,0)"))
    else:
        fonte_fig = empty_figure("Gasto por recebedor")

    # Futuros
    horizon = max(future_horizon) if future_horizon else 30
    today   = pd.Timestamp.today().normalize()
    future  = df[
        (~df["Pago"]) &
        (df["Vencimento"] >= today) &
        (df["Vencimento"] <= today + pd.Timedelta(days=horizon))
    ].copy()
    future["Venc_str"] = future["Vencimento"].dt.strftime("%d/%m")
    future_by_date = future.groupby("Venc_str")["Valor"].sum().reset_index()
    if not future_by_date.empty:
        future_fig = px.bar(future_by_date, x="Venc_str", y="Valor",
                             title=f"Pagamentos futuros ({horizon}d)",
                             color_discrete_sequence=[COLORS["orange"]], text_auto=",.0f")
        future_fig.update_traces(textfont_color=COLORS["text"])
        future_fig.update_layout(**PLOT_LAYOUT, xaxis_title="Vencimento", yaxis_title="R$")
    else:
        future_fig = empty_figure(f"Pagamentos futuros ({horizon}d)")

    figs = [
        px.line(trend, x="Mes", y="Valor", markers=True, title="Evolucao mensal")
            if not trend.empty else empty_figure("Evolucao mensal"),
        px.bar(by_dept, x="Valor", y="Departamento", orientation="h",
               title="Gasto por departamento",
               color_discrete_sequence=[COLORS["red"]])
            if not by_dept.empty else empty_figure("Gasto por departamento"),
        px.bar(top, x="Valor", y="Despesa", orientation="h",
               title="Top 10 despesas",
               color_discrete_sequence=[COLORS["orange"]])
            if not top.empty else empty_figure("Top 10 despesas"),
        px.bar(aging_summ, x="Faixa", y="Valor", title="Pontualidade",
               color="Faixa", color_discrete_map=AGING_COLORS)
            if not aging_summ.empty else empty_figure("Pontualidade"),
    ]
    for fig in figs:
        fig.update_layout(**PLOT_LAYOUT, showlegend=False)
    figs[1].update_layout(yaxis={"autorange": "reversed"})
    figs[2].update_layout(yaxis={"autorange": "reversed"})

    largest_dept    = by_dept.iloc[-1] if not by_dept.empty else None
    largest_expense = top.iloc[0]      if not top.empty     else None
    next_payment    = future.sort_values("Vencimento").iloc[0] if not future.empty else None

    view = df.sort_values("Valor", ascending=False).head(50).copy()
    for col in ["Vencimento", "Data_Pagamento"]:
        view[col] = view[col].dt.strftime("%d/%m/%Y").fillna("Pendente")
    tcols = ["Despesa", "Departamento", "Valor", "Vencimento",
              "Data_Pagamento", "Status", "Fonte"]

    return (
        [card("Despesas",  brl(total)),
         card("Pago",      brl(paid),       f"{paid/total:.1%}" if total else "0%"),
         card("Em aberto", brl(open_value)),
         card("Em atraso", brl(overdue),    "vencidos nao pagos")],
        [insight("Maior centro de custo",
                 f"{largest_dept['Departamento']} concentra {brl(largest_dept['Valor'])}."
                 if largest_dept is not None else "Sem dados."),
         insight("Maior despesa",
                 f"{largest_expense['Despesa']} soma {brl(largest_expense['Valor'])}."
                 if largest_expense is not None else "Sem dados."),
         insight("Proximo vencimento",
                 f"{next_payment['Despesa']} vence em "
                 f"{next_payment['Vencimento'].strftime('%d/%m/%Y')}."
                 if next_payment is not None else "Nenhum pagamento programado.")],
        *figs, fonte_fig, future_fig,
        view[tcols].to_dict("records"),
        [{"name": c, "id": c} for c in tcols],
    )


# ── RH ────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("rh-kpis",               "children"),
    Output("rh-role-chart",         "figure"),
    Output("rh-pareto-chart",       "figure"),
    Output("rh-employee-chart",     "figure"),
    Output("rh-distribution-chart", "figure"),
    Input("roles",    "value"),
    Input("rh-obras", "value"),
)
def update_rh(sel_roles, sel_obras):
    empties = ([], empty_figure(), empty_figure(), empty_figure(), empty_figure())
    if advances.empty or "Obra" not in advances.columns:
        return empties

    df = advances[
        advances["Funcao"].isin(sel_roles or []) &
        advances["Obra"].isin(sel_obras or [])
    ].copy()
    if df.empty:
        return empties

    by_role    = df.groupby(["Funcao", "Obra"])["Valor"].sum().reset_index()
    role_order = df.groupby("Funcao")["Valor"].sum().sort_values().index
    top        = df.nlargest(10, "Valor").sort_values("Valor", ascending=True)
    pareto_df  = df.groupby("Funcao")["Valor"].sum().sort_values(ascending=False).reset_index()
    pareto_df["Acumulado %"] = pareto_df["Valor"].cumsum() / pareto_df["Valor"].sum() * 100

    role_fig = px.bar(by_role, x="Valor", y="Funcao", color="Obra",
                       orientation="h", title="Adiantamentos por Funcao")
    role_fig.update_layout(yaxis={"categoryorder": "array",
                                   "categoryarray": list(role_order)})

    pareto_fig = px.line(pareto_df, x="Funcao", y="Acumulado %",
                          markers=True, title="Concentracao de Adiantamentos (Pareto)")
    pareto_fig.add_hline(y=80, line_dash="dash", line_color=COLORS["green"],
                          annotation_text="80%")

    employee_fig = px.bar(top, x="Valor", y="Nome", color="Obra",
                           orientation="h", title="Top 10 Maiores Adiantamentos")

    dist_fig = px.box(df, x="Funcao", y="Valor", color="Obra",
                       title="Distribuicao de Valores por Funcao")

    for fig in [role_fig, pareto_fig, employee_fig, dist_fig]:
        fig.update_layout(**PLOT_LAYOUT)

    return (
        [card("Total de adiantamentos", brl(df["Valor"].sum())),
         card("Colaboradores",          str(len(df))),
         card("Ticket medio",           brl(df["Valor"].mean())),
         card("Maior adiantamento",     brl(df["Valor"].max()))],
        role_fig, pareto_fig, employee_fig, dist_fig,
    )


if __name__ == "__main__":
    app.run(debug=True)
