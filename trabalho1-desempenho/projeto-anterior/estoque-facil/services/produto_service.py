"""Regras de produto: busca (RN13), cadastro e edição (RN04 a RN08) e exclusão (RN12)."""
from database.conexao import agora, get_db, transacao
from models import ErroRegra, Pagina
from repositories import MovimentacaoRepository, ProdutoRepository
from services import validacoes

POR_PAGINA = 20


class ProdutoService:
    def listar(self, q="", somente_baixo=False, pagina=1):
        """Busca por nome ou SKU, 20 por página, ordem alfabética.

        Página fora do intervalo é ajustada para a primeira ou a última.
        """
        repo = ProdutoRepository(get_db())
        q = (q or "").strip()
        total = repo.contar(q, somente_baixo)
        paginas = max(1, -(-total // POR_PAGINA))          # divisão arredondando para cima
        pagina = min(max(1, pagina), paginas)
        itens = repo.buscar(q, somente_baixo, POR_PAGINA, (pagina - 1) * POR_PAGINA)
        return Pagina(total=total, pagina=pagina, paginas=paginas, itens=itens)

    def obter(self, pid):
        produto = ProdutoRepository(get_db()).buscar_por_id(pid)
        if not produto:
            raise ErroRegra("Produto não encontrado.", 404)
        return produto

    def criar(self, dados, usuario):
        """Cadastra o produto. Quantidade inicial > 0 gera a entrada "Saldo inicial" (RN08)."""
        d = validacoes.validar_produto(dados, novo=True)
        with transacao() as con:
            produtos = ProdutoRepository(con)
            if produtos.existe_sku(d["sku"]):
                raise ErroRegra("SKU já cadastrado.", 409)
            instante = agora()
            pid = produtos.inserir(d["sku"], d["nome"], d["preco"], d["quantidade"],
                                   d["estoque_minimo"], instante)
            if d["quantidade"] > 0:
                MovimentacaoRepository(con).inserir(pid, "entrada", d["quantidade"], d["quantidade"],
                                                    usuario, "Saldo inicial", instante)
        return self.obter(pid)

    def editar(self, pid, dados):
        """Altera nome, preço e estoque mínimo. SKU e saldo não mudam por aqui."""
        d = validacoes.validar_produto(dados, novo=False)
        with transacao() as con:
            if not ProdutoRepository(con).atualizar(pid, d["nome"], d["preco"], d["estoque_minimo"]):
                raise ErroRegra("Produto não encontrado.", 404)
        return self.obter(pid)

    def excluir(self, pid):
        """RN12: só exclui com saldo 0; o histórico do produto é removido junto."""
        with transacao() as con:
            produtos = ProdutoRepository(con)
            saldo = produtos.saldo(pid)
            if saldo is None:
                raise ErroRegra("Produto não encontrado.", 404)
            if saldo > 0:
                raise ErroRegra("Só é possível excluir produto com estoque zerado.", 409)
            produtos.excluir(pid)
