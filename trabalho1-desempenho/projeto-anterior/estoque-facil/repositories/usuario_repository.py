"""Acesso à tabela usuarios."""
from models import Usuario


class UsuarioRepository:
    def __init__(self, con):
        self.con = con

    def buscar_por_login(self, login):
        row = self.con.execute("SELECT * FROM usuarios WHERE login = ?", (login,)).fetchone()
        return Usuario(**dict(row)) if row else None
