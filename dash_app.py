# -*- coding: utf-8 -*-
"""Dashboard Dash interativo para os dados financeiros, operacionais e de RH."""
from __future__ import annotations
from pathlib import Path
from dash import Dash, Input, Output, State, ctx, dash_table, dcc, html, no_update
import pandas as pd
import plotly.express as px
from data_transformer import DATA_DIR, load_all
import base64
import os

COLORS = {
    "bg":     "#0E1117",
    "panel":  "#1A1C24",
    "red":    "#C41E3A",
    "text":   "#F5F5F5",
    "muted":  "#A7A9B0",
    "orange": "#FB8C00",
    "green":  "#4CAF50",
    "blue":   "#2196F3",
}

PLOT_LAYOUT = {
    "paper_bgcolor": COLORS["panel"],
    "plot_bgcolor":  COLORS["panel"],
    "font_color":    COLORS["text"],
    "margin":        {"l": 45, "r": 25, "t": 45, "b": 45},
}

AGING_LABELS = ["Antecipado", "No prazo", "Atraso ate 30d", "Atraso >30d"]
AGING_BINS   = [-9999, -1, 7, 30, 9999]
AGING_COLORS = {
    "Antecipado":      "#4CAF50",
    "No prazo":        "#8BC34A",
    "Atraso ate 30d":  "#FB8C00",
    "Atraso >30d":     "#F44336",
}

def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def empty_figure(title: str):
    fig = px.scatter(title=title)
    fig.update_layout(**PLOT_LAYOUT, xaxis={"visible": False}, yaxis={"visible": False})
    fig.add_annotation(
        text="Sem dados para os filtros selecionados",
        showarrow=False, font={"color": COLORS["muted"]},
    )
    return fig

def card(label: str, value: str, note: str = ""):
    return html.Div([
        html.Div(label, className="metric-label"),
        html.Div(value, className="metric-value"),
        html.Small(note, className="metric-note"),
    ], className="metric-card")

def insight(title: str, text: str):
    return html.Div([html.Strong(title), html.Span(text)], className="insight")

def graph(graph_id: str):
    return dcc.Graph(id=graph_id, config={"displaylogo": False}, style={"height": "100%", "width": "100%"})

def get_logo_src():
    logo_path = "alfa_logo.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    return ""    

