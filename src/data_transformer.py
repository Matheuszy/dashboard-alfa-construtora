# -*- coding: utf-8 -*-
"""ETL dos arquivos Excel usados nos paineis da Alfa Construtora.
Refatorado para ser mais robusto, buscando colunas por similaridade ao inves de linhas hardcoded,
evitando erros caso as planilhas da operacao e de RH sofram pequenas alteracoes de layout.
"""
from __future__ import annotations
from pathlib import Path
import re
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def to_number(value: object) -> float:
    if pd.isna(value): return 0.0
    text = str(value).strip()
    if not text or text == "-": return 0.0
    text = re.sub(r"[^0-9,.-]", "", text)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    return pd.to_numeric(text, errors="coerce") if text else 0.0

def _text_column(series: pd.Series, default: str = "Nao informado") -> pd.Series:
    return series.fillna(default).astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

def robust_find_header(df: pd.DataFrame, expected_keywords: list[str], max_rows: int = 15) -> int:
    """Procura a linha do cabecalho com base em palavras-chave esperadas para evitar dependencias de linha fixa."""
    for i in range(min(max_rows, len(df))):
        # Conversão nativa forçada: transforma qualquer dado (incluindo NaN) em string e minúsculo
        row_values = [str(val).lower() for val in df.iloc[i].tolist()]
        
        matches = sum(1 for kw in expected_keywords if any(kw.lower() in rv for rv in row_values))
        if matches >= len(expected_keywords) / 2:  # Encontrou pelo menos metade das colunas esperadas
            return i
    return 3 # Fallback padrao

