from functools import wraps

from django.shortcuts import redirect

CHAVE_SESSAO = "auth"


def salvar_login(request, usuario):
    request.session.cycle_key()
    request.session[CHAVE_SESSAO] = usuario


def usuario_logado(request):
    return request.session.get(CHAVE_SESSAO)


def atualizar_tokens(request, tokens):
    auth = request.session.get(CHAVE_SESSAO)
    if not auth:
        return
    auth["accessToken"] = tokens["accessToken"]
    auth["refreshToken"] = tokens["refreshToken"]
    request.session[CHAVE_SESSAO] = auth


def encerrar_login(request):
    request.session.flush()


def professor_obrigatorio(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        usuario = usuario_logado(request)
        if not usuario or usuario.get("role") != "professor":
            return redirect("core:login")
        request.usuario = usuario
        return view(request, *args, **kwargs)

    return wrapper


def com_renovacao(request, chamada, *args, **kwargs):
    """Executa `chamada(token, *args, **kwargs)`.

    Se o access token tiver expirado (401), renova com o refresh token
    guardado na sessão e tenta a chamada mais uma vez.
    """
    from .api import ErroAPI, trocar_token

    usuario = request.usuario
    try:
        return chamada(usuario["accessToken"], *args, **kwargs)
    except ErroAPI as e:
        if e.status != 401:
            raise
        try:
            tokens = trocar_token(usuario["refreshToken"])
        except ErroAPI:
            encerrar_login(request)
            raise

        atualizar_tokens(request, tokens)
        usuario["accessToken"] = tokens["accessToken"]
        usuario["refreshToken"] = tokens["refreshToken"]
        return chamada(usuario["accessToken"], *args, **kwargs)