def build_app() -> Dash:
    data      = load_all(DATA_DIR)
    financial = data["financeiro"]
    if not financial.empty:
        financial["Faixa_Aging"] = pd.cut(
            financial["Aging_dias"], AGING_BINS, labels=AGING_LABELS,
        ).astype("string")
    
    works     = data["obras"]
    advances  = data["adiantamentos"]
    contract  = data["medicao_geral"]

    months      = financial["Mes"].drop_duplicates().tolist() if not financial.empty else []
    departments = sorted(financial["Departamento"].unique()) if not financial.empty else []
    statuses    = sorted(financial["Status"].unique()) if not financial.empty else []

    
    
    services    = works["Servico"].drop_duplicates().tolist() if not works.empty else []
    roles       = sorted(advances["Funcao"].unique()) if not advances.empty else []

    obras_rh = sorted(advances["Obra"].unique()) if "Obra" in advances.columns and not advances.empty else []

    app = Dash(
        __name__, 
        title="Alfa Construtora | Analytics", 
        suppress_callback_exceptions=True,
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1"}]
    )

    app.layout = html.Div(className="page", children=[
        html.Header([
            html.Div([
                html.Img(src=get_logo_src(), style={"height": "60px", "marginRight": "20px"}),
                html.Div([
                    html.H1("Alfa Construtora"),
                    html.P("Painel Analitico: Financeiro, Obras e RH"),
                ]),
            ], style={"display": "flex", "alignItems": "center"}),
        ]),
        dcc.Tabs(id="module", value="financeiro", children=[
            dcc.Tab(label="Financeiro", value="financeiro"),
            dcc.Tab(label="RH",         value="rh"),
        ]),
        dcc.Store(id="chart-filters", data={}),
        html.Div(className="toolbar", children=[
            html.Div(id="active-chart-filter", className="source-note"),
            html.Button("Limpar filtros dos graficos", id="clear-chart-filters",
                        n_clicks=0, className="clear-button"),
        ]),
        html.Div(id="page-content") 
    ])

   
    @app.callback(
        Output("page-content", "children"),
        Input("module", "value")
    )
    def render_page_content(module):
        if module == "financeiro":
            return html.Div([
                html.Div(id="finance-filters", className="finance-filters", children=[
                    html.Div([
                        html.Span("Mes", className="filter-label"),
                        dcc.Checklist(id="months", options=[{"label": m, "value": m} for m in months],
                                      value=months, inline=True, className="pill-checklist"),
                    ], className="filter-group"),
                    html.Div([
                        html.Span("Departamento", className="filter-label"),
                        dcc.Checklist(id="departments", options=[{"label": d, "value": d} for d in departments],
                                      value=departments, inline=True, className="pill-checklist"),
                    ], className="filter-group"),
                    html.Div([
                        html.Span("Status", className="filter-label"),
                        dcc.Checklist(id="statuses", options=[{"label": s, "value": s} for s in statuses],
                                      value=statuses, inline=True, className="pill-checklist"),
                    ], className="filter-group"),
                    html.Div([
                        html.Span("Pontualidade", className="filter-label"),
                        dcc.Checklist(id="aging-filter", options=[{"label": l, "value": l} for l in AGING_LABELS],
                                      value=AGING_LABELS, inline=True, className="pill-checklist"),
                    ], className="filter-group"),
                    html.Div([
                        html.Span("Pgtos futuros", className="filter-label"),
                        dcc.Checklist(id="future-horizon", options=[
                            {"label": "Prox. 7 dias",  "value": 7},
                            {"label": "Prox. 30 dias", "value": 30},
                            {"label": "Prox. 90 dias", "value": 90},
                        ], value=[30], inline=True, className="pill-checklist"),
                    ], className="filter-group"),
                ]),
                html.Section(id="finance-section", children=[
                    html.Div(id="finance-kpis",     className="cards"),
                    html.Div(id="finance-insights", className="insights"),
                    html.Div(className="grid", children=[
                        graph("financial-month-chart"),
                        graph("financial-dept-chart"),
                    ]),
                    html.Div(className="grid", children=[
                        graph("financial-top-chart"),
                        graph("financial-aging-chart"),
                    ]),
                    html.Div(className="grid", children=[
                        graph("financial-fonte-chart"),
                        graph("financial-future-chart"),
                    ]),
                    html.H3("Lancamentos que exigem atencao"),
                    dash_table.DataTable(
                        id="finance-table", page_size=12,
                        style_table={"overflowX": "auto"},
                        style_header={"backgroundColor": "#30333D", "color": "white"},
                        style_data={"backgroundColor": COLORS["panel"], "color": "white"},
                    ),
                ])
            ])
        elif module == "obras":
            return html.Div([
                html.Div(id="works-filters", className="work-nav", children=[
                    html.Span("Servicos da obra:"),
                    dcc.RadioItems(id="work-service",
                        options=[{"label": "Visao geral", "value": "Todos"}] + [{"label": s, "value": s} for s in services],
                        value="Todos", inline=True, className="button-radio",
                    ),
                ]),
                html.Section(id="works-section", children=[
                    html.Div(id="works-kpis",     className="cards"),
                    html.Div(id="works-insights", className="insights"),
                    html.Div(className="grid", children=[
                        graph("works-service-chart"),
                        graph("works-neighborhood-chart"),
                    ]),
                    html.Div(className="grid", children=[
                        graph("works-timeline-chart"), # Analise de dados: produtividade ao longo do tempo
                        graph("works-scatter-chart"),
                    ]),
                ])
            ])
        elif module == "rh":
            return html.Div([
                html.Div(id="rh-filters", className="finance-filters", children=[
                    html.Div([
                        html.Span("Obra", className="filter-label"),
                        dcc.Checklist(id="rh-obras", options=[{"label": o, "value": o} for o in obras_rh],
                                      value=obras_rh, inline=True, className="pill-checklist"),
                    ], className="filter-group"),
                    html.Div([
                        html.Span("Funcao", className="filter-label"),
                        dcc.Checklist(id="roles", options=[{"label": r, "value": r} for r in roles],
                                      value=roles, inline=True, className="pill-checklist"),
                    ], className="filter-group"),
                ]),
                html.Section(id="rh-section", children=[
                    html.H2("Operacao de RH — Adiantamentos e Custos com Pessoal"),
                    html.P("Analise aprofundada de adiantamentos por colaborador, funcao e impacto financeiro (separado por Obra)."),
                    html.Div(id="rh-kpis", className="cards"),
                    html.Div(className="grid", children=[
                        graph("rh-role-chart"),
                        graph("rh-pareto-chart"), 
                    ]),
                    html.Div(className="grid", children=[
                        graph("rh-employee-chart"),
                        graph("rh-distribution-chart"), 
                    ]),
                ])
            ])

    @app.callback(
        Output("chart-filters", "data"),
        Input("clear-chart-filters", "n_clicks"),
        State("chart-filters", "data"),
        prevent_initial_call=True,
    )
    def apply_chart_filter(clear_clicks, current):
        if ctx.triggered_id == "clear-chart-filters":
            return {}
        return no_update

    # --- FINANCEIRO CALLBACKS ---
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
    def update_financial(selected_months, selected_departments, selected_statuses, selected_aging, future_horizon, chart_filters):
        if financial.empty:
            return [], [], empty_figure(""), empty_figure(""), empty_figure(""), empty_figure(""), empty_figure(""), empty_figure(""), [], []
        
        df = financial[
            financial["Mes"].isin(selected_months or []) &
            financial["Departamento"].isin(selected_departments or []) &
            financial["Status"].isin(selected_statuses or [])
        ].copy()

        if selected_aging and len(selected_aging) < len(AGING_LABELS):
            mask_no_aging = df["Faixa_Aging"].isna()
            mask_in_aging = df["Faixa_Aging"].isin(selected_aging)
            df = df[mask_no_aging | mask_in_aging]

        total      = df["Valor"].sum()
        paid       = df.loc[df["Pago"], "Valor"].sum()
        open_value = df.loc[~df["Pago"], "Valor"].sum()
        overdue    = df[(~df["Pago"]) & (df["Vencimento"] < pd.Timestamp.today())]["Valor"].sum()

        trend    = df.groupby("Mes", sort=False)["Valor"].sum().reset_index()
        by_dept  = df.groupby("Departamento")["Valor"].sum().sort_values().reset_index()
        top      = df.groupby("Despesa")["Valor"].sum().nlargest(10).reset_index()
        
        aging_df = df.dropna(subset=["Aging_dias"]).copy()
        aging_df["Faixa"] = pd.cut(aging_df["Aging_dias"], AGING_BINS, labels=AGING_LABELS)
        aging_summary = aging_df.groupby("Faixa", observed=True)["Valor"].sum().reset_index()

        by_fonte = df.groupby(["Fonte", "Status"])["Valor"].sum().reset_index().query("Valor > 0").sort_values("Valor", ascending=True)
        if not by_fonte.empty:
            fonte_fig = px.bar(by_fonte, x="Valor", y="Fonte", color="Status", orientation="h", title="Gasto por recebedor",
                               color_discrete_map={"PAGO": COLORS["green"], "EM ABERTO": COLORS["red"]})
            fonte_fig.update_layout(**PLOT_LAYOUT, yaxis={"autorange": "reversed"})
        else:
            fonte_fig = empty_figure("Gasto por recebedor")

        horizon = max(future_horizon) if future_horizon else 30
        today = pd.Timestamp.today().normalize()
        future = df[(~df["Pago"]) & (df["Vencimento"] >= today) & (df["Vencimento"] <= today + pd.Timedelta(days=horizon))].copy()
        future["Venc_str"] = future["Vencimento"].dt.strftime("%d/%m")
        future_by_date = future.groupby("Venc_str")["Valor"].sum().reset_index()
        
        if not future_by_date.empty:
            future_fig = px.bar(future_by_date, x="Venc_str", y="Valor", title=f"Pagamentos futuros ({horizon}d)", color_discrete_sequence=[COLORS["orange"]])
            future_fig.update_layout(**PLOT_LAYOUT)
        else:
            future_fig = empty_figure(f"Pagamentos futuros ({horizon}d)")

        figs = [
            px.line(trend, x="Mes", y="Valor", markers=True, title="Evolucao mensal das despesas") if not trend.empty else empty_figure(""),
            px.bar(by_dept, x="Valor", y="Departamento", orientation="h", title="Gasto por departamento", color_discrete_sequence=[COLORS["red"]]) if not by_dept.empty else empty_figure(""),
            px.bar(top, x="Valor", y="Despesa", orientation="h", title="Top 10 despesas", color_discrete_sequence=[COLORS["orange"]]) if not top.empty else empty_figure(""),
            px.bar(aging_summary, x="Faixa", y="Valor", title="Pontualidade", color="Faixa", color_discrete_map=AGING_COLORS) if not aging_summary.empty else empty_figure(""),
        ]
        for fig in figs: fig.update_layout(**PLOT_LAYOUT, showlegend=False)
        figs[1].update_layout(yaxis={"autorange": "reversed"})
        figs[2].update_layout(yaxis={"autorange": "reversed"})

        largest_dept    = by_dept.iloc[-1] if not by_dept.empty else None
        largest_expense = top.iloc[0]      if not top.empty     else None
        next_payment    = future.sort_values("Vencimento").iloc[0] if not future.empty else None

        view = df.sort_values("Valor", ascending=False).head(50).copy()
        for col in ["Vencimento", "Data_Pagamento"]:
            view[col] = view[col].dt.strftime("%d/%m/%Y").fillna("Pendente")
        table_cols = ["Despesa", "Departamento", "Valor", "Vencimento", "Data_Pagamento", "Status", "Fonte"]

        return (
            [
                card("Despesas",  brl(total)),
                card("Pago",      brl(paid),       f"{paid / total:.1%}" if total else "0%"),
                card("Em aberto", brl(open_value)),
                card("Em atraso", brl(overdue),    "vencidos nao pagos"),
            ],
            [
                insight("Maior centro de custo", f"{largest_dept['Departamento']} concentra {brl(largest_dept['Valor'])}." if largest_dept is not None else "Sem dados."),
                insight("Maior despesa", f"{largest_expense['Despesa']} soma {brl(largest_expense['Valor'])}." if largest_expense is not None else "Sem dados."),
                insight("Proximo vencimento", f"{next_payment['Despesa']} vence em {next_payment['Vencimento'].strftime('%d/%m/%Y')}." if next_payment is not None else "Nenhum pagamento programado."),
            ],
            *figs, fonte_fig, future_fig, view[table_cols].to_dict("records"), [{"name": c, "id": c} for c in table_cols]
        )

    # --- OBRAS CALLBACKS ---
    @app.callback(
        Output("works-kpis",               "children"),
        Output("works-insights",           "children"),
        Output("works-service-chart",      "figure"),
        Output("works-neighborhood-chart", "figure"),
        Output("works-timeline-chart",     "figure"),
        Output("works-scatter-chart",      "figure"),
        Input("work-service",  "value"),
        Input("chart-filters", "data"),
    )
    def update_works(selected_service, chart_filters):
        if works.empty:
            return [], [], empty_figure(""), empty_figure(""), empty_figure(""), empty_figure("")

        df = works.copy()
        if selected_service and selected_service != "Todos":
            df = df[df["Servico"].eq(selected_service)]
            
        total_area    = df["Area_m2"].sum()
        q75, q25      = df["Area_m2"].quantile(.75), df["Area_m2"].quantile(.25)
        outlier_limit = (q75 + 1.5 * (q75 - q25)) if not df.empty else 0
        
        service_summary = df.groupby("Servico")["Area_m2"].sum().reset_index()
        neighborhoods   = df.groupby("Bairro")["Area_m2"].sum().nlargest(10).reset_index()
        
        # New Analytical Insight: Productivity over time
        if "Data" in df.columns and not df["Data"].isna().all():
            timeline_df = df.dropna(subset=["Data"]).groupby(df["Data"].dt.to_period("W").dt.start_time)["Area_m2"].sum().reset_index()
            timeline_fig = px.area(timeline_df, x="Data", y="Area_m2", title="Evolucao da Producao (m2) ao longo do tempo", color_discrete_sequence=[COLORS["blue"]])
        else:
            timeline_fig = empty_figure("Sem dados de data para Timeline")

        figs = [
            px.bar(service_summary, x="Servico", y="Area_m2", title="Producao por servico", color="Servico") if not service_summary.empty else empty_figure(""),
            px.bar(neighborhoods, x="Area_m2", y="Bairro", orientation="h", title="Bairros com maior producao", color_discrete_sequence=[COLORS["red"]]) if not neighborhoods.empty else empty_figure(""),
            timeline_fig,
            px.scatter(df.assign(Perfil=df["Area_m2"].gt(outlier_limit).map({True: "Atipico", False: "Normal"})), x="Comprimento", y="Largura", size="Area_m2", color="Perfil", hover_name="Rua", title="Trechos atipicos por dimensao") if not df.empty else empty_figure(""),
        ]
        for fig in figs: fig.update_layout(**PLOT_LAYOUT, showlegend=False)
        figs[1].update_layout(yaxis={"autorange": "reversed"})

        top_service      = service_summary.sort_values("Area_m2", ascending=False).iloc[0] if not service_summary.empty else None
        top_neighborhood = neighborhoods.iloc[0] if not neighborhoods.empty else None
        
        return (
            [
                card("Area executada",         f"{total_area:,.2f} m2"),
                card("Trechos medidos",        f"{len(df):,}"),
                card("Maior trecho",           f"{df['Area_m2'].max():,.2f} m2" if not df.empty else "0 m2"),
                card("Valor da medicao geral", brl(contract["Valor_atual"].sum()) if not contract.empty else "R$ 0,00"),
            ],
            [
                insight("Servico dominante", f"{top_service['Servico']} responde por {top_service['Area_m2']:,.2f} m2." if top_service is not None else "Sem dados."),
                insight("Frente prioritaria", f"{top_neighborhood['Bairro']} lidera com {top_neighborhood['Area_m2']:,.2f} m2." if top_neighborhood is not None else "Sem dados."),
            ],
            *figs,
        )

    # --- RH CALLBACKS ---
    @app.callback(
        Output("rh-kpis",               "children"),
        Output("rh-role-chart",         "figure"),
        Output("rh-pareto-chart",       "figure"),
        Output("rh-employee-chart",     "figure"),
        Output("rh-distribution-chart", "figure"),
        Input("roles", "value"),
        Input("rh-obras", "value"),
    )
    def update_rh(selected_roles, selected_obras):
        if advances.empty or "Obra" not in advances.columns:
            return [], empty_figure("Adiantamentos por funcao"), empty_figure("Pareto"), empty_figure("Maiores adiantamentos"), empty_figure("Distribuicao")

        df = advances[
            advances["Funcao"].isin(selected_roles or []) &
            advances["Obra"].isin(selected_obras or [])
        ].copy()
        
        if df.empty:
            return [], empty_figure(""), empty_figure(""), empty_figure(""), empty_figure("")

        # Agrupamentos mantendo a Obra para a legenda de cores
        by_role = df.groupby(["Funcao", "Obra"])["Valor"].sum().reset_index()
        role_totals = df.groupby("Funcao")["Valor"].sum().sort_values().index
        
        top = df.nlargest(10, "Valor").sort_values("Valor", ascending=True)

        role_fig = px.bar(by_role, x="Valor", y="Funcao", color="Obra", orientation="h", title="Adiantamentos por Funcao")
        role_fig.update_layout(yaxis={'categoryorder':'array', 'categoryarray': role_totals})
        
        employee_fig = px.bar(top, x="Valor", y="Nome", color="Obra", orientation="h", title="Top 10 Maiores Adiantamentos")
        
        # Pareto: Ignora separação de obra para ver o todo acumulado
        pareto_df = df.groupby("Funcao")["Valor"].sum().sort_values(ascending=False).reset_index()
        pareto_df["Acumulado %"] = pareto_df["Valor"].cumsum() / pareto_df["Valor"].sum() * 100
        pareto_fig = px.line(pareto_df, x="Funcao", y="Acumulado %", markers=True, title="Concentracao de Adiantamentos (Pareto)")
        pareto_fig.add_hline(y=80, line_dash="dash", line_color=COLORS["green"], annotation_text="80%")

        # Boxplot agora separado por Obra
        dist_fig = px.box(df, x="Funcao", y="Valor", color="Obra", title="Distribuicao de Valores por Funcao")

        role_fig.update_layout(**PLOT_LAYOUT)
        employee_fig.update_layout(**PLOT_LAYOUT)
        pareto_fig.update_layout(**PLOT_LAYOUT)
        dist_fig.update_layout(**PLOT_LAYOUT)

        return (
            [
                card("Total de adiantamentos", brl(df["Valor"].sum())),
                card("Colaboradores",          str(len(df))),
                card("Ticket medio",           brl(df["Valor"].mean())),
                card("Maior adiantamento",     brl(df["Valor"].max())),
            ],
            role_fig, pareto_fig, employee_fig, dist_fig
        )
    @app.callback(
        Output("active-chart-filter", "children"),
        Input("chart-filters", "data"),
    )
    def display_chart_filters(filters):
        if not filters:
            return "Dashboard pronto para interacao. Os filtros visuais foram ajustados."
        return "Filtros ativos: " + " | ".join(f"{k}: {v}" for k, v in filters.items())

    return app

if __name__ == "__main__":
    build_app().run(debug=True)
