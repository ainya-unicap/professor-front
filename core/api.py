import requests
from django.conf import settings


class ErroAPI(Exception):
    def __init__(self, mensagem, status=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


class ErroValidacao(ErroAPI):
    def __init__(self, erros):
        super().__init__("Revise os campos destacados.", status=400)
        self.erros = erros


def _url(caminho):
    return f"{settings.API_BASE_URL.rstrip('/')}/{caminho.lstrip('/')}"


def _post(caminho, dados):
    try:
        return requests.post(_url(caminho), json=dados, timeout=10)
    except requests.RequestException:
        raise ErroAPI("Não foi possível conectar ao servidor. Tente novamente.")


def autenticar(email, senha):
    resposta = _post("auth/login/", {"email": email, "password": senha})
    if resposta.status_code == 401:
        raise ErroAPI("E-mail ou senha inválidos.", status=401)
    if not resposta.ok:
        raise ErroAPI("Não foi possível entrar agora. Tente novamente.", status=resposta.status_code)
    return resposta.json()


def cadastrar(nome, email, senha):
    resposta = _post("auth/cadastro/", {"nome": nome, "email": email, "password": senha})
    if resposta.status_code == 400:
        raise ErroValidacao(resposta.json())
    if not resposta.ok:
        raise ErroAPI("Não foi possível criar a conta agora. Tente novamente.", status=resposta.status_code)
    return resposta.json()
