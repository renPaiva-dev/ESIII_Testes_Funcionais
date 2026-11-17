"""RN01 – Login."""
from werkzeug.security import check_password_hash

from database.conexao import get_db
from repositories import UsuarioRepository


class AutenticacaoService:
    def autenticar(self, login, senha):
        """Retorna o Usuario se login e senha conferem, senão None.

        A senha é conferida com hash scrypt: um custo intencional de segurança
        (é o ponto mais caro do sistema nos testes de desempenho).
        """
        usuario = UsuarioRepository(get_db()).buscar_por_login(login)
        if usuario and check_password_hash(usuario.senha_hash, senha):
            return usuario
        return None
