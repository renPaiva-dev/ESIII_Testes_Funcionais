"""Serviços de negócio do estoque. Usados tanto pelas telas (web.py) quanto pela API (api.py)."""
from werkzeug.security import check_password_hash

import db
import regras
from regras import ErroRegra

POR_PAGINA = 20
TEXTO_SITUACAO = {"sem_estoque": "Sem estoque", "baixo": "Estoque baixo", "normal": "Normal"}


def situacao(p):
    """Sem estoque (0) > Estoque baixo (quantidade <= mínimo) > Normal."""
    if p["quantidade"] == 0:
        return "sem_estoque"
    if p["quantidade"] <= p["estoque_minimo"]:
        return "baixo"
    return "normal"


def _produto(row):
    d = dict(row)
    d["situacao"] = situacao(d)
    return d


# --------------------------------------------------------------------------- usuários
def autenticar(login, senha):
    row = db.get_db().execute("SELECT * FROM usuarios WHERE login = ?", (login,)).fetchone()
    if row and check_password_hash(row["senha_hash"], senha):
        return dict(row)
    return None


# --------------------------------------------------------------------------- produtos
def listar(q="", somente_baixo=False, pagina=1):
    """Busca por nome ou SKU (sem diferenciar maiúsculas), 20 por página, ordem alfabética."""
    con = db.get_db()
    filtros, params = [], []
    q = (q or "").strip()
    if q:
        termo = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        filtros.append("(nome LIKE ? ESCAPE '\\' OR sku LIKE ? ESCAPE '\\')")
        params += [termo, termo]
    if somente_baixo:
        filtros.append("quantidade <= estoque_minimo")
    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

    total = con.execute(f"SELECT COUNT(*) FROM produtos {where}", params).fetchone()[0]
    paginas = max(1, -(-total // POR_PAGINA))
    pagina = min(max(1, pagina), paginas)
    rows = con.execute(
        f"SELECT * FROM produtos {where} ORDER BY nome COLLATE NOCASE, id LIMIT ? OFFSET ?",
        params + [POR_PAGINA, (pagina - 1) * POR_PAGINA]).fetchall()
    return {"total": total, "pagina": pagina, "paginas": paginas,
            "itens": [_produto(r) for r in rows]}


def obter(pid):
    row = db.get_db().execute("SELECT * FROM produtos WHERE id = ?", (pid,)).fetchone()
    if not row:
        raise ErroRegra("Produto não encontrado.", 404)
    return _produto(row)


def criar(dados, usuario):
    d = regras.validar_produto(dados, novo=True)
    with db.transacao() as con:
        if con.execute("SELECT 1 FROM produtos WHERE sku = ?", (d["sku"],)).fetchone():
            raise ErroRegra("SKU já cadastrado.", 409)
        instante = db.agora()
        pid = con.execute(
            "INSERT INTO produtos (sku, nome, preco, quantidade, estoque_minimo, criado_em) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (d["sku"], d["nome"], d["preco"], d["quantidade"], d["estoque_minimo"], instante)).lastrowid
        if d["quantidade"] > 0:
            con.execute(
                "INSERT INTO movimentacoes (produto_id, tipo, quantidade, saldo_apos, usuario, observacao, criado_em) "
                "VALUES (?, 'entrada', ?, ?, ?, 'Saldo inicial', ?)",
                (pid, d["quantidade"], d["quantidade"], usuario, instante))
    return obter(pid)


def editar(pid, dados):
    d = regras.validar_produto(dados, novo=False)
    with db.transacao() as con:
        cur = con.execute("UPDATE produtos SET nome = ?, preco = ?, estoque_minimo = ? WHERE id = ?",
                          (d["nome"], d["preco"], d["estoque_minimo"], pid))
        if cur.rowcount == 0:
            raise ErroRegra("Produto não encontrado.", 404)
    return obter(pid)


def excluir(pid):
    with db.transacao() as con:
        row = con.execute("SELECT quantidade FROM produtos WHERE id = ?", (pid,)).fetchone()
        if not row:
            raise ErroRegra("Produto não encontrado.", 404)
        if row["quantidade"] > 0:
            raise ErroRegra("Só é possível excluir produto com estoque zerado.", 409)
        con.execute("DELETE FROM produtos WHERE id = ?", (pid,))  # histórico sai junto (CASCADE)


# --------------------------------------------------------------------------- movimentações
def registrar_movimentacao(pid, dados, usuario):
    m = regras.validar_movimentacao(dados)
    with db.transacao() as con:
        row = con.execute("SELECT quantidade FROM produtos WHERE id = ?", (pid,)).fetchone()
        if not row:
            raise ErroRegra("Produto não encontrado.", 404)
        if m["tipo"] == "saida":
            # Atualização condicional: o saldo nunca fica negativo, mesmo com acessos simultâneos.
            cur = con.execute("UPDATE produtos SET quantidade = quantidade - ? "
                              "WHERE id = ? AND quantidade >= ?", (m["quantidade"], pid, m["quantidade"]))
            if cur.rowcount == 0:
                raise ErroRegra(f"Estoque insuficiente. Saldo atual: {row['quantidade']}.", 409)
        else:
            con.execute("UPDATE produtos SET quantidade = quantidade + ? WHERE id = ?", (m["quantidade"], pid))
        saldo = con.execute("SELECT quantidade FROM produtos WHERE id = ?", (pid,)).fetchone()[0]
        mid = con.execute(
            "INSERT INTO movimentacoes (produto_id, tipo, quantidade, saldo_apos, usuario, observacao, criado_em) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pid, m["tipo"], m["quantidade"], saldo, usuario, m["observacao"] or None, db.agora())).lastrowid
    return {"id": mid, "produto_id": pid, "tipo": m["tipo"], "quantidade": m["quantidade"],
            "saldo_apos": saldo, "usuario": usuario, "observacao": m["observacao"]}


def historico(pid, limite=50):
    obter(pid)  # 404 se não existir
    rows = db.get_db().execute(
        "SELECT * FROM movimentacoes WHERE produto_id = ? ORDER BY id DESC LIMIT ?", (pid, limite)).fetchall()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------- relatório
def relatorio():
    """Resumo do estoque. Percorre TODOS os produtos e TODAS as movimentações."""
    con = db.get_db()
    r = con.execute(
        "SELECT COUNT(*) AS produtos, COALESCE(SUM(quantidade), 0) AS unidades, "
        "COALESCE(SUM(quantidade * preco), 0) AS valor, "
        "COALESCE(SUM(CASE WHEN quantidade <= estoque_minimo THEN 1 ELSE 0 END), 0) AS em_baixa "
        "FROM produtos").fetchone()
    mov = {t: {"movimentacoes": 0, "unidades": 0} for t in ("entrada", "saida")}
    for row in con.execute("SELECT tipo, COUNT(*) AS n, SUM(quantidade) AS u FROM movimentacoes GROUP BY tipo"):
        mov[row["tipo"]] = {"movimentacoes": row["n"], "unidades": row["u"]}
    baixa = con.execute("SELECT * FROM produtos WHERE quantidade <= estoque_minimo "
                        "ORDER BY quantidade, nome COLLATE NOCASE").fetchall()
    mais_saidas = con.execute(
        "SELECT p.sku, p.nome, SUM(m.quantidade) AS unidades FROM movimentacoes m "
        "JOIN produtos p ON p.id = m.produto_id WHERE m.tipo = 'saida' "
        "GROUP BY p.id ORDER BY unidades DESC, p.nome LIMIT 5").fetchall()
    return {
        "total_produtos": r["produtos"],
        "total_unidades": r["unidades"],
        "valor_total": round(r["valor"], 2),
        "produtos_em_baixa": r["em_baixa"],
        "entradas": mov["entrada"],
        "saidas": mov["saida"],
        "lista_em_baixa": [_produto(x) for x in baixa],
        "mais_saidas": [dict(x) for x in mais_saidas],
    }
