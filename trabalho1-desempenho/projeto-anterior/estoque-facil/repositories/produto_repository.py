"""Acesso à tabela produtos."""
from models import Produto


def _para_produto(row):
    return Produto(**dict(row)) if row else None


def _filtro(q, somente_baixo):
    """Monta o WHERE da busca (nome ou SKU, sem diferenciar maiúsculas) e do filtro de baixa."""
    filtros, params = [], []
    if q:
        # Escapa os curingas do LIKE para buscar "%" e "_" literalmente.
        termo = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        filtros.append("(nome LIKE ? ESCAPE '\\' OR sku LIKE ? ESCAPE '\\')")
        params += [termo, termo]
    if somente_baixo:
        filtros.append("quantidade <= estoque_minimo")
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    return where, params


class ProdutoRepository:
    def __init__(self, con):
        self.con = con

    # ------------------------------------------------------------------ consultas
    def contar(self, q="", somente_baixo=False):
        where, params = _filtro(q, somente_baixo)
        return self.con.execute(f"SELECT COUNT(*) FROM produtos {where}", params).fetchone()[0]

    def buscar(self, q="", somente_baixo=False, limite=20, deslocamento=0):
        """Ordem alfabética por nome (desempate pelo id)."""
        where, params = _filtro(q, somente_baixo)
        rows = self.con.execute(
            f"SELECT * FROM produtos {where} ORDER BY nome COLLATE NOCASE, id LIMIT ? OFFSET ?",
            params + [limite, deslocamento]).fetchall()
        return [_para_produto(r) for r in rows]

    def buscar_por_id(self, pid):
        return _para_produto(self.con.execute("SELECT * FROM produtos WHERE id = ?", (pid,)).fetchone())

    def existe_sku(self, sku):
        return self.con.execute("SELECT 1 FROM produtos WHERE sku = ?", (sku,)).fetchone() is not None

    def saldo(self, pid):
        row = self.con.execute("SELECT quantidade FROM produtos WHERE id = ?", (pid,)).fetchone()
        return row["quantidade"] if row else None

    def listar_em_baixa(self):
        rows = self.con.execute("SELECT * FROM produtos WHERE quantidade <= estoque_minimo "
                                "ORDER BY quantidade, nome COLLATE NOCASE").fetchall()
        return [_para_produto(r) for r in rows]

    def resumo(self):
        """Totais para o relatório: produtos, unidades, valor e quantos estão em baixa."""
        return self.con.execute(
            "SELECT COUNT(*) AS produtos, COALESCE(SUM(quantidade), 0) AS unidades, "
            "COALESCE(SUM(quantidade * preco), 0) AS valor, "
            "COALESCE(SUM(CASE WHEN quantidade <= estoque_minimo THEN 1 ELSE 0 END), 0) AS em_baixa "
            "FROM produtos").fetchone()

    # ------------------------------------------------------------------ alterações
    def inserir(self, sku, nome, preco, quantidade, estoque_minimo, criado_em):
        return self.con.execute(
            "INSERT INTO produtos (sku, nome, preco, quantidade, estoque_minimo, criado_em) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (sku, nome, preco, quantidade, estoque_minimo, criado_em)).lastrowid

    def atualizar(self, pid, nome, preco, estoque_minimo):
        """Retorna True se o produto existia."""
        cur = self.con.execute("UPDATE produtos SET nome = ?, preco = ?, estoque_minimo = ? WHERE id = ?",
                               (nome, preco, estoque_minimo, pid))
        return cur.rowcount > 0

    def excluir(self, pid):
        self.con.execute("DELETE FROM produtos WHERE id = ?", (pid,))  # histórico sai junto (CASCADE)

    def creditar(self, pid, quantidade):
        self.con.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?", (quantidade, pid))

    def debitar_se_houver_saldo(self, pid, quantidade):
        """Atualização condicional: o saldo nunca fica negativo, mesmo com acessos simultâneos.

        Retorna False (e não altera nada) quando o saldo não é suficiente.
        """
        cur = self.con.execute("UPDATE produtos SET quantidade = quantidade - ? "
                               "WHERE id = ? AND quantidade >= ?", (quantidade, pid, quantidade))
        return cur.rowcount > 0
