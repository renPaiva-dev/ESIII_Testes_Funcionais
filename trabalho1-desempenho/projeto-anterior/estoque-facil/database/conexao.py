"""Conexão por requisição e controle de transação."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from flask import current_app, g


def agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_db():
    """Uma conexão por requisição (guardada em g e fechada no teardown)."""
    if "db" not in g:
        con = sqlite3.connect(current_app.config["DATABASE"], timeout=15,
                              isolation_level=None)  # autocommit; transações explícitas
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("PRAGMA busy_timeout = 15000")
        g.db = con
    return g.db


def fechar(_erro=None):
    con = g.pop("db", None)
    if con is not None:
        con.close()


@contextmanager
def transacao():
    """BEGIN IMMEDIATE: reserva a escrita no início, evitando corrida entre leitura e gravação.

    Os services abrem a transação e entregam a conexão aos repositories, assim várias
    operações de repositório (ex.: debitar saldo + gravar histórico) são atômicas.
    """
    con = get_db()
    con.execute("BEGIN IMMEDIATE")
    try:
        yield con
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        raise
