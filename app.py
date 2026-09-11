import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pdfplumber
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="BI & Analytics Obra Marquise - Alfa Construtora",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    div.stMetric {
        background-color: #1A1C24;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #C41E3A;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div.stMetric label, div.stMetric [data-testid="stMetricValue"], div.stMetric div {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] { background-color: #161922; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #1A1C24;
        color: #FFFFFF;
        border: 1px solid #333333;
        padding: 8px 16px;
        margin-bottom: 5px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #C41E3A;
        color: white;
        border-color: #C41E3A;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# FUNÇÕES DE AUXÍLIO E TRATAMENTO SEGURO
# -----------------------------------------------------------------------------

def parse_float(val):
    if pd.isna(val) or str(val).strip() == '':
        return 0.0
    try:
        clean_str = str(val).replace(',', '.').strip()
        return float(clean_str)
    except ValueError:
        return 0.0

LAYOUT_DARK = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='white',
)

@st.cache_data
def load_financial_data():
    file_env = os.getenv("DATA_FILE", "FINANCEIRO_ALFA.xlsx")
    file_path = os.path.join(DATA_DIR, os.path.basename(file_env)) if not os.path.isabs(file_env) else file_env

    if not os.path.exists(file_path):
        return pd.DataFrame()

    try:
        xls = pd.ExcelFile(file_path)
        all_data = []
        for sheet in xls.sheet_names:
            if sheet == 'Planilha1':
                continue
            df_sheet = pd.read_excel(file_path, sheet_name=sheet)
            if df_sheet.shape[0] > 3:
                df_clean = df_sheet.iloc[3:].copy()
                df_clean.columns = ['Despesa', 'Departamento', 'Valor', 'Parcela', 'Vencimento', 'Data_Pagamento', 'Fonte', 'Status', 'Obs']
                df_clean['Mês'] = sheet
                all_data.append(df_clean)

        if not all_data:
            return pd.DataFrame()

        df_total = pd.concat(all_data, ignore_index=True)
        df_total['Valor'] = pd.to_numeric(df_total['Valor'], errors='coerce')
        df_total['Departamento'] = df_total['Departamento'].fillna('NÃO INFORMADO').astype(str)
        df_total['Status'] = df_total['Status'].fillna('EM ABERTO').astype(str).str.upper().str.strip()
        df_total['Status'] = df_total['Status'].replace(['NAN', 'NONE', ''], 'EM ABERTO')
        df_total['Obs'] = df_total['Obs'].fillna('').astype(str)
        df_total['Fonte'] = df_total['Fonte'].fillna('NÃO INFORMADO').astype(str).str.strip()

        # Datas com formato original preservado para cálculos
        df_total['Vencimento_dt'] = pd.to_datetime(df_total['Vencimento'], errors='coerce')
        df_total['Pagamento_dt'] = pd.to_datetime(df_total['Data_Pagamento'], errors='coerce')

        df_total['Vencimento'] = df_total['Vencimento_dt'].dt.strftime('%d/%m/%Y').fillna('Não informado')
        df_total['Data_Pagamento'] = df_total['Pagamento_dt'].dt.strftime('%d/%m/%Y').fillna('Pendente')

        # Aging: dias entre vencimento e pagamento (negativo = antecipado, positivo = atrasado)
        df_total['Aging_dias'] = (df_total['Pagamento_dt'] - df_total['Vencimento_dt']).dt.days

        return df_total
    except Exception:
        return pd.DataFrame()

@st.cache_data
def load_and_transform_intertravado():
    pdf_path = os.path.join(DATA_DIR, "MEDIÇÃO GERAL 8 - MARQUISE (PISO INTERTRAVADO).pdf")
    cols_default = ["Data", "Bairro", "Rua", "Número", "Largura", "Comprimento", "Area_m2"]
    if not os.path.exists(pdf_path):
        return pd.DataFrame(columns=cols_default)

    rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for r in table:
                        if r and len(r) >= 5 and r[0] != 'DATA':
                            rows.append(r)

        parsed_rows = []
        for r in rows:
            data    = r[0] if len(r) > 0 else ''
            bairro  = r[1] if len(r) > 1 else ''
            rua     = r[2] if len(r) > 2 else ''
            numero  = r[3] if len(r) > 3 else ''
            m2_val  = parse_float(r[-1])
            comp_val = parse_float(r[-2]) if len(r) >= 6 else 0.0
            larg_val = parse_float(r[-3]) if len(r) >= 7 else 0.0

            if m2_val > 0 or rua != '':
                parsed_rows.append({
                    "Data": str(data).replace('\n', ' ').strip(),
                    "Bairro": str(bairro).replace('\n', ' ').strip(),
                    "Rua": str(rua).replace('\n', ' ').strip(),
                    "Número": str(numero).replace('\n', ' ').strip(),
                    "Largura": larg_val,
                    "Comprimento": comp_val,
                    "Area_m2": m2_val
                })

        df = pd.DataFrame(parsed_rows)
        if df.empty or 'Area_m2' not in df.columns:
            return pd.DataFrame(columns=cols_default)
        return df[df['Area_m2'] > 0]
    except Exception:
        return pd.DataFrame(columns=cols_default)

