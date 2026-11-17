"""Resultado paginado de uma busca de produtos (RN13: 20 por página)."""
from dataclasses import dataclass, field
from typing import List

from models.produto import Produto


@dataclass
class Pagina:
    total: int
    pagina: int
    paginas: int
    itens: List[Produto] = field(default_factory=list)

    def to_dict(self):
        return {"total": self.total, "pagina": self.pagina, "paginas": self.paginas,
                "itens": [p.to_dict() for p in self.itens]}
