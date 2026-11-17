"""Estoque Fácil - sistema simples de controle de estoque (arquitetura em camadas).

Ponto de entrada: cria a aplicação Flask, registra os controllers e trata os erros globais.

    controllers  ->  services  ->  repositories  ->  database
                 (todos usam models: entidades e ErroRegra)

Executar:
    pip install -r requirements.txt
    python app.py              # http://127.0.0.1:5001
    python app.py --reset      # recria os dados iniciais antes de subir

Variáveis de ambiente (opcionais):
    PORTA           porta HTTP (padrão 5001)
    ESTOQUE_DB      caminho do arquivo SQLite (padrão dados/estoque.db)
    SEED_PRODUTOS   quantidade de produtos iniciais, mínimo 10 (padrão 30)
    PERMITIR_RESET  "0" desliga POST /api/reset (padrão "1")
"""
import argparse
import sqlite3

from flask import Flask, jsonify, render_template, request

import config
from controllers import api_controller, web_controller
from database import conexao, esquema
from models import TEXTO_SITUACAO


def moeda(valor):
    """12345.6 -> 'R$ 12.345,60'"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def create_app(config_extra=None):
    app = Flask(__name__)
    app.config.update(config.carregar())
    if config_extra:
        app.config.update(config_extra)
    app.json.ensure_ascii = False
    app.jinja_env.filters["moeda"] = moeda
    app.jinja_env.globals["textos_situacao"] = TEXTO_SITUACAO
    app.teardown_appcontext(conexao.fechar)
    app.register_blueprint(web_controller.bp)
    app.register_blueprint(api_controller.bp)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    def _eh_api():
        return request.path.startswith("/api/")

    @app.errorhandler(404)
    def nao_encontrado(_e):
        if _eh_api():
            return jsonify(erro="Recurso não encontrado."), 404
        return render_template("erro.html", mensagem="Página não encontrada."), 404

    @app.errorhandler(405)
    def metodo_invalido(_e):
        return jsonify(erro="Método não permitido."), 405

    @app.errorhandler(sqlite3.OperationalError)
    def banco_ocupado(e):
        # Sob carga pesada o SQLite pode esgotar o tempo de espera pela escrita.
        app.logger.warning("Erro do banco: %s", e)
        if _eh_api():
            return jsonify(erro="Banco de dados ocupado. Tente novamente."), 503
        return render_template("erro.html", mensagem="Sistema ocupado. Tente novamente."), 503

    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estoque Fácil")
    parser.add_argument("--reset", action="store_true", help="recria os dados iniciais")
    args = parser.parse_args()

    aplicacao = create_app()
    esquema.iniciar(aplicacao, reset=args.reset)
    porta = config.porta()
    print(f"Estoque Fácil em http://127.0.0.1:{porta}  (banco: {aplicacao.config['DATABASE']})", flush=True)
    aplicacao.run(host="127.0.0.1", port=porta, threaded=True)