@st.cache_data
def load_and_transform_especiais():
    pdf_path = os.path.join(DATA_DIR, "MEDIÇÃO GERAL 8 - JUNHO - (PISOS ESPECIAIS).pdf")
    cols_default = ["Bairro", "Rua", "Número", "Area_m2"]
    if not os.path.exists(pdf_path):
        return pd.DataFrame(columns=cols_default)

    rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for r in table:
                        if r and len(r) >= 4 and 'ENDEREÇO' not in str(r[0]):
                            rows.append(r)

        parsed_rows = []
        for r in rows:
            rua    = r[2] if len(r) > 2 else ''
            numero = r[3] if len(r) > 3 else ''
            area_val = parse_float(r[-1]) if len(r) >= 8 else parse_float(r[-2])

            if area_val > 0:
                parsed_rows.append({
                    "Bairro": str(r[1]).replace('\n', ' ').strip() if len(r) > 1 else 'Ribeirópolis',
                    "Rua": str(rua).replace('\n', ' ').strip(),
                    "Número": str(numero).replace('\n', ' ').strip(),
                    "Area_m2": area_val
                })

        df = pd.DataFrame(parsed_rows)
        if df.empty or 'Area_m2' not in df.columns:
            return pd.DataFrame(columns=cols_default)
        return df[df['Area_m2'] > 0]
    except Exception:
        return pd.DataFrame(columns=cols_default)

@st.cache_data
def load_and_transform_esgoto():
    pdf_path = os.path.join(DATA_DIR, "MEDIÇÃO 08 - MARQUISE (LIGAÇÕES POSTERIORES).pdf")
    cols_default = ["Bairro", "Rua", "Número", "Qtd_Ligacao", "Status_Tecnico"]
    if not os.path.exists(pdf_path):
        return pd.DataFrame(columns=cols_default)

    rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for r in table:
                        if r and len(r) >= 4 and r[0] != 'BAIRRO':
                            rows.append(r)

        parsed_rows = []
        for r in rows:
            bairro     = r[0] if len(r) > 0 else ''
            rua        = r[1] if len(r) > 1 else ''
            numero     = r[2] if len(r) > 2 else ''
            status_val = parse_float(r[3]) if len(r) > 3 else 0.0
            status_desc = (
                "Concluída" if status_val == 1.0
                else ("Parcial / Refazer" if status_val == 0.5
                      else "Sem Ramal / Pendente")
            )

            if str(rua).strip() != '':
                parsed_rows.append({
                    "Bairro": str(bairro).replace('\n', ' ').strip(),
                    "Rua": str(rua).replace('\n', ' ').strip(),
                    "Número": str(numero).replace('\n', ' ').strip(),
                    "Qtd_Ligacao": status_val,
                    "Status_Tecnico": status_desc
                })

        df = pd.DataFrame(parsed_rows)
        if df.empty or 'Qtd_Ligacao' not in df.columns:
            return pd.DataFrame(columns=cols_default)
        return df
    except Exception:
        return pd.DataFrame(columns=cols_default)

@st.cache_data
def load_and_transform_concreto():
    pdf_path = os.path.join(DATA_DIR, "MEDIÇÃO 08 - MARQUISE (CONCRETO).pdf")
    cols_default = ["Bairro", "Rua", "Número", "Largura", "Comprimento", "Area_m2"]
    if not os.path.exists(pdf_path):
        return pd.DataFrame(columns=cols_default)

    rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for r in table:
                        if r and len(r) >= 4 and r[0] != 'BAIRRO':
                            rows.append(r)

        parsed_rows = []
        for r in rows:
            bairro   = r[0] if len(r) > 0 else ''
            rua      = r[1] if len(r) > 1 else ''
            numero   = r[2] if len(r) > 2 else ''
            area_val = parse_float(r[-1])
            comp_val = parse_float(r[-2]) if len(r) >= 5 else 0.0
            larg_val = parse_float(r[-3]) if len(r) >= 6 else 0.0

            if area_val > 0:
                parsed_rows.append({
                    "Bairro": str(bairro).replace('\n', ' ').strip(),
                    "Rua": str(rua).replace('\n', ' ').strip(),
                    "Número": str(numero).replace('\n', ' ').strip(),
                    "Largura": larg_val,
                    "Comprimento": comp_val,
                    "Area_m2": area_val
                })

        df = pd.DataFrame(parsed_rows)
        if df.empty or 'Area_m2' not in df.columns:
            return pd.DataFrame(columns=cols_default)
        return df[df['Area_m2'] > 0]
    except Exception:
        return pd.DataFrame(columns=cols_default)


# -----------------------------------------------------------------------------
# HELPERS ANALÍTICOS
# -----------------------------------------------------------------------------

