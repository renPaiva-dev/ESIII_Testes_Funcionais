"""API REST em JSON (alvo dos testes de desempenho e da preparação de dados).

Sem autenticação, para simplificar os testes de carga em ambiente local.
"""
from flask import Blueprint, current_app, jsonify, request

from database import esquema
from models import ErroRegra
from services import MovimentacaoService, ProdutoService, RelatorioService

bp = Blueprint("api", __name__, url_prefix="/api")

produto_service = ProdutoService()
movimentacao_service = MovimentacaoService(produto_service)
relatorio_service = RelatorioService()


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
    resultado = produto_service.listar(request.args.get("q", ""), request.args.get("baixo") == "1", _pagina())
    return jsonify(resultado.to_dict())


@bp.get("/produtos/<int:pid>")
def obter(pid):
    return jsonify(produto_service.obter(pid).to_dict())


@bp.post("/produtos")
def criar():
    return jsonify(produto_service.criar(_json(), "api").to_dict()), 201


@bp.put("/produtos/<int:pid>")
def editar(pid):
    return jsonify(produto_service.editar(pid, _json()).to_dict())


@bp.delete("/produtos/<int:pid>")
def excluir(pid):
    produto_service.excluir(pid)
    return jsonify(mensagem="Produto excluído.")


@bp.get("/produtos/<int:pid>/movimentacoes")
def historico(pid):
    return jsonify([m.to_dict() for m in movimentacao_service.historico(pid)])


@bp.post("/produtos/<int:pid>/movimentacoes")
def movimentar(pid):
    dados = _json()
    usuario = str(dados.get("usuario") or "api")[:40]
    resposta = movimentacao_service.registrar(pid, dados, usuario).to_dict()
    resposta.pop("criado_em")  # contrato da API (README): o 201 não devolve a data
    return jsonify(resposta), 201


@bp.get("/relatorio")
def relatorio():
    return jsonify(relatorio_service.gerar())


@bp.post("/reset")
def reset():
    if not current_app.config["PERMITIR_RESET"]:
        return jsonify(erro="Reset desabilitado."), 403
    esquema.resetar(current_app.config["SEED_PRODUTOS"])
    return jsonify(mensagem="Dados restaurados.", produtos=current_app.config["SEED_PRODUTOS"])
