"""Camada SERVICES: regras de negócio (RN01 a RN14) e controle de transação.

Não conhece HTTP nem HTML (isso é dos controllers) e não escreve SQL (isso é dos
repositories). É usada igualmente pelas telas e pela API, então as duas seguem as
mesmas regras e mensagens.
"""
from services.autenticacao_service import AutenticacaoService
from services.movimentacao_service import MovimentacaoService
from services.produto_service import ProdutoService
from services.relatorio_service import RelatorioService

__all__ = ["AutenticacaoService", "MovimentacaoService", "ProdutoService", "RelatorioService"]
