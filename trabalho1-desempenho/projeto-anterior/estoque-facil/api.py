"""API REST em JSON (alvo dos testes de desempenho e da preparação de dados).

Sem autenticação, para simplificar os testes de carga em ambiente local.
"""
from flask import Blueprint, current_app, jsonify, request

import db
import estoque
from regras import ErroRegra

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.errorhandler(ErroRegra)
def _erro_regra(e):
    return jsonify(erro=e.mensagem), e.status


def _json():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ErroRegra("JSON inválido.", 400)
    return dados


def _pagina():
    try:
        return int(request.args.get("pagina", 1))
    except ValueError:
        return 1


@bp.get("/produtos")
def listar():
    return jsonify(estoque.listar(request.args.get("q", ""), request.args.get("baixo") == "1", _pagina()))


@bp.get("/produtos/<int:pid>")
def obter(pid):
    return jsonify(estoque.obter(pid))


@bp.post("/produtos")
def criar():
    return jsonify(estoque.criar(_json(), "api")), 201


@bp.put("/produtos/<int:pid>")
def editar(pid):
    return jsonify(estoque.editar(pid, _json()))


@bp.delete("/produtos/<int:pid>")
def excluir(pid):
    estoque.excluir(pid)
    return jsonify(mensagem="Produto excluído.")


@bp.get("/produtos/<int:pid>/movimentacoes")
def historico(pid):
    return jsonify(estoque.historico(pid))


@bp.post("/produtos/<int:pid>/movimentacoes")
def movimentar(pid):
    dados = _json()
    usuario = str(dados.get("usuario") or "api")[:40]
    return jsonify(estoque.registrar_movimentacao(pid, dados, usuario)), 201


@bp.get("/relatorio")
def relatorio():
    return jsonify(estoque.relatorio())


@bp.post("/reset")
def reset():
    if not current_app.config["PERMITIR_RESET"]:
        return jsonify(erro="Reset desabilitado."), 403
    db.resetar(current_app.config["SEED_PRODUTOS"])
    return jsonify(mensagem="Dados restaurados.", produtos=current_app.config["SEED_PRODUTOS"])
