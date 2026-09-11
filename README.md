# 📊 BI & Analytics — ETL Alfa Construtora

> Plataforma de Business Intelligence para consolidação e análise de despesas financeiras, execução de obras e operação de RH de uma construtora. Pipeline ETL completo + dashboard interativo com Dash.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Dash](https://img.shields.io/badge/Dash-2.18-008DE4?logo=plotly&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-3.x-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-6.x-3F4F75?logo=plotly&logoColor=white)
![Status](https://img.shields.io/badge/Status-Produção-success)

---

## 🎯 Sobre o Projeto

Desenvolvido para automatizar a **consolidação e visualização de relatórios mensais** armazenados em planilhas Excel. O pipeline realiza o processo completo de **ETL (Extract, Transform, Load)**, transformando dados brutos de múltiplas fontes em um dashboard analítico interativo com três módulos integrados.

> ⚠️ **Aviso de privacidade:** Os dados reais da empresa são confidenciais e **não estão incluídos** neste repositório. Para rodar o projeto, forneça suas próprias planilhas seguindo a estrutura descrita abaixo.

---

## ✨ Funcionalidades

### Módulo Financeiro
| Funcionalidade | Descrição |
|---|---|
| 📥 **ETL Multi-abas** | Consolida automaticamente todas as abas mensais do Excel financeiro |
| 🎛️ **Filtros interativos** | Filtragem por Mês, Departamento, Status, Pontualidade e horizonte de pagamentos futuros |
| 📈 **KPIs em tempo real** | Total de despesas, total pago, em aberto e em atraso |
| 📊 **Análise de Pareto** | Identifica quais despesas concentram 80% do custo |
| ⏱️ **Aging de pagamentos** | Classifica pagamentos em faixas: Antecipado, No prazo, Atraso até 30d, Atraso >30d |
| 🏦 **Gasto por recebedor** | Stacked bar por Fonte de pagamento com breakdown PAGO/EM ABERTO |
| 📅 **Pagamentos futuros** | Visualiza vencimentos em aberto nos próximos 7, 30 ou 90 dias |
| 🖱️ **Filtro por clique** | Clique em qualquer barra para filtrar todos os gráficos relacionados |

### Módulo Obras
| Funcionalidade | Descrição |
|---|---|
| 🏗️ **Visão geral consolidada** | KPIs e distribuição de m² entre todos os tipos de serviço |
| 🧱 **Piso Intertravado** | Top 10 endereços, histograma de tamanhos, scatter dimensional com outliers |
| 🪨 **Pisos Especiais** | Consumo por logradouro e perfil de trechos padrão vs. atípicos |
| 🚰 **Ligações de Esgoto** | Funil de conclusão técnica (Concluída → Parcial → Pendente) |
| 🧱 **Calçada em Concreto** | Produção por bairro, top 8 ruas, scatter dimensional |

### Módulo RH
| Funcionalidade | Descrição |
|---|---|
| 👷 **Adiantamentos** | Total, ticket médio e distribuição por função |
| 🔒 **Privacidade** | Dados bancários removidos automaticamente no ETL |

---

## 🗂️ Arquitetura do Projeto

```
ETL-ALFA-CONSTRUTORA/
│
├── dash_app.py          # Dashboard principal (Dash) ← ENTRADA PRINCIPAL
├── data_transformer.py  # ETL: leitura, limpeza e normalização de todos os Excel
│
├── assets/
│   └── alfa.css         # Tema dark customizado, pills, cards, grid responsivo
│
├── data/                # Planilhas Excel (não versionadas)
│   ├── FINANCEIRO_ALFA.xlsx
│   ├── MEDIÇÃO GERAL 8 - MARQUISE (PISO INTERTRAVADO).xlsx
│   ├── MEDIÇÃO 08 - MARQUISE (CONCRETO).xlsx
│   ├── MEDIÇÃO GERAL 8 - JUNHO - (PISOS ESPECIAIS).xlsx
│   ├── PLANILHA GERAL - ADIANTAMENTO.xlsx
│   └── MEDIÇÃO GERAL 8 - JUNHO - PLANILHA GERAL.xlsx
│
├── app.py               # Dashboard legado (Streamlit) — mantido para referência
├── pipeline.py          # Protótipo inicial Streamlit — mantido para referência
│
├── .env                 # Variável DATA_FILE (não versionado)
├── .env.example         # Modelo do .env
├── requirements.txt     # Dependências do projeto
└── README.md
```

---

## 🛠️ Tecnologias

| Biblioteca | Versão | Uso |
|---|---|---|
| **Python** | 3.10+ | Linguagem principal |
| **Dash** | 2.18 | Framework do dashboard |
| **dash-bootstrap-components** | 1.6 | Layout e componentes UI |
| **Plotly** | 6.x | Visualizações interativas |
| **Pandas** | 3.x | ETL e transformação de dados |
| **Openpyxl** | 3.x | Leitura de arquivos Excel |
| **python-dotenv** | 1.x | Variáveis de ambiente |

---

## 🗂️ Estrutura Esperada das Planilhas

### `FINANCEIRO_ALFA.xlsx`
Uma aba por mês (`JAN-2026`, `FEV`, `MARÇO`...). Dados a partir da **5ª linha**, colunas na ordem:

| Coluna | Descrição |
|---|---|
| `Despesa` | Nome/descrição da despesa |
| `Departamento` | Departamento responsável |
| `Valor` | Valor em R$ |
| `Parcela` | Ex: `1/3` |
| `Vencimento` | Data de vencimento |
| `Data_Pagamento` | Data em que foi efetivamente pago |
| `Fonte` | Banco ou meio de pagamento (recebedor) |
| `Status` | `PAGO` ou `EM ABERTO` |
| `Obs` | Observações livres |

> A aba `Planilha1` é ignorada automaticamente.

### Medições de Obra (`.xlsx`)
Cada arquivo de medição deve conter, a partir da **4ª linha**:
`Bairro`, `Rua`, `Número`, `Comprimento`, `Largura`, `Area_m2`
O arquivo de Piso Intertravado inclui uma coluna `Data` como primeira coluna.

### `PLANILHA GERAL - ADIANTAMENTO.xlsx`
A partir da **4ª linha**: `Nome`, `Função`, `Dados_bancários` *(removido no ETL)*, `Valor`.

---

## ⚙️ Como Executar

**1. Clone o repositório**
```bash
git clone https://github.com/seu-usuario/etl-alfa-construtora.git
cd etl-alfa-construtora
```

**2. Crie e ative o ambiente virtual**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Configure o `.env`**
```bash
cp .env.example .env
```
```env
DATA_FILE=FINANCEIRO_ALFA.xlsx
```

**5. Coloque os arquivos Excel na pasta `data/`**

Consulte a seção *Estrutura Esperada das Planilhas* acima para os nomes e formatos corretos.

**6. Inicie o dashboard**
```bash
python dash_app.py
```

Acesse **http://127.0.0.1:8050** no navegador.

---

## 🖱️ Como Usar o Dashboard

- **Filtros por pill** — clique nas pills de Mês, Departamento, Status, Pontualidade e Pagamentos Futuros para filtrar os gráficos do módulo Financeiro
- **Filtro por clique no gráfico** — clique em qualquer barra para aplicar aquele valor como filtro cruzado; o indicador na toolbar mostra os filtros ativos
- **Limpar filtros dos gráficos** — botão na toolbar remove todos os filtros aplicados por clique
- **Troca de módulo** — tabs no topo alternam entre Financeiro, Obras e RH
- **Serviços da obra** — radio buttons selecionam qual tipo de serviço detalhar

---

## 📌 Observações Técnicas

- O `data_transformer.py` é independente do dashboard — pode ser importado em outros scripts ou notebooks
- Todos os dados são carregados uma única vez no startup e mantidos em memória; nenhum arquivo de origem é modificado
- Valores não numéricos na coluna `Valor` são convertidos com `errors="coerce"` e preenchidos com `0.0`
- Datas inválidas resultam em `NaT` e não afetam o cálculo de aging
- O aging é calculado como `Data_Pagamento - Vencimento` em dias (negativo = antecipado)
- O campo `Dados_bancários` da planilha de adiantamentos é descartado no ETL e nunca exposto no dashboard

---

## 👨‍💻 Autor

Desenvolvido por **Matheus** — [LinkedIn](https://linkedin.com/in/seu-perfil) · [GitHub](https://github.com/seu-usuario)