def load_financial(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    path = data_dir / "FINANCEIRO_ALFA.xlsx"
    columns = ["Despesa", "Departamento", "Valor", "Parcela", "Vencimento", "Data_Pagamento", "Fonte", "Status", "Obs"]
    if not path.exists(): return pd.DataFrame(columns=columns + ["Mes", "Aging_dias"])
    
    tables = []
    try:
        xls = pd.ExcelFile(path)
        for sheet_name in xls.sheet_names:
            if sheet_name.lower() == "planilha1": continue
            raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
            header_idx = robust_find_header(raw, ["Despesa", "Departamento", "Valor"])
            if len(raw) <= header_idx + 1: continue
            
            frame = raw.iloc[header_idx + 1:, : len(columns)].copy()
            frame.columns = columns
            frame = frame.dropna(how="all").dropna(subset=["Despesa"])
            frame["Mes"] = sheet_name
            tables.append(frame)
    except Exception as e:
        print(f"Erro processando financeiro: {e}")

    if not tables: return pd.DataFrame(columns=columns + ["Mes", "Aging_dias"])
    
    df = pd.concat(tables, ignore_index=True)
    df["Valor"] = df["Valor"].map(to_number).fillna(0.0)
    for col, default in [("Departamento", "Nao informado"), ("Fonte", "Nao informado"), ("Status", "EM ABERTO")]:
        df[col] = _text_column(df[col], default)
    df["Status"] = df["Status"].str.upper().replace({"NAN": "EM ABERTO", "NONE": "EM ABERTO", "": "EM ABERTO"})
    df["Despesa"] = _text_column(df["Despesa"])
    df["Vencimento"]     = pd.to_datetime(df["Vencimento"],     errors="coerce")
    df["Data_Pagamento"] = pd.to_datetime(df["Data_Pagamento"], errors="coerce")
    df["Aging_dias"]     = (df["Data_Pagamento"] - df["Vencimento"]).dt.days
    df["Pago"]           = df["Status"].eq("PAGO")
    return df

def _load_measurement(path: Path, service: str, has_date: bool) -> pd.DataFrame:
    base_columns = ["Data", "Bairro", "Rua", "Numero", "Comprimento", "Largura", "Area_m2"]
    if not path.exists(): return pd.DataFrame(columns=base_columns + ["Servico"])
    
    raw = pd.read_excel(path, header=None)
    header_idx = robust_find_header(raw, ["Bairro", "Rua", "Area", "Comprimento"])
    
    if has_date:
        frame = raw.iloc[header_idx + 1:, :7].copy()
        frame.columns = base_columns
    else:
        frame = raw.iloc[header_idx + 1:, :6].copy()
        frame.columns = base_columns[1:]
        frame.insert(0, "Data", pd.NaT)
        
    frame = frame.dropna(how="all")
    for col in ["Bairro", "Rua", "Numero"]: frame[col] = _text_column(frame[col], "")
    for col in ["Comprimento", "Largura", "Area_m2"]: frame[col] = frame[col].map(to_number).fillna(0.0)
    frame["Data"]    = pd.to_datetime(frame["Data"], errors="coerce")
    frame["Servico"] = service
    return frame[(frame["Rua"] != "") & (frame["Area_m2"] > 0)].reset_index(drop=True)

def load_work_measurements(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    mappings = [
        ("MEDICAO GERAL 8 - MARQUISE (PISO INTERTRAVADO).xlsx",  "Piso intertravado",   True),
        ("MEDICAO 08 - MARQUISE (CONCRETO).xlsx",                 "Calcada em concreto", False),
        ("MEDIÇÃO GERAL 8 - MARQUISE (PISO INTERTRAVADO).xlsx",  "Piso intertravado",   True),
        ("MEDIÇÃO 08 - MARQUISE (CONCRETO).xlsx",                 "Calcada em concreto", False),
    ]
    frames = []
    for fn, svc, hd in mappings:
        p = data_dir / fn
        if p.exists(): frames.append(_load_measurement(p, svc, hd))

    for fname in ["MEDICAO GERAL 8 - JUNHO - (PISOS ESPECIAIS).xlsx", "MEDIÇÃO GERAL 8 - JUNHO - (PISOS ESPECIAIS).xlsx"]:
        path = data_dir / fname
        if path.exists():
            try:
                xls = pd.ExcelFile(path)
                sname = "Table 5" if "Table 5" in xls.sheet_names else xls.sheet_names[0]
                raw  = pd.read_excel(path, sheet_name=sname, header=None)
                header_idx = robust_find_header(raw, ["Bairro", "Rua", "Area"])
                
                special = raw.iloc[header_idx + 1:, :8].copy()
                special.columns = ["Data", "Bairro", "Rua", "Numero", "Complemento", "Unidade", "Area_m2", "Area_Marquise"]
                special = special.dropna(how="all")
                special["Area_m2"] = special["Area_m2"].map(to_number).fillna(0.0)
                special["Data"]    = pd.to_datetime(special["Data"], errors="coerce")
                for col in ["Bairro", "Rua", "Numero"]: special[col] = _text_column(special[col], "")
                special["Servico"]     = "Pisos especiais"
                special["Comprimento"] = 0.0
                special["Largura"]     = 0.0
                frames.append(special[["Data", "Bairro", "Rua", "Numero", "Comprimento", "Largura", "Area_m2", "Servico"]].query("Area_m2 > 0 and Rua != ''"))
            except Exception as e:
                pass
            break
            
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def load_advances(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Le a folha de adiantamentos identificando a Obra e o Administrativo pelos sub-cabecalhos."""
    import re
    for fname in ["PLANILHA GERAL - ADIANTAMENTO.xlsx", "PLANILHA GERAL - ADIANTAMENTO_2.xlsx"]:
        path = data_dir / fname
        if path.exists():
            try:
                raw = pd.read_excel(path, header=None)
                parsed_data = []
                current_obra = "Geral"
                
                for idx, row in raw.iterrows():
                    col0 = str(row[0]).strip()
                    
                    # NOVA REGRA: Detecta a mudança de Obra ou Setor Administrativo
                    if "DADOS DE PAGAMENTO" in col0.upper() or "OBRA" in col0.upper() or "ADMINISTRATIVO" in col0.upper():
                        match = re.search(r'\((.*?)\)', col0)
                        if match:
                            sector = match.group(1).strip().upper()
                            if sector.startswith("OBRA "):
                                current_obra = sector.replace("OBRA ", "").strip()
                            else:
                                current_obra = sector
                        continue
                        
                    # Ignora cabeçalhos internos, totais ou linhas vazias
                    if (col0.lower() == "nan" or 
                        col0.upper() == "NOME" or 
                        "TOTAL" in col0.upper() or 
                        col0.upper().startswith("ALFA")):
                        continue
                        
                    nome = col0
                    funcao = str(row[1]).strip()
                    valor = row[3]
                    
                    try:
                        if isinstance(valor, str):
                            valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
                        valor = float(valor)
                        if pd.isna(valor) or valor <= 0:
                            continue
                    except:
                        continue
                        
                    if nome and nome.lower() != "nan":
                        parsed_data.append({
                            "Obra": current_obra.title(), # Retorna 'Administrativo', 'Marquise', etc.
                            "Nome": _text_column(pd.Series([nome]), "")[0],
                            "Funcao": _text_column(pd.Series([funcao]), "Nao informado")[0],
                            "Valor": valor
                        })
                        
                df = pd.DataFrame(parsed_data)
                if not df.empty:
                    return df
            except Exception as e:
                print(f"Erro lendo RH: {e}")
                
    return pd.DataFrame(columns=["Obra", "Nome", "Funcao", "Valor"])

def load_contract_measurement(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    columns = ["Item", "Descricao", "Unidade", "Preco_unitario", "Qtd_atual", "Valor_atual"]
    for fname in ["MEDIÇÃO GERAL 8 - JUNHO - PLANILHA GERAL.xlsx", "MEDICAO GERAL 8 - JUNHO - PLANILHA GERAL.xlsx"]:
        path = data_dir / fname
        if path.exists():
            try:
                raw = pd.read_excel(path, header=None)
                header_idx = robust_find_header(raw, ["Item", "Descricao", "Valor"])
                
                df = raw.iloc[header_idx + 1:, [0, 1, 2, 3, 10, 16]].copy()
                df.columns = columns
                df = df[df["Item"].astype(str).str.match(r"^\d+(\.\d+)?$", na=False)].copy()
                for col in ["Preco_unitario", "Qtd_atual", "Valor_atual"]:
                    df[col] = df[col].map(to_number).fillna(0.0)
                df["Descricao"] = _text_column(df["Descricao"], "")
                df["Unidade"]   = _text_column(df["Unidade"],   "")
                return df.reset_index(drop=True)
            except Exception as e:
                pass
    return pd.DataFrame(columns=columns)

def load_all(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    return {
        "financeiro":    load_financial(data_dir),
        "obras":         load_work_measurements(data_dir),
        "adiantamentos": load_advances(data_dir),
        "medicao_geral": load_contract_measurement(data_dir),
    }