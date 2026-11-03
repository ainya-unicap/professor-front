import requests
from django.conf import settings


class ErroAPI(Exception):
    def __init__(self, mensagem, status=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def _url(caminho):
    return f"{settings.API_BASE_URL.rstrip('/')}/{caminho.lstrip('/')}"


def autenticar(email, senha):
    try:
        resposta = requests.post(
            _url("auth/login/"),
            json={"email": email, "password": senha},
            timeout=10,
        )
    except requests.RequestException:
        raise ErroAPI("Não foi possível conectar ao servidor. Tente novamente.")

    if resposta.status_code == 401:
        raise ErroAPI("E-mail ou senha inválidos.", status=401)
    if not resposta.ok:
        raise ErroAPI("Não foi possível entrar agora. Tente novamente.", status=resposta.status_code)
    return resposta.json()
