import logging

import requests
from django.conf import settings

from .sessao import CHAVE_SESSAO

logger = logging.getLogger(__name__)

_sessao = requests.Session()
_sessao.trust_env = False


class ErroAPI(Exception):
    def __init__(self, mensagem, status=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


class ErroValidacao(ErroAPI):
    def __init__(self, erros):
        super().__init__("Revise os campos destacados.", status=400)
        self.erros = erros


class SessaoExpirada(ErroAPI):
    def __init__(self):
        super().__init__("Sua sessão expirou. Entre novamente.", status=401)


class NaoEncontrado(ErroAPI):
    def __init__(self):
        super().__init__("Não encontrado.", status=404)


def _url(caminho):
    return f"{settings.API_BASE_URL.rstrip('/')}/{caminho.lstrip('/')}"


def _requisicao(metodo, caminho, dados=None, token=None):
    url = _url(caminho)
    cabecalhos = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        return _sessao.request(metodo, url, json=dados, headers=cabecalhos, timeout=10)
    except requests.RequestException as erro:
        logger.warning("Falha ao chamar a API em %s: %r", url, erro)
        raise ErroAPI("Não foi possível conectar ao servidor. Tente novamente.")


def _post(caminho, dados):
    return _requisicao("POST", caminho, dados)


def _renovar_token(refresh):
    resposta = _requisicao("POST", "auth/token/refresh/", {"refresh": refresh})
    if resposta.status_code != 200:
        return None
    return resposta.json().get("access")


def chamar(request, metodo, caminho, dados=None):
    auth = request.session.get(CHAVE_SESSAO)
    if not auth:
        raise SessaoExpirada()

    resposta = _requisicao(metodo, caminho, dados, token=auth["access"])
    if resposta.status_code == 401:
        novo_access = _renovar_token(auth["refresh"])
        if not novo_access:
            raise SessaoExpirada()
        auth["access"] = novo_access
        request.session[CHAVE_SESSAO] = auth
        resposta = _requisicao(metodo, caminho, dados, token=novo_access)
        if resposta.status_code == 401:
            raise SessaoExpirada()
    return resposta


def _verificar(resposta, mensagem):
    if resposta.status_code == 404:
        raise NaoEncontrado()
    if resposta.status_code == 400:
        raise ErroValidacao(resposta.json())
    if not resposta.ok:
        raise ErroAPI(mensagem, status=resposta.status_code)
    return resposta


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


def listar_turmas(request):
    resposta = chamar(request, "GET", "turmas/")
    return _verificar(resposta, "Não foi possível carregar as turmas agora.").json()


def criar_turma(request, nome, periodo, instituicao):
    resposta = chamar(
        request,
        "POST",
        "turmas/",
        {"nome": nome, "periodo": periodo, "instituicao": instituicao},
    )
    return _verificar(resposta, "Não foi possível criar a turma agora. Tente novamente.").json()


def buscar_turma(request, turma_id):
    resposta = chamar(request, "GET", f"turmas/{turma_id}/")
    return _verificar(resposta, "Não foi possível carregar a turma agora.").json()


def listar_relatorios_da_turma(request, turma_id):
    resposta = chamar(request, "GET", f"turmas/{turma_id}/relatorios/")
    return _verificar(resposta, "Não foi possível carregar os relatórios agora.").json()


def baixar_pdf_do_relatorio(request, relatorio_id):
    resposta = chamar(request, "GET", f"relatorios/{relatorio_id}/pdf/")
    return _verificar(resposta, "Não foi possível baixar o PDF agora.")
