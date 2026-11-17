"""Entidade Produto e a regra de situação do estoque (RN11)."""
from dataclasses import dataclass

TEXTO_SITUACAO = {"sem_estoque": "Sem estoque", "baixo": "Estoque baixo", "normal": "Normal"}


@dataclass
class Produto:
    id: int
    sku: str
    nome: str
    preco: float
    quantidade: int
    estoque_minimo: int
    criado_em: str

    @property
    def situacao(self):
        """RN11: Sem estoque (0) > Estoque baixo (quantidade <= mínimo) > Normal."""
        if self.quantidade == 0:
            return "sem_estoque"
        if self.quantidade <= self.estoque_minimo:
            return "baixo"
        return "normal"

    def to_dict(self):
        """Formato devolvido pela API (inclui o campo calculado 'situacao')."""
        return {
            "id": self.id,
            "sku": self.sku,
            "nome": self.nome,
            "preco": self.preco,
            "quantidade": self.quantidade,
            "estoque_minimo": self.estoque_minimo,
            "criado_em": self.criado_em,
            "situacao": self.situacao,
        }