def build_pareto(df: pd.DataFrame, col_label: str, col_value: str) -> go.Figure:
    """Gráfico de Pareto (80/20): bars descendentes + linha de % acumulado."""
    df_sorted = df.groupby(col_label)[col_value].sum().reset_index()
    df_sorted = df_sorted.sort_values(col_value, ascending=False).reset_index(drop=True)
    df_sorted = df_sorted[df_sorted[col_value] > 0]
    total = df_sorted[col_value].sum()
    df_sorted['pct_acum'] = (df_sorted[col_value].cumsum() / total * 100).round(1)

    fig = go.Figure()
    fig.add_bar(
        x=df_sorted[col_label], y=df_sorted[col_value],
        name='Valor (R$)', marker_color='#C41E3A',
        text=df_sorted[col_value].apply(lambda v: f'R$ {v:,.0f}'),
        textposition='outside'
    )
    fig.add_scatter(
        x=df_sorted[col_label], y=df_sorted['pct_acum'],
        name='% Acumulado', yaxis='y2',
        mode='lines+markers', line=dict(color='#FF9800', width=2),
        marker=dict(size=6)
    )
    fig.add_hline(y=80, yref='y2', line_dash='dash', line_color='#888888',
                  annotation_text='80%', annotation_position='right')
    fig.update_layout(
        **LAYOUT_DARK,
        yaxis=dict(title='Valor (R$)', showgrid=False),
        yaxis2=dict(title='% Acumulado', overlaying='y', side='right',
                    range=[0, 110], showgrid=False),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        bargap=0.3
    )
    return fig


def build_heatmap_mes_depto(df: pd.DataFrame, meses_ordem: list) -> go.Figure:
    """Heatmap de valor gasto: eixo X = mês, eixo Y = departamento."""
    pivot = df.pivot_table(index='Departamento', columns='Mês', values='Valor',
                           aggfunc='sum', fill_value=0)
    pivot = pivot.reindex(columns=[m for m in meses_ordem if m in pivot.columns])

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, '#1A1C24'], [0.5, '#C41E3A'], [1, '#FF6B6B']],
        text=[[f'R$ {v:,.0f}' for v in row] for row in pivot.values],
        texttemplate='%{text}',
        hovertemplate='Mês: %{x}<br>Depto: %{y}<br>Valor: %{text}<extra></extra>',
        showscale=True
    ))
    fig.update_layout(**LAYOUT_DARK, xaxis_title='Mês', yaxis_title='Departamento')
    return fig


