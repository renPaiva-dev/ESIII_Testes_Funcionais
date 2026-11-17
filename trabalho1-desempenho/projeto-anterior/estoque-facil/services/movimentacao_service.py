"""Regras de movimentação: entrada e saída (RN09, RN10) e histórico (RN14)."""
from database.conexao import agora, get_db, transacao
from models import ErroRegra, Movimentacao
from repositories import MovimentacaoRepository, ProdutoRepository
from services import validacoes
from services.produto_service import ProdutoService


class MovimentacaoService:
    def __init__(self, produtos=None):
        self.produtos = produtos or ProdutoService()

    def registrar(self, pid, dados, usuario):
        """Entrada soma e saída subtrai. Saída maior que o saldo é recusada e nada é gravado.

        Tudo acontece numa única transação: atualizar o saldo e gravar o histórico
        ou nenhum dos dois.
        """
        m = validacoes.validar_movimentacao(dados)
        with transacao() as con:
            produtos = ProdutoRepository(con)
            saldo_antes = produtos.saldo(pid)
            if saldo_antes is None:
                raise ErroRegra("Produto não encontrado.", 404)
            if m["tipo"] == "saida":
                if not produtos.debitar_se_houver_saldo(pid, m["quantidade"]):
                    raise ErroRegra(f"Estoque insuficiente. Saldo atual: {saldo_antes}.", 409)
            else:
                produtos.creditar(pid, m["quantidade"])
            saldo = produtos.saldo(pid)
            instante = agora()
            mid = MovimentacaoRepository(con).inserir(pid, m["tipo"], m["quantidade"], saldo,
                                                      usuario, m["observacao"], instante)
        return Movimentacao(id=mid, produto_id=pid, tipo=m["tipo"], quantidade=m["quantidade"],
                            saldo_apos=saldo, usuario=usuario, observacao=m["observacao"],
                            criado_em=instante)

    def historico(self, pid, limite=50):
        """As 50 movimentações mais recentes do produto (404 se ele não existir)."""
        self.produtos.obter(pid)
        return MovimentacaoRepository(get_db()).listar_por_produto(pid, limite)
