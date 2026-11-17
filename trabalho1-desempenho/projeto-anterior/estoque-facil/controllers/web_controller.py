"""Telas web (alvo dos testes funcionais com Selenium)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from controllers.autorizacao import admin_obrigatorio, login_obrigatorio
from models import ErroRegra
from services import AutenticacaoService, MovimentacaoService, ProdutoService, RelatorioService

bp = Blueprint("web", __name__)

autenticacao_service = AutenticacaoService()
produto_service = ProdutoService()
movimentacao_service = MovimentacaoService(produto_service)
relatorio_service = RelatorioService()


def _int_arg(nome, padrao):
    try:
        return int(request.args.get(nome, padrao))
    except (TypeError, ValueError):
        return padrao


def _obter_ou_404(pid):
    try:
        return produto_service.obter(pid)
    except ErroRegra:
        abort(404)


@bp.get("/")
def inicio():
    return redirect(url_for("web.produtos"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        login_digitado = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        if not login_digitado or not senha:
            erro = "Informe usuário e senha."
        else:
            usuario = autenticacao_service.autenticar(login_digitado, senha)
            if not usuario:
                erro = "Usuário ou senha inválidos."
            else:
                session.clear()
                session.update(usuario=usuario.login, nome=usuario.nome, perfil=usuario.perfil)
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
    resultado = produto_service.listar(q, baixo, _int_arg("pagina", 1))
    return render_template("produtos.html", q=q, baixo=baixo, total=resultado.total,
                           pagina=resultado.pagina, paginas=resultado.paginas, itens=resultado.itens)


@bp.route("/produtos/novo", methods=["GET", "POST"])
@admin_obrigatorio
def novo():
    if request.method == "POST":
        try:
            p = produto_service.criar(request.form.to_dict(), session["usuario"])
        except ErroRegra as e:
            return render_template("produto_form.html", modo="novo", form=request.form, erro=e.mensagem)
        flash("Produto cadastrado com sucesso.", "sucesso")
        return redirect(url_for("web.detalhe", pid=p.id))
    return render_template("produto_form.html", modo="novo", form={})


@bp.get("/produtos/<int:pid>")
@login_obrigatorio
def detalhe(pid):
    p = _obter_ou_404(pid)
    return render_template("produto_detalhe.html", p=p, historico=movimentacao_service.historico(pid))


@bp.route("/produtos/<int:pid>/editar", methods=["GET", "POST"])
@admin_obrigatorio
def editar(pid):
    p = _obter_ou_404(pid)
    if request.method == "POST":
        try:
            produto_service.editar(pid, request.form.to_dict())
        except ErroRegra as e:
            return render_template("produto_form.html", modo="editar", produto=p, form=request.form, erro=e.mensagem)
        flash("Produto atualizado com sucesso.", "sucesso")
        return redirect(url_for("web.detalhe", pid=pid))
    form = {"nome": p.nome, "preco": f"{p.preco:.2f}", "estoque_minimo": p.estoque_minimo}
    return render_template("produto_form.html", modo="editar", produto=p, form=form)


@bp.post("/produtos/<int:pid>/excluir")
@admin_obrigatorio
def excluir(pid):
    try:
        produto_service.excluir(pid)
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
        m = movimentacao_service.registrar(pid, request.form.to_dict(), session["usuario"])
    except ErroRegra as e:
        if e.status == 404:
            abort(404)
        flash(e.mensagem, "erro")
    else:
        rotulo = "Entrada" if m.tipo == "entrada" else "Saída"
        flash(f"{rotulo} registrada. Saldo atual: {m.saldo_apos}.", "sucesso")
    return redirect(url_for("web.detalhe", pid=pid))


@bp.get("/relatorio")
@login_obrigatorio
def relatorio():
    return render_template("relatorio.html", r=relatorio_service.gerar())
