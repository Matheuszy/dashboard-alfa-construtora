import sys
from pathlib import Path

# Adiciona a pasta src diretamente ao caminho do Python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
import mongomock
from werkzeug.security import generate_password_hash, check_password_hash
from dash_app import brl

@pytest.fixture
def mock_db():
    """Cria um banco de dados falso na memória para os testes."""
    client = mongomock.MongoClient()
    return client.db.usuarios

def test_criptografia_de_senha():
    """Garante que a biblioteca de criptografia do Flask está operante."""
    senha_plana = "minha_senha_123"
    hash_senha = generate_password_hash(senha_plana)
    
    # O hash nunca pode ser igual à senha plana
    assert hash_senha != senha_plana
    # A verificação deve bater
    assert check_password_hash(hash_senha, senha_plana) is True

def test_criacao_usuario_root(mock_db):
    """Simula a criação do usuário Root no banco de dados Mockado."""
    # Simula a lógica que fizemos no dash_app.py
    mock_db.insert_one({
        "username": "root_test",
        "password_hash": generate_password_hash("senha_root"),
        "role": "root"
    })
    
    # Verifica se salvou corretamente
    user_salvo = mock_db.find_one({"username": "root_test"})
    assert user_salvo is not None
    assert user_salvo["role"] == "root"
    assert check_password_hash(user_salvo["password_hash"], "senha_root") is True