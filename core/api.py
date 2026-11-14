import requests
from django.conf import settings


class ErroAPI(Exception):
    def __init__(self, mensagem, status=None, codigo=None, campos=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
        self.codigo = codigo
        self.campos = campos or {}


def _url(caminho):
    return f"{settings.API_BASE_URL.rstrip('/')}/{caminho.lstrip('/')}"


def requisicao(metodo, caminho, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resposta = requests.request(metodo, _url(caminho), headers=headers, timeout=10, **kwargs)
    except requests.RequestException:
        raise ErroAPI("Não foi possível conectar ao servidor. Tente novamente.")

    if not resposta.ok:
        corpo = {}
        try:
            corpo = resposta.json()
        except ValueError:
            pass
        raise ErroAPI(
            corpo.get("error") or "Não foi possível completar a ação agora. Tente novamente.",
            status=resposta.status_code,
            codigo=corpo.get("codigo"),
            campos=corpo.get("campos"),
        )

    if resposta.status_code == 204 or not resposta.content:
        return None
    return resposta.json()


def autenticar(email, senha, recaptcha_token=None):
    dados = {"email": email, "password": senha}
    if recaptcha_token:
        dados["recaptchaToken"] = recaptcha_token
    return requisicao("POST", "users/login", json=dados)


def cadastrar(nome, email, senha, confirmar_senha, recaptcha_token=None):
    dados = {"name": nome, "email": email, "password": senha, "confirmPassword": confirmar_senha}
    if recaptcha_token:
        dados["recaptchaToken"] = recaptcha_token
    return requisicao("POST", "professores", json=dados)


def buscar_usuario(user_id, token):
    return requisicao("GET", f"users/{user_id}", token=token)


def trocar_token(refresh_token):
    return requisicao("POST", "users/refresh", json={"refreshToken": refresh_token})


def encerrar_sessao_api(refresh_token):
    try:
        requisicao("POST", "users/logout", json={"refreshToken": refresh_token})
    except ErroAPI:
        pass


def listar_periodos():
    return requisicao("GET", "academic-periods")


def listar_instituicoes():
    return requisicao("GET", "institutions")
