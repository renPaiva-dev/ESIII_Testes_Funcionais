"""Entidade Usuario (perfis admin e operador, RN03)."""
from dataclasses import dataclass


@dataclass
class Usuario:
    id: int
    login: str
    senha_hash: str
    nome: str
    perfil: str          # "admin" ou "operador"

    @property
    def eh_admin(self):
        return self.perfil == "admin"
