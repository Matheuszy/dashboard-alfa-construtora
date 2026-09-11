# 📊 Dashboard Financeiro — ETL Alfa Construtora

> Painel gerencial interativo para consolidação e análise de despesas corporativas, desenvolvido como solução de Business Intelligence para o setor financeiro de uma construtora.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-ETL-150458?logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interativo-3F4F75?logo=plotly&logoColor=white)
![Status](https://img.shields.io/badge/Status-Produção-success)

---

## 🎯 Sobre o Projeto

Este projeto foi desenvolvido para automatizar a **consolidação e visualização de relatórios financeiros mensais** armazenados em planilhas Excel. O pipeline realiza o processo completo de **ETL (Extract, Transform, Load)**, transformando dados brutos em um dashboard analítico interativo.

> ⚠️ **Aviso de privacidade:** Os dados reais da empresa são confidenciais e **não estão incluídos** neste repositório. Para rodar o projeto localmente, utilize o arquivo de exemplo disponibilizado (`sample_data.xlsx`) ou forneça sua própria planilha seguindo a estrutura descrita abaixo.

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 📥 **ETL Multi-abas** | Leitura e consolidação automática de múltiplas abas mensais do Excel |
| 🎛️ **Filtros Dinâmicos** | Filtragem cruzada por Mês, Departamento e Status de Pagamento |
| 📈 **KPIs em Tempo Real** | Total de Despesas, Total Pago e Média por Despesa |
| 📊 **Gráficos Interativos** | Barras, rosca, linha cronológica e análise por fonte |
| 🎨 **Layout Customizado** | Modo escuro com identidade visual corporativa |

---

## 🛠️ Tecnologias Utilizadas

- **Python** — linguagem principal
- **Pandas** — tratamento e transformação de dados (ETL)
- **Streamlit** — interface web e dashboard
- **Plotly** — visualizações interativas
- **Openpyxl** — leitura de arquivos Excel
- **Python-dotenv** — gerenciamento de variáveis de ambiente

---

## 📁 Estrutura do Projeto

```
ETL-ALFA-CONSTRUTORA/
│
├── app.py                  # Dashboard principal (multi-mês)
├── pipeline.py             # Versão simplificada (single-mês)
├── sample_data.xlsx        # ✅ Arquivo de exemplo com dados fictícios
├── .env                    # Variável DATA_FILE (não versionado)
├── .env.example            # Modelo do .env para novos usuários
├── requirements.txt        # Dependências do projeto
└── README.md
```

---

## 🗂️ Estrutura Esperada da Planilha

O arquivo Excel deve conter **uma aba por mês** (ex: `JAN-2026`, `FEV`, `MARÇO`...), com dados a partir da **4ª linha** e as seguintes colunas na ordem:

| Coluna | Descrição |
|---|---|
| `Despesa` | Nome/descrição da despesa |
| `Departamento` | Departamento responsável |
| `Valor` | Valor em R$ |
| `Parcela` | Ex: `1/3` |
| `Vencimento` | Data de vencimento |
| `Data_Pagamento` | Data em que foi pago |
| `Fonte` | Banco ou meio de pagamento |
| `Status` | `PAGO` ou `EM ABERTO` |
| `Obs` | Observações livres |

> O arquivo `sample_data.xlsx` já segue essa estrutura e pode ser usado como ponto de partida.

---

## ⚙️ Como Executar Localmente

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

**4. Configure o arquivo `.env`**

Copie o arquivo de exemplo e ajuste o nome da planilha:
```bash
cp .env.example .env
```

Conteúdo do `.env`:
```env
DATA_FILE=sample_data.xlsx
```

> Substitua `sample_data.xlsx` pelo caminho da sua planilha real caso queira usar dados próprios.

**5. Execute o dashboard**
```bash
streamlit run app.py
```

### Alternativa Dash: painel integrado dos Excel

O arquivo `dash_app.py` lê automaticamente os arquivos da pasta `data/`, normaliza as planilhas financeiras, as medições de obra e os adiantamentos da operação de RH. Ele preserva os arquivos de origem e gera os insights diretamente em memória.

```bash
python dash_app.py
```

Abra `http://127.0.0.1:8050`. O painel Dash oferece filtros cruzados e indicadores de despesas, inadimplência, execução por serviço e bairro, trechos atípicos e adiantamentos por função. Clique em barras e pontos para filtrar os gráficos relacionados; use o botão de limpeza para remover esses filtros.

---

## 📌 Observações

- A aba `Planilha1` é ignorada automaticamente no carregamento — use-a como índice ou sumário se necessário.
- Valores não numéricos na coluna `Valor` são descartados com `coerce`.
- Datas inválidas são exibidas como `Não informado` ou `Pendente`.

---

## 👨‍💻 Autor

Desenvolvido por **Matheus** — [LinkedIn](https://linkedin.com/in/seu-perfil) · [GitHub](https://github.com/seu-usuario)
