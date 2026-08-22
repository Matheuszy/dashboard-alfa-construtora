import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração da página
st.set_page_config(page_title="Dashboard Financeiro Alfa", layout="wide")

# Logo da empresa (Certifique-se de que o arquivo 'alfa_logo.png' esteja na mesma pasta)
# st.image("alfa_logo.png", width=200) 

st.title("Dashboard Financeiro - Alfa Construtora")

# Carregamento e limpeza dos dados
file_path = os.getenv("DATA_FILE")
df = pd.read_excel(file_path, sheet_name='JAN-2026')
df_clean = df.iloc[3:].copy()
df_clean.columns = ['Despesa', 'Departamento', 'Valor', 'Parcela', 'Vencimento', 'Data_Pagamento', 'Fonte', 'Status', 'Obs']
df_clean = df_clean.dropna(subset=['Despesa'])
df_clean['Valor'] = pd.to_numeric(df_clean['Valor'], errors='coerce')

# Sidebar para filtros
departamentos = df_clean['Departamento'].dropna().unique().tolist()
departamento_selecionado = st.sidebar.multiselect("Selecione o Departamento", options=departamentos, default=departamentos)
df_filtered = df_clean[df_clean['Departamento'].isin(departamento_selecionado)]

# Paleta de cores Alfa (Vermelho e Cinzas)
alfa_colors = ['#C41E3A', '#2E2E2E', '#505050', '#A0A0A0']

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Despesas por Departamento")
    fig1 = px.bar(df_filtered.groupby('Departamento')['Valor'].sum().reset_index(), 
                  x='Departamento', y='Valor', color_discrete_sequence=[alfa_colors[0]])
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Status de Pagamento")
    fig2 = px.pie(df_filtered, names='Status', values='Valor', color_discrete_sequence=alfa_colors)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Detalhamento das Despesas")
st.dataframe(df_filtered, use_container_width=True)