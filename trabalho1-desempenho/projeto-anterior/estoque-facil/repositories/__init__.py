"""Camada REPOSITORIES: único lugar com SQL.

Cada repository recebe uma conexão já aberta (dentro ou fora de transação, quem decide
é o service) e converte linhas do banco em objetos de models.
"""
from repositories.movimentacao_repository import MovimentacaoRepository
from repositories.produto_repository import ProdutoRepository
from repositories.usuario_repository import UsuarioRepository

__all__ = ["MovimentacaoRepository", "ProdutoRepository", "UsuarioRepository"]
