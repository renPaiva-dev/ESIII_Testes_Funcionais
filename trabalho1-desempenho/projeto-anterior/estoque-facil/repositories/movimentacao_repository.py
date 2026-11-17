"""Acesso à tabela movimentacoes."""
from models import Movimentacao


class MovimentacaoRepository:
    def __init__(self, con):
        self.con = con

    def inserir(self, produto_id, tipo, quantidade, saldo_apos, usuario, observacao, criado_em):
        """Grava a movimentação. Observação vazia é guardada como NULL."""
        return self.con.execute(
            "INSERT INTO movimentacoes (produto_id, tipo, quantidade, saldo_apos, usuario, observacao, criado_em) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (produto_id, tipo, quantidade, saldo_apos, usuario, observacao or None, criado_em)).lastrowid

    def listar_por_produto(self, produto_id, limite=50):
        """Mais recentes primeiro (RN14)."""
        rows = self.con.execute(
            "SELECT * FROM movimentacoes WHERE produto_id = ? ORDER BY id DESC LIMIT ?",
            (produto_id, limite)).fetchall()
        return [Movimentacao(**dict(r)) for r in rows]

    def totais_por_tipo(self):
        """{'entrada': {'movimentacoes': n, 'unidades': u}, 'saida': {...}}"""
        totais = {t: {"movimentacoes": 0, "unidades": 0} for t in ("entrada", "saida")}
        for row in self.con.execute(
                "SELECT tipo, COUNT(*) AS n, SUM(quantidade) AS u FROM movimentacoes GROUP BY tipo"):
            totais[row["tipo"]] = {"movimentacoes": row["n"], "unidades": row["u"]}
        return totais

    def mais_saidas(self, limite=5):
        """Produtos com mais unidades de saída."""
        rows = self.con.execute(
            "SELECT p.sku, p.nome, SUM(m.quantidade) AS unidades FROM movimentacoes m "
            "JOIN produtos p ON p.id = m.produto_id WHERE m.tipo = 'saida' "
            "GROUP BY p.id ORDER BY unidades DESC, p.nome LIMIT ?", (limite,)).fetchall()
        return [dict(r) for r in rows]
