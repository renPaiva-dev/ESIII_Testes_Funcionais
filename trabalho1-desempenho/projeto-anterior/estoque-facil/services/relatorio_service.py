"""Relatório do estoque."""
from database.conexao import get_db
from repositories import MovimentacaoRepository, ProdutoRepository


class RelatorioService:
    def gerar(self):
        """Resumo do estoque. Percorre TODOS os produtos e TODAS as movimentações,
        por isso fica mais lento conforme o histórico cresce."""
        con = get_db()
        produtos = ProdutoRepository(con)
        movimentacoes = MovimentacaoRepository(con)
        r = produtos.resumo()
        totais = movimentacoes.totais_por_tipo()
        return {
            "total_produtos": r["produtos"],
            "total_unidades": r["unidades"],
            "valor_total": round(r["valor"], 2),
            "produtos_em_baixa": r["em_baixa"],
            "entradas": totais["entrada"],
            "saidas": totais["saida"],
            "lista_em_baixa": [p.to_dict() for p in produtos.listar_em_baixa()],
            "mais_saidas": movimentacoes.mais_saidas(),
        }
