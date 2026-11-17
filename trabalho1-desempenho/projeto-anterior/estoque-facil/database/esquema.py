"""Esquema do banco e dados iniciais (seed). Os dados são sempre iguais após cada reset."""
import random
from pathlib import Path

from werkzeug.security import generate_password_hash

from database.conexao import agora, get_db, transacao

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY,
    login       TEXT UNIQUE NOT NULL,
    senha_hash  TEXT NOT NULL,
    nome        TEXT NOT NULL,
    perfil      TEXT NOT NULL CHECK (perfil IN ('admin', 'operador'))
);
CREATE TABLE IF NOT EXISTS produtos (
    id              INTEGER PRIMARY KEY,
    sku             TEXT UNIQUE NOT NULL,
    nome            TEXT NOT NULL,
    preco           REAL NOT NULL CHECK (preco > 0),
    quantidade      INTEGER NOT NULL CHECK (quantidade >= 0),
    estoque_minimo  INTEGER NOT NULL CHECK (estoque_minimo >= 0),
    criado_em       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS movimentacoes (
    id          INTEGER PRIMARY KEY,
    produto_id  INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
    tipo        TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
    quantidade  INTEGER NOT NULL CHECK (quantidade > 0),
    saldo_apos  INTEGER NOT NULL,
    usuario     TEXT NOT NULL,
    observacao  TEXT,
    criado_em   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mov_produto ON movimentacoes(produto_id);
"""

USUARIOS = [
    # login, senha, nome, perfil
    ("admin", "admin123", "Administrador", "admin"),
    ("operador", "oper123", "Operador de Estoque", "operador"),
]

# Produtos fixos (sempre os ids 1 a 10 após o reset). Os testes podem contar com eles.
PRODUTOS_BASE = [
    # sku, nome, preco, quantidade, estoque_minimo
    ("CAN-001", "Caneta esferográfica azul", 2.50, 200, 50),
    ("CAD-001", "Caderno universitário 200 folhas", 18.90, 40, 10),
    ("LAP-001", "Lápis preto HB", 1.20, 8, 30),           # estoque baixo
    ("BOR-001", "Borracha branca", 1.80, 60, 20),
    ("GRA-001", "Grampeador de mesa", 32.00, 5, 5),        # baixo (igual ao mínimo)
    ("RES-001", "Resma papel A4 500 folhas", 29.90, 25, 10),
    ("MAR-001", "Marca-texto amarelo", 4.50, 0, 10),       # sem estoque
    ("TES-001", "Tesoura escolar", 7.90, 15, 5),
    ("COL-001", "Cola branca 90 g", 3.60, 13, 12),         # 1 acima do mínimo
    ("PAS-001", "Pasta catálogo 20 plásticos", 11.00, 30, 8),
]

_hashes = {}


def _hash(senha):
    if senha not in _hashes:
        _hashes[senha] = generate_password_hash(senha)
    return _hashes[senha]


def semear(con, total_produtos):
    """Insere usuários e produtos iniciais. Produtos além dos 10 fixos são gerados."""
    instante = agora()
    con.executemany("INSERT INTO usuarios (login, senha_hash, nome, perfil) VALUES (?, ?, ?, ?)",
                    [(lg, _hash(s), n, p) for lg, s, n, p in USUARIOS])

    rng = random.Random(42)  # sempre os mesmos dados gerados
    linhas = list(PRODUTOS_BASE)
    for n in range(len(PRODUTOS_BASE) + 1, max(total_produtos, len(PRODUTOS_BASE)) + 1):
        linhas.append((f"GEN-{n:05d}", f"Item genérico {n:05d}",
                       round(rng.uniform(1, 500), 2), rng.randint(20, 500), rng.randint(0, 20)))

    con.executemany(
        "INSERT INTO produtos (id, sku, nome, preco, quantidade, estoque_minimo, criado_em) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(i, sku, nome, preco, qtd, minimo, instante)
         for i, (sku, nome, preco, qtd, minimo) in enumerate(linhas, start=1)])
    con.executemany(
        "INSERT INTO movimentacoes (produto_id, tipo, quantidade, saldo_apos, usuario, observacao, criado_em) "
        "VALUES (?, 'entrada', ?, ?, 'sistema', 'Saldo inicial', ?)",
        [(i, qtd, qtd, instante) for i, (_, _, _, qtd, _) in enumerate(linhas, start=1) if qtd > 0])


def resetar(total_produtos):
    """Apaga tudo e recarrega os dados iniciais (ids voltam a começar em 1)."""
    with transacao() as con:
        con.execute("DELETE FROM movimentacoes")
        con.execute("DELETE FROM produtos")
        con.execute("DELETE FROM usuarios")
        semear(con, total_produtos)


def iniciar(app, reset=False):
    """Cria o arquivo e as tabelas; semeia se o banco estiver vazio ou se reset=True."""
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        con = get_db()
        con.execute("PRAGMA journal_mode = WAL")  # leituras não bloqueiam escritas
        con.executescript(SCHEMA)
        vazio = con.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0
        if reset or vazio:
            resetar(app.config["SEED_PRODUTOS"])