def build_aging_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart horizontal de aging: agrupa por faixa de dias de atraso/antecipação."""
    df_aging = df.dropna(subset=['Aging_dias']).copy()
    if df_aging.empty:
        return go.Figure()

    bins   = [-999, -1, 7, 15, 30, 999]
    labels = ['Antecipado', 'No Prazo (0-7d)', 'Leve Atraso (8-15d)', 'Atraso Moderado (16-30d)', 'Atraso Crítico (>30d)']
    df_aging['Faixa'] = pd.cut(df_aging['Aging_dias'], bins=bins, labels=labels)

    resumo = df_aging.groupby('Faixa', observed=True).agg(
        Qtd=('Aging_dias', 'count'),
        Valor=('Valor', 'sum')
    ).reset_index()

    cores = ['#4CAF50', '#8BC34A', '#FF9800', '#FF5722', '#F44336']
    fig = go.Figure()
    for i, row in resumo.iterrows():
        fig.add_bar(
            x=[row['Valor']], y=[str(row['Faixa'])],
            orientation='h',
            name=str(row['Faixa']),
            marker_color=cores[i % len(cores)],
            text=[f"R$ {row['Valor']:,.0f}  ({int(row['Qtd'])} pagamentos)"],
            textposition='outside'
        )
    fig.update_layout(
        **LAYOUT_DARK,
        showlegend=False,
        xaxis_title='Valor Total (R$)',
        yaxis_title='',
        bargap=0.35
    )
    return fig


def build_fonte_status_chart(df: pd.DataFrame) -> go.Figure:
    """Stacked bar: eixo X = Fonte, cores = Status (PAGO / EM ABERTO / outros)."""
    df_f = df.groupby(['Fonte', 'Status'])['Valor'].sum().reset_index()
    df_f = df_f[df_f['Valor'] > 0]

    cores_status = {
        'PAGO': '#4CAF50',
        'EM ABERTO': '#C41E3A',
    }

    fig = go.Figure()
    for status in df_f['Status'].unique():
        sub = df_f[df_f['Status'] == status]
        fig.add_bar(
            x=sub['Fonte'],
            y=sub['Valor'],
            name=status,
            marker_color=cores_status.get(status, '#888888'),
            text=sub['Valor'].apply(lambda v: f'R$ {v:,.0f}'),
            textposition='inside'
        )
    fig.update_layout(
        **LAYOUT_DARK,
        barmode='stack',
        xaxis_title='Fonte de Pagamento',
        yaxis_title='Valor (R$)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, bgcolor='rgba(0,0,0,0)')
    )
    return fig


def build_scatter_dimensional(df: pd.DataFrame, titulo: str) -> go.Figure:
    """Scatter Largura × Comprimento com tamanho proporcional à área e highlight de outliers."""
    df = df[(df['Largura'] > 0) & (df['Comprimento'] > 0)].copy()
    if df.empty:
        return go.Figure()

    q3 = df['Area_m2'].quantile(0.75)
    iqr = df['Area_m2'].quantile(0.75) - df['Area_m2'].quantile(0.25)
    limite_outlier = q3 + 1.5 * iqr

    df['Perfil'] = df['Area_m2'].apply(lambda v: 'Outlier (>Q3+1.5IQR)' if v > limite_outlier else 'Normal')
    df['Endereço'] = df['Rua'] + ', ' + df['Número']

    fig = px.scatter(
        df, x='Largura', y='Comprimento',
        size='Area_m2', color='Perfil',
        hover_name='Endereço',
        hover_data={'Area_m2': ':.2f', 'Largura': ':.2f', 'Comprimento': ':.2f'},
        color_discrete_map={'Normal': '#C41E3A', 'Outlier (>Q3+1.5IQR)': '#FF9800'},
        size_max=40,
        title=titulo
    )
    fig.update_layout(**LAYOUT_DARK)
    return fig


def build_boxplot_servicos(df_inter, df_espec, df_conc) -> go.Figure:
    """Boxplot comparativo de distribuição de área (m²) entre os 3 tipos de serviço."""
    fig = go.Figure()
    datasets = [
        ('Piso Intertravado', df_inter, '#C41E3A'),
        ('Pisos Especiais',   df_espec, '#FF9800'),
        ('Calçada Concreto',  df_conc,  '#4CAF50'),
    ]
    for label, df, cor in datasets:
        if 'Area_m2' in df.columns and not df.empty:
            fig.add_box(
                y=df['Area_m2'], name=label,
                marker_color=cor, boxmean='sd',
                line_color='white'
            )
    fig.update_layout(
        **LAYOUT_DARK,
        yaxis_title='Área (m²)',
        showlegend=False
    )
    return fig


def build_heatmap_bairro_servico(df_inter, df_espec, df_conc, df_esg) -> go.Figure:
    """Heatmap Bairro × Tipo de Serviço mostrando m² ou unidades produzidas."""
    frames = []
    for df, col, label in [
        (df_inter, 'Area_m2',     'Intertravado (m²)'),
        (df_espec, 'Area_m2',     'Pisos Especiais (m²)'),
        (df_conc,  'Area_m2',     'Concreto (m²)'),
        (df_esg,   'Qtd_Ligacao', 'Esgoto (un)'),
    ]:
        if 'Bairro' in df.columns and col in df.columns and not df.empty:
            sub = df.groupby('Bairro')[col].sum().reset_index()
            sub.columns = ['Bairro', 'Valor']
            sub['Serviço'] = label
            frames.append(sub)

    if not frames:
        return go.Figure()

    df_all = pd.concat(frames, ignore_index=True)
    pivot = df_all.pivot_table(index='Bairro', columns='Serviço', values='Valor', fill_value=0)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, '#1A1C24'], [0.5, '#C41E3A'], [1, '#FF6B6B']],
        text=[[f'{v:,.1f}' for v in row] for row in pivot.values],
        texttemplate='%{text}',
        hovertemplate='Serviço: %{x}<br>Bairro: %{y}<br>Qtd: %{text}<extra></extra>',
    ))
    fig.update_layout(**LAYOUT_DARK, xaxis_title='Tipo de Serviço', yaxis_title='Bairro')
    return fig


def build_funnel_esgoto(df_esg: pd.DataFrame) -> go.Figure:
    """Funnel chart de progresso técnico do esgoto: Concluída → Parcial → Pendente."""
    if df_esg.empty:
        return go.Figure()

    contagem = df_esg['Status_Tecnico'].value_counts()
    ordem = ['Concluída', 'Parcial / Refazer', 'Sem Ramal / Pendente']
    valores = [contagem.get(s, 0) for s in ordem]
    cores   = ['#4CAF50', '#FF9800', '#F44336']

    fig = go.Figure(go.Funnel(
        y=ordem,
        x=valores,
        textinfo='value+percent initial',
        marker=dict(color=cores),
        connector=dict(line=dict(color='#444', width=1))
    ))
    fig.update_layout(**LAYOUT_DARK, showlegend=False)
    return fig


# -----------------------------------------------------------------------------
# INTERFACE E NAVEGAÇÃO
# -----------------------------------------------------------------------------

logo_path = os.path.join(BASE_DIR, "alfa_logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=180)
else:
    st.sidebar.title("🏢 ALFA CONSTRUTORA")

st.sidebar.markdown("---")

if "modulo" not in st.session_state:
    st.session_state.modulo = "Financeiro"
if "servico_marquise" not in st.session_state:
    st.session_state.servico_marquise = "Visão Geral"

st.sidebar.subheader("📌 Módulos do Sistema")
col_nav1, col_nav2 = st.sidebar.columns(2)

if col_nav1.button("💰 Financeiro"):
    st.session_state.modulo = "Financeiro"
if col_nav2.button("🏗️ Obras"):
    st.session_state.modulo = "Obras"

st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# MÓDULO 1: FINANCEIRO
# -----------------------------------------------------------------------------
if st.session_state.modulo == "Financeiro":
    st.title("📊 Dashboard Financeiro - Alfa Construtora")
    st.markdown("Acompanhamento gerencial de despesas, departamentos e status de pagamentos.")
    st.markdown("---")

    df_total = load_financial_data()

    if df_total.empty:
        st.warning(f"⚠️ Nenhuma planilha encontrada ou dados inválidos em `{DATA_DIR}`.")
    else:
        meses_ordem = ['JAN-2026', 'FEV', 'MARÇO', 'ABRIL', 'MAIO', 'JUN', 'JUL']
        meses_disponiveis = [m for m in meses_ordem if m in df_total['Mês'].unique()]

        st.sidebar.header("🎛️ Filtros Financeiros")
        mes_selecionado = st.sidebar.multiselect("Filtrar por Mês", options=meses_disponiveis, default=meses_disponiveis)
        deptos_disponiveis = sorted(df_total['Departamento'].unique().tolist())
        depto_selecionado = st.sidebar.multiselect("Filtrar por Departamento", options=deptos_disponiveis, default=deptos_disponiveis)
        status_disponiveis = sorted(df_total['Status'].unique().tolist())
        status_selecionado = st.sidebar.multiselect("Filtrar por Status", options=status_disponiveis, default=status_disponiveis)

        df_filtered = df_total[
            (df_total['Mês'].isin(mes_selecionado)) &
            (df_total['Departamento'].isin(depto_selecionado)) &
            (df_total['Status'].isin(status_selecionado))
        ]

        total_gasto  = df_filtered['Valor'].sum()
        total_pago   = df_filtered[df_filtered['Status'] == 'PAGO']['Valor'].sum()
        total_aberto = df_filtered[df_filtered['Status'] == 'EM ABERTO']['Valor'].sum()
        media_despesa = df_filtered['Valor'].mean() if not df_filtered.empty else 0
        pct_pago = (total_pago / total_gasto * 100) if total_gasto > 0 else 0

        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        col_kpi1.metric("Total de Despesas",        f"R$ {total_gasto:,.2f}")
        col_kpi2.metric("Total Pago",               f"R$ {total_pago:,.2f}",   f"{pct_pago:.1f}% do total")
        col_kpi3.metric("Total em Aberto",          f"R$ {total_aberto:,.2f}")
        col_kpi4.metric("Ticket Médio por Despesa", f"R$ {media_despesa:,.2f}")

        st.markdown("---")

        # --- LINHA 1: Despesas por departamento + Proporção por status ---
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Despesas por Departamento")
            df_dept = df_filtered.groupby('Departamento')['Valor'].sum().reset_index().sort_values('Valor', ascending=True)
            fig_dept = px.bar(df_dept, x='Valor', y='Departamento', orientation='h',
                              color_discrete_sequence=['#C41E3A'], text_auto=',.0f')
            fig_dept.update_layout(**LAYOUT_DARK)
            st.plotly_chart(fig_dept, width='stretch')

        with col_g2:
            st.subheader("Proporção por Status de Pagamento")
            df_status_pie = df_filtered.groupby('Status')['Valor'].sum().reset_index()
            fig_status = px.pie(df_status_pie, names='Status', values='Valor', hole=0.4,
                                color_discrete_sequence=['#4CAF50', '#C41E3A', '#FF9800', '#888888'])
            fig_status.update_layout(**LAYOUT_DARK)
            st.plotly_chart(fig_status, width='stretch')

        # --- LINHA 2: Evolução mensal + Fonte por Status (stacked) ---
        col_g3, col_g4 = st.columns(2)
        with col_g3:
            st.subheader("Evolução das Despesas por Mês")
            df_mes = df_filtered.groupby('Mês')['Valor'].sum().reindex(meses_disponiveis).reset_index()
            fig_mes = px.line(df_mes, x='Mês', y='Valor', markers=True, line_shape='spline',
                              color_discrete_sequence=['#C41E3A'])
            fig_mes.update_layout(**LAYOUT_DARK)
            st.plotly_chart(fig_mes, width='stretch')

        with col_g4:
            st.subheader("Fonte de Pagamento × Status")
            st.caption("Visualiza quanto cada fonte pagou vs. ainda tem em aberto")
            fig_fonte_status = build_fonte_status_chart(df_filtered)
            st.plotly_chart(fig_fonte_status, width='stretch')

        st.markdown("---")

        # --- LINHA 3: Pareto de despesas ---
        st.subheader("📉 Análise de Pareto — Quais despesas concentram 80% do custo?")
        st.caption("Identifica os poucos itens que representam a maior parte do gasto. Útil para priorização de negociação e controle.")
        df_pareto_input = df_filtered.dropna(subset=['Despesa', 'Valor'])
        df_pareto_input = df_pareto_input[df_pareto_input['Valor'] > 0]
        if not df_pareto_input.empty:
            fig_pareto = build_pareto(df_pareto_input, 'Despesa', 'Valor')
            st.plotly_chart(fig_pareto, width='stretch')
        else:
            st.info("Sem dados suficientes para o Pareto com os filtros atuais.")

        st.markdown("---")

        # --- LINHA 4: Heatmap Mês × Departamento ---
        st.subheader("🗓️ Heatmap de Sazonalidade — Mês × Departamento")
        st.caption("Revela em quais meses cada departamento concentra mais gastos, sem necessidade de filtros.")
        fig_heat = build_heatmap_mes_depto(df_total, meses_ordem)
        st.plotly_chart(fig_heat, width='stretch')

        st.markdown("---")

        # --- LINHA 5: Aging de pagamentos ---
        st.subheader("⏱️ Aging de Pagamentos — Pontualidade Financeira")
        st.caption("Classifica pagamentos por faixa de dias em relação ao vencimento. Detecta padrões de atraso e antecipações.")
        df_aging_filtrado = df_filtered.dropna(subset=['Aging_dias'])
        if not df_aging_filtrado.empty:
            fig_aging = build_aging_chart(df_aging_filtrado)
            st.plotly_chart(fig_aging, width='stretch')
        else:
            st.info("Sem datas de pagamento suficientes para calcular o aging com os filtros atuais.")

        st.markdown("---")
        st.subheader("📋 Detalhamento Analítico dos Dados")
        cols_show = ['Despesa', 'Departamento', 'Valor', 'Parcela', 'Vencimento', 'Data_Pagamento', 'Fonte', 'Status', 'Obs', 'Mês']
        st.dataframe(df_filtered[cols_show], width='stretch')


# -----------------------------------------------------------------------------
# MÓDULO 2: OBRAS
# -----------------------------------------------------------------------------
else:
    st.sidebar.subheader("🏗️ Seleção de Obra")
    st.sidebar.selectbox("Obra Ativa:", ["Obra Marquise (Junho/2026)"])

    st.sidebar.markdown("### 🛠️ Serviços da Obra")
    if st.sidebar.button("📊 Visão Geral Consolidada"):
        st.session_state.servico_marquise = "Visão Geral"
    if st.sidebar.button("🧱 Piso Intertravado"):
        st.session_state.servico_marquise = "Intertravado"
    if st.sidebar.button("🪨 Pisos Especiais"):
        st.session_state.servico_marquise = "Especiais"
    if st.sidebar.button("🚰 Ligações de Esgoto"):
        st.session_state.servico_marquise = "Esgoto"
    if st.sidebar.button("🧱 Calçada em Concreto"):
        st.session_state.servico_marquise = "Concreto"

    df_inter = load_and_transform_intertravado()
    df_espec = load_and_transform_especiais()
    df_esg   = load_and_transform_esgoto()
    df_conc  = load_and_transform_concreto()

    # -------------------------------------------------------------------------
    # VISÃO GERAL CONSOLIDADA
    # -------------------------------------------------------------------------
    if st.session_state.servico_marquise == "Visão Geral":
        st.title("🏗️ Analytics Executivo — Obra Marquise")
        st.markdown("**Acompanhamento de Rendimento da Medição Nº 08 (Junho/2026)**")
        st.markdown("---")

        total_m2_conc  = df_conc['Area_m2'].sum()  if 'Area_m2'     in df_conc.columns  else 0.0
        total_m2_inter = df_inter['Area_m2'].sum() if 'Area_m2'     in df_inter.columns else 0.0
        total_m2_espec = df_espec['Area_m2'].sum() if 'Area_m2'     in df_espec.columns else 0.0
        total_un_esg   = df_esg['Qtd_Ligacao'].sum() if 'Qtd_Ligacao' in df_esg.columns else 0.0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Calçadas Concreto",   f"{total_m2_conc:,.2f} m²",  f"{len(df_conc)} Trechos")
        kpi2.metric("Piso Intertravado",   f"{total_m2_inter:,.2f} m²", f"{len(df_inter)} Trechos")
        kpi3.metric("Pisos Especiais",     f"{total_m2_espec:,.2f} m²", f"{len(df_espec)} Trechos")
        kpi4.metric("Ligações de Esgoto",  f"{total_un_esg:,.1f} un",   f"{len(df_esg)} Pontos")

        st.markdown("---")

        # --- Volume por categoria + share ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Volume de Pavimentação por Categoria (m²)")
            df_comp = pd.DataFrame({
                "Serviço": ["Calçada Concreto", "Piso Intertravado", "Pisos Especiais"],
                "Área (m²)": [total_m2_conc, total_m2_inter, total_m2_espec]
            })
            fig = px.bar(df_comp, x="Serviço", y="Área (m²)", color="Serviço", text_auto='.2f',
                         color_discrete_sequence=['#C41E3A', '#FF4B4B', '#FF6B6B'])
            fig.update_layout(**LAYOUT_DARK)
            st.plotly_chart(fig, width='stretch')

        with c2:
            st.subheader("Share Percentual de Pavimentação")
            fig_donut = px.pie(df_comp, names="Serviço", values="Área (m²)", hole=0.4,
                               color_discrete_sequence=['#C41E3A', '#FF4B4B', '#FF6B6B'])
            fig_donut.update_layout(**LAYOUT_DARK)
            st.plotly_chart(fig_donut, width='stretch')

        st.markdown("---")

        # --- Boxplot comparativo + Heatmap bairro × serviço ---
        st.subheader("📦 Distribuição de Trechos por Tipo de Serviço")
        st.caption("Compara a variância de tamanho dos trechos executados entre os 3 tipos de pavimentação. Outliers indicam trechos atípicos.")
        fig_box = build_boxplot_servicos(df_inter, df_espec, df_conc)
        st.plotly_chart(fig_box, width='stretch')

        st.markdown("---")

        st.subheader("🗺️ Mapa de Calor — Produção por Bairro × Tipo de Serviço")
        st.caption("Identifica quais bairros concentram quais tipos de obra. Útil para logística de equipes e insumos.")
        fig_heat_obra = build_heatmap_bairro_servico(df_inter, df_espec, df_conc, df_esg)
        st.plotly_chart(fig_heat_obra, width='stretch')

    # -------------------------------------------------------------------------
    # PISO INTERTRAVADO
    # -------------------------------------------------------------------------
    elif st.session_state.servico_marquise == "Intertravado":
        st.title("🧱 Analytics: Calçada de Piso Intertravado")
        st.markdown("**Análise de distribuição e maiores frentes de trabalho**")

        c1, c2, c3 = st.columns(3)
        c1.metric("Área Total Executada", f"{df_inter['Area_m2'].sum():,.2f} m²")
        c2.metric("Média por Trecho",     f"{df_inter['Area_m2'].mean():,.2f} m²" if not df_inter.empty else "0 m²")
        c3.metric("Maior Trecho Único",   f"{df_inter['Area_m2'].max():,.2f} m²"  if not df_inter.empty else "0 m²")

        st.markdown("---")

        if not df_inter.empty:
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Top 10 Maior Metragem por Endereço")
                top10 = df_inter.sort_values("Area_m2", ascending=False).head(10).copy()
                top10['Local'] = top10['Rua'] + ", " + top10['Número']
                fig = px.bar(top10, x="Area_m2", y="Local", orientation="h", color="Area_m2",
                             color_continuous_scale="Reds", text_auto='.2f')
                fig.update_layout(**LAYOUT_DARK, yaxis={'autorange': 'reversed'})
                st.plotly_chart(fig, width='stretch')

            with g2:
                st.subheader("Distribuição do Tamanho das Calçadas (m²)")
                fig_hist = px.histogram(df_inter, x="Area_m2", nbins=15,
                                        color_discrete_sequence=['#C41E3A'])
                fig_hist.update_layout(**LAYOUT_DARK,
                                       xaxis_title="Metragem Quadrada (m²)",
                                       yaxis_title="Ocorrências")
                st.plotly_chart(fig_hist, width='stretch')

            st.markdown("---")
            st.subheader("📐 Scatter Dimensional — Identificação de Trechos Atípicos")
            st.caption("Cada ponto é um trecho. Tamanho proporcional à área. Pontos laranja são outliers estatísticos (IQR × 1.5).")
            fig_scatter = build_scatter_dimensional(df_inter, "Largura × Comprimento — Intertravado")
            st.plotly_chart(fig_scatter, width='stretch')

        with st.expander("🔍 Visualizar Dados Analíticos Formatados"):
            st.dataframe(df_inter, width='stretch')

    # -------------------------------------------------------------------------
    # PISOS ESPECIAIS
    # -------------------------------------------------------------------------
    elif st.session_state.servico_marquise == "Especiais":
        st.title("🪨 Analytics: Pisos Especiais")
        st.markdown("**Concentração por Logradouro e Análise de Ocorrências**")

        c1, c2 = st.columns(2)
        c1.metric("Total Medido",       f"{df_espec['Area_m2'].sum():,.2f} m²")
        c2.metric("Quantidade de Locais", f"{len(df_espec)}")

        st.markdown("---")

        if not df_espec.empty:
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Consumo por Logradouro (m²) — Top 8")
                df_rua = df_espec.groupby('Rua')['Area_m2'].sum().reset_index().sort_values("Area_m2", ascending=False).head(8)
                fig = px.bar(df_rua, x="Area_m2", y="Rua", orientation="h",
                             color_discrete_sequence=['#E53935'], text_auto='.2f')
                fig.update_layout(**LAYOUT_DARK, yaxis={'autorange': 'reversed'})
                st.plotly_chart(fig, width='stretch')

            with g2:
                st.subheader("Trechos Padrão vs. Grande Trecho (>10m²)")
                df_espec_c = df_espec.copy()
                df_espec_c['Perfil'] = df_espec_c['Area_m2'].apply(
                    lambda x: 'Grande Trecho (>10m²)' if x >= 10 else 'Padrão (<10m²)'
                )
                fig_pie = px.pie(df_espec_c, names="Perfil", values="Area_m2",
                                 color_discrete_sequence=['#C41E3A', '#555555'])
                fig_pie.update_layout(**LAYOUT_DARK)
                st.plotly_chart(fig_pie, width='stretch')

        with st.expander("🔍 Visualizar Dados Analíticos Formatados"):
            st.dataframe(df_espec, width='stretch')

    # -------------------------------------------------------------------------
    # LIGAÇÕES DE ESGOTO
    # -------------------------------------------------------------------------
    elif st.session_state.servico_marquise == "Esgoto":
        st.title("🚰 Analytics: Ligações Posteriores de Esgoto")
        st.markdown("**Status Técnico de Conclusão e Densidade por Logradouro**")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Ligações Efetuadas", f"{df_esg['Qtd_Ligacao'].sum():,.1f} un")
        c2.metric("Pontos Vistoriados",           f"{len(df_esg)}")
        eficiencia = (df_esg['Qtd_Ligacao'].sum() / len(df_esg)) * 100 if len(df_esg) > 0 else 0
        c3.metric("Taxa de Conclusão Operacional", f"{eficiencia:.1f}%")

        st.markdown("---")

        if not df_esg.empty:
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("🔽 Funil de Conclusão Técnica")
                st.caption("Mostra a progressão de status do esgoto: da conclusão total até pendências críticas.")
                fig_funnel = build_funnel_esgoto(df_esg)
                st.plotly_chart(fig_funnel, width='stretch')

            with g2:
                st.subheader("Volume de Ligações Concluídas por Rua — Top 8")
                df_rua_esg = df_esg.groupby('Rua')['Qtd_Ligacao'].sum().reset_index() \
                                   .sort_values("Qtd_Ligacao", ascending=False).head(8)
                fig_bar = px.bar(df_rua_esg, x="Qtd_Ligacao", y="Rua", orientation="h",
                                 color_discrete_sequence=['#C41E3A'], text_auto='.1f')
                fig_bar.update_layout(**LAYOUT_DARK, yaxis={'autorange': 'reversed'})
                st.plotly_chart(fig_bar, width='stretch')

        with st.expander("🔍 Visualizar Registros da Medição de Esgoto"):
            st.dataframe(df_esg, width='stretch')

    # -------------------------------------------------------------------------
    # CALÇADA EM CONCRETO
    # -------------------------------------------------------------------------
    elif st.session_state.servico_marquise == "Concreto":
        st.title("🧱 Analytics: Calçada em Concreto")
        st.markdown("**Análise Dimensional e Produção por Bairro/Logradouro**")

        c1, c2, c3 = st.columns(3)
        c1.metric("Área Concretada",  f"{df_conc['Area_m2'].sum():,.2f} m²")
        c2.metric("Total de Trechos", f"{len(df_conc)}")
        c3.metric("Média por Trecho", f"{df_conc['Area_m2'].mean():,.2f} m²" if not df_conc.empty else "0 m²")

        st.markdown("---")

        if not df_conc.empty:
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Volume Executado por Bairro")
                df_bairro = df_conc.groupby('Bairro')['Area_m2'].sum().reset_index()
                fig = px.bar(df_bairro, x="Bairro", y="Area_m2", color="Bairro", text_auto='.2f',
                             color_discrete_sequence=['#C41E3A', '#FF6B6B'])
                fig.update_layout(**LAYOUT_DARK)
                st.plotly_chart(fig, width='stretch')

            with g2:
                st.subheader("Concentração por Rua — Top 8")
                df_rua_conc = df_conc.groupby('Rua')['Area_m2'].sum().reset_index() \
                                     .sort_values("Area_m2", ascending=False).head(8)
                fig_bar = px.bar(df_rua_conc, x="Area_m2", y="Rua", orientation="h",
                                 color_discrete_sequence=['#C41E3A'], text_auto='.2f')
                fig_bar.update_layout(**LAYOUT_DARK, yaxis={'autorange': 'reversed'})
                st.plotly_chart(fig_bar, width='stretch')

            st.markdown("---")
            st.subheader("📐 Scatter Dimensional — Identificação de Trechos Atípicos")
            st.caption("Cada ponto é um trecho. Tamanho proporcional à área. Pontos laranja são outliers estatísticos (IQR × 1.5).")
            fig_scatter = build_scatter_dimensional(df_conc, "Largura × Comprimento — Concreto")
            st.plotly_chart(fig_scatter, width='stretch')

        with st.expander("🔍 Visualizar Registros da Medição de Concreto"):
            st.dataframe(df_conc, width='stretch')
