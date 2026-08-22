import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

# Configuração da página
st.set_page_config(page_title="Dashboard Financeiro - Alfa Construtora", layout="wide")

# Estilização CSS customizada
st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
    }
    div.stMetric {
        background-color: #1A1C24;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #C41E3A;
    }
    div.stMetric label, div.stMetric [data-testid="stMetricValue"], div.stMetric div {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] img {
        background: transparent !important;
        border-radius: 8px;
        padding: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Barra Lateral (Sidebar)
st.sidebar.image("alfa_logo.png", width=180)
st.sidebar.markdown("---")
st.sidebar.header("🎛️ Painel de Filtros")

# Carregamento de dados de todas as abas do Excel
file_path = os.getenv("DATA_FILE")
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

df_total = pd.concat(all_data, ignore_index=True)
df_total['Valor'] = pd.to_numeric(df_total['Valor'], errors='coerce')
df_total['Departamento'] = df_total['Departamento'].fillna('NÃO INFORMADO').astype(str)

# Tratamento seguro da coluna Status
df_total['Status'] = df_total['Status'].fillna('EM ABERTO').astype(str).str.upper().str.strip()
df_total['Status'] = df_total['Status'].replace(['NAN', 'NONE', ''], 'EM ABERTO')

# Tratamento seguro das colunas de data
df_total['Vencimento'] = pd.to_datetime(df_total['Vencimento'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('Não informado')
df_total['Data_Pagamento'] = pd.to_datetime(df_total['Data_Pagamento'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('Pendente')

# Ordenação cronológica correta dos meses
meses_ordem = ['JAN-2026', 'FEV', 'MARÇO', 'ABRIL', 'MAIO', 'JUN', 'JUL']
meses_disponiveis = [m for m in meses_ordem if m in df_total['Mês'].unique()]

# Filtros da Sidebar
mes_selecionado = st.sidebar.multiselect("Filtrar por Mês", options=meses_disponiveis, default=meses_disponiveis)

deptos_disponiveis = sorted(df_total['Departamento'].unique().tolist())
depto_selecionado = st.sidebar.multiselect("Filtrar por Departamento", options=deptos_disponiveis, default=deptos_disponiveis)

status_disponiveis = sorted(df_total['Status'].unique().tolist())
status_selecionado = st.sidebar.multiselect("Filtrar por Status", options=status_disponiveis, default=status_disponiveis)

# Aplicando filtros globais
df_filtered = df_total[
    (df_total['Mês'].isin(mes_selecionado)) & 
    (df_total['Departamento'].isin(depto_selecionado)) &
    (df_total['Status'].isin(status_selecionado))
]

# Cabeçalho Principal
st.title("📊 Dashboard Financeiro - Alfa Construtora")
st.markdown("Acompanhamento gerencial de despesas, departamentos e status de pagamentos.")
st.markdown("---")

# Métricas Principais (KPIs)
total_gasto = df_filtered['Valor'].sum()
total_pago = df_filtered[df_filtered['Status'] == 'PAGO']['Valor'].sum()
media_despesa = df_filtered['Valor'].mean() if not df_filtered.empty else 0

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
col_kpi1.metric("Total de Despesas", f"R$ {total_gasto:,.2f}")
col_kpi2.metric("Total Pago", f"R$ {total_pago:,.2f}")
col_kpi3.metric("Média por Despesa", f"R$ {media_despesa:,.2f}")

st.markdown("---")

# Paleta de Cores Alfa Construtora
alfa_colors = ['#C41E3A', '#FF4B4B', '#FF6B6B', '#333333', '#555555', '#888888']

# Linha 1 de Gráficos
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Despesas por Departamento")
    df_dept = df_filtered.groupby('Departamento')['Valor'].sum().reset_index().sort_values(by='Valor', ascending=True)
    fig_dept = px.bar(df_dept, x='Valor', y='Departamento', orientation='h', color_discrete_sequence=['#C41E3A'])
    fig_dept.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig_dept, width='stretch')

with col_g2:
    st.subheader("Proporção por Status de Pagamento")
    df_status = df_filtered.groupby('Status')['Valor'].sum().reset_index()
    fig_status = px.pie(df_status, names='Status', values='Valor', hole=0.4, color_discrete_sequence=alfa_colors)
    fig_status.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig_status, width='stretch')

col_g3, col_g4 = st.columns(2)

with col_g3:
    st.subheader("Evolução das Despesas por Mês")
    df_mes = df_filtered.groupby('Mês')['Valor'].sum().reindex(meses_disponiveis).reset_index()
    fig_mes = px.line(df_mes, x='Mês', y='Valor', markers=True, line_shape='spline', color_discrete_sequence=['#C41E3A'])
    fig_mes.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig_mes, width='stretch')

with col_g4:
    st.subheader("Despesas por Fonte de Pagamento")
    df_fonte = df_filtered.groupby('Fonte')['Valor'].sum().reset_index().dropna()
    if not df_fonte.empty:
        fig_fonte = px.bar(df_fonte, x='Fonte', y='Valor', color_discrete_sequence=['#E53935'])
        fig_fonte.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig_fonte, width='stretch')
    else:
        st.info("Nenhuma fonte de pagamento informada nos filtros atuais.")

st.markdown("---")
st.subheader("📋 Detalhamento Analítico dos Dados")
st.dataframe(df_filtered, width='stretch')