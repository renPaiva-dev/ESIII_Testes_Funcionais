"""Entidade Movimentacao (entrada ou saída de estoque, RN09/RN14)."""
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class Movimentacao:
    id: int
    produto_id: int
    tipo: str            # "entrada" ou "saida"
    quantidade: int
    saldo_apos: int
    usuario: str
    observacao: Optional[str]
    criado_em: str

    def to_dict(self):
        return asdict(self)
