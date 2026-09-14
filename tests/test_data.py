import sys
from pathlib import Path

# Adiciona a pasta src diretamente ao caminho do Python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
import pandas as pd
from data_transformer import to_number, robust_find_header
from dash_app import brl

def test_conversao_moeda_brl():
    """Garante que a formatação visual de moeda está correta."""
    assert brl(1234.56) == "R$ 1.234,56"
    assert brl(0.0) == "R$ 0,00"

def test_to_number_limpeza_extrema():
    """Testa se a função de limpeza lida com a bagunça do Excel humano."""
    assert to_number("1.234,56") == 1234.56
    assert to_number("R$ 500.00") == 500.0
    assert to_number("-") == 0.0
    assert to_number(None) == 0.0
    assert to_number("texto_invalido") == 0.0

def test_robust_find_header():
    """Garante que a função acha o cabeçalho mesmo se ele mudar de linha."""
    dados_simulados = pd.DataFrame([
        ["Empresa Alfa", None, None],
        ["Relatório V2", None, None],
        ["Data", "Despesa", "Valor"], # O cabeçalho real está na linha 2 (índice 2)
        ["01/01", "Cimento", "100"]
    ])
    
    idx = robust_find_header(dados_simulados, ["Despesa", "Valor"])
    assert idx == 2