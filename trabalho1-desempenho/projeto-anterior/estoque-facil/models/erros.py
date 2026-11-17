"""Erro de regra de negócio, compartilhado por todas as camadas."""


class ErroRegra(Exception):
    """Violação de regra. Leva a mensagem exibida ao usuário e o status HTTP usado pela API.

    422 = dado inválido, 409 = conflito de regra, 404 = inexistente, 400 = corpo malformado.
    """

    def __init__(self, mensagem, status=422):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
