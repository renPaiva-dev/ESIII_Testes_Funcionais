"""Configuração lida das variáveis de ambiente."""
import os
from pathlib import Path

BASE = Path(__file__).parent


def carregar():
    return {
        "SECRET_KEY": os.getenv("ESTOQUE_SECRET", "estoque-facil-dev"),
        "DATABASE": os.getenv("ESTOQUE_DB", str(BASE / "dados" / "estoque.db")),
        "SEED_PRODUTOS": int(os.getenv("SEED_PRODUTOS", "30")),
        "PERMITIR_RESET": os.getenv("PERMITIR_RESET", "1") == "1",
    }


def porta():
    return int(os.getenv("PORTA", "5001"))
