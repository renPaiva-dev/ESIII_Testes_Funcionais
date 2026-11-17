"""Regras de validação do Estoque Fácil (funções puras, sem banco nem Flask).

Cada violação levanta ErroRegra com a mensagem exibida ao usuário e o
status HTTP usado pela API (422 = dado inválido, 409 = conflito de regra,
404 = inexistente, 400 = corpo malformado).
"""
import re

SKU_RE = re.compile(r"[A-Z0-9][A-Z0-9-]{2,19}")   # 3 a 20 caracteres
NOME_MIN, NOME_MAX = 3, 60
PRECO_MIN, PRECO_MAX = 0.01, 99999.99
QTD_MAX = 10000
OBS_MAX = 200

MSG = {
    "sku": "SKU deve ter de 3 a 20 caracteres (letras, números ou hífen).",
    "nome": "Nome deve ter de 3 a 60 caracteres.",
    "preco": "Preço deve estar entre 0,01 e 99.999,99.",
    "minimo": "Estoque mínimo deve ser um inteiro entre 0 e 10000.",
    "qtd_inicial": "Quantidade inicial deve ser um inteiro entre 0 e 10000.",
    "tipo": "Selecione o tipo de movimentação (entrada ou saída).",
    "qtd_mov": "Quantidade deve ser um inteiro entre 1 e 10000.",
    "obs": "Observação deve ter no máximo 200 caracteres.",
    "json": "JSON inválido.",
}


class ErroRegra(Exception):
    def __init__(self, mensagem, status=422):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def _inteiro(valor):
    """Aceita int ou texto só com dígitos. Rejeita bool, fração e vazio."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and re.fullmatch(r"\s*\d+\s*", valor):
        return int(valor)
    return None


def _decimal(valor):
    """Aceita número ou texto como 12.50 / 12,50 (no máximo 2 casas)."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        v = float(valor)
        return v if abs(round(v, 2) - v) < 1e-9 else None
    if isinstance(valor, str):
        s = valor.strip().replace(",", ".")
        if re.fullmatch(r"\d{1,5}(\.\d{1,2})?", s):
            return float(s)
    return None


def _exigir_dict(dados):
    if not isinstance(dados, dict):
        raise ErroRegra(MSG["json"], 400)


def validar_produto(dados, novo=True):
    """Valida cadastro (novo=True) ou edição (novo=False; SKU e quantidade não mudam).

    Ordem das verificações: SKU, nome, preço, estoque mínimo, quantidade inicial.
    Retorna um dict com os valores normalizados.
    """
    _exigir_dict(dados)
    r = {}
    if novo:
        sku = str(dados.get("sku") or "").strip().upper()
        if not SKU_RE.fullmatch(sku):
            raise ErroRegra(MSG["sku"])
        r["sku"] = sku

    nome = str(dados.get("nome") or "").strip()
    if not NOME_MIN <= len(nome) <= NOME_MAX:
        raise ErroRegra(MSG["nome"])
    r["nome"] = nome

    preco = _decimal(dados.get("preco"))
    if preco is None or not PRECO_MIN <= preco <= PRECO_MAX:
        raise ErroRegra(MSG["preco"])
    r["preco"] = round(preco, 2)

    minimo = _inteiro(dados.get("estoque_minimo"))
    if minimo is None or not 0 <= minimo <= QTD_MAX:
        raise ErroRegra(MSG["minimo"])
    r["estoque_minimo"] = minimo

    if novo:
        bruto = dados.get("quantidade")
        qtd = 0 if bruto is None or (isinstance(bruto, str) and not bruto.strip()) else _inteiro(bruto)
        if qtd is None or not 0 <= qtd <= QTD_MAX:
            raise ErroRegra(MSG["qtd_inicial"])
        r["quantidade"] = qtd
    return r


def validar_movimentacao(dados):
    """Valida tipo (entrada/saida), quantidade (1..10000) e observação (até 200)."""
    _exigir_dict(dados)
    tipo = str(dados.get("tipo") or "").strip().lower()
    if tipo not in ("entrada", "saida"):
        raise ErroRegra(MSG["tipo"])
    qtd = _inteiro(dados.get("quantidade"))
    if qtd is None or not 1 <= qtd <= QTD_MAX:
        raise ErroRegra(MSG["qtd_mov"])
    obs = str(dados.get("observacao") or "").strip()
    if len(obs) > OBS_MAX:
        raise ErroRegra(MSG["obs"])
    return {"tipo": tipo, "quantidade": qtd, "observacao": obs}
