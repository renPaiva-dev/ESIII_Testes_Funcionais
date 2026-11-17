"""Telas web (alvo dos testes funcionais com Selenium)."""
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

import estoque
from regras import ErroRegra

bp = Blueprint("web", __name__)


def login_obrigatorio(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "usuario" not in session:
            return redirect(url_for("web.login"))
        return f(*a, **kw)
    return wrapper


def admin_obrigatorio(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if session.get("perfil") != "admin":
            flash("Acesso restrito ao administrador.", "erro")
            return redirect(url_for("web.produtos"))
        return f(*a, **kw)
    return login_obrigatorio(wrapper)


def _int_arg(nome, padrao):
    try:
        return int(request.args.get(nome, padrao))
    except (TypeError, ValueError):
        return padrao


@bp.get("/")
def inicio():
    return redirect(url_for("web.produtos"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        if not usuario or not senha:
            erro = "Informe usuário e senha."
        else:
            u = estoque.autenticar(usuario, senha)
            if not u:
                erro = "Usuário ou senha inválidos."
            else:
                session.clear()
                session.update(usuario=u["login"], nome=u["nome"], perfil=u["perfil"])
                return redirect(url_for("web.produtos"))
    return render_template("login.html", erro=erro, usuario=request.form.get("usuario", ""))


@bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("web.login"))


@bp.get("/produtos")
@login_obrigatorio
def produtos():
    q = request.args.get("q", "")
    baixo = request.args.get("baixo") == "1"
    res = estoque.listar(q, baixo, _int_arg("pagina", 1))
    return render_template("produtos.html", q=q, baixo=baixo, **res)


@bp.route("/produtos/novo", methods=["GET", "POST"])
@admin_obrigatorio
def novo():
    if request.method == "POST":
        try:
            p = estoque.criar(request.form.to_dict(), session["usuario"])
        except ErroRegra as e:
            return render_template("produto_form.html", modo="novo", form=request.form, erro=e.mensagem)
        flash("Produto cadastrado com sucesso.", "sucesso")
        return redirect(url_for("web.detalhe", pid=p["id"]))
    return render_template("produto_form.html", modo="novo", form={})


@bp.get("/produtos/<int:pid>")
@login_obrigatorio
def detalhe(pid):
    try:
        p = estoque.obter(pid)
    except ErroRegra:
        abort(404)
    return render_template("produto_detalhe.html", p=p, historico=estoque.historico(pid))


@bp.route("/produtos/<int:pid>/editar", methods=["GET", "POST"])
@admin_obrigatorio
def editar(pid):
    try:
        p = estoque.obter(pid)
    except ErroRegra:
        abort(404)
    if request.method == "POST":
        try:
            estoque.editar(pid, request.form.to_dict())
        except ErroRegra as e:
            return render_template("produto_form.html", modo="editar", produto=p, form=request.form, erro=e.mensagem)
        flash("Produto atualizado com sucesso.", "sucesso")
        return redirect(url_for("web.detalhe", pid=pid))
    form = {"nome": p["nome"], "preco": f"{p['preco']:.2f}", "estoque_minimo": p["estoque_minimo"]}
    return render_template("produto_form.html", modo="editar", produto=p, form=form)


@bp.post("/produtos/<int:pid>/excluir")
@admin_obrigatorio
def excluir(pid):
    try:
        estoque.excluir(pid)
    except ErroRegra as e:
        if e.status == 404:
            abort(404)
        flash(e.mensagem, "erro")
        return redirect(url_for("web.detalhe", pid=pid))
    flash("Produto excluído.", "sucesso")
    return redirect(url_for("web.produtos"))


@bp.post("/produtos/<int:pid>/movimentacoes")
@login_obrigatorio
def movimentar(pid):
    try:
        m = estoque.registrar_movimentacao(pid, request.form.to_dict(), session["usuario"])
    except ErroRegra as e:
        if e.status == 404:
            abort(404)
        flash(e.mensagem, "erro")
    else:
        rotulo = "Entrada" if m["tipo"] == "entrada" else "Saída"
        flash(f"{rotulo} registrada. Saldo atual: {m['saldo_apos']}.", "sucesso")
    return redirect(url_for("web.detalhe", pid=pid))


@bp.get("/relatorio")
@login_obrigatorio
def relatorio():
    return render_template("relatorio.html", r=estoque.relatorio())
