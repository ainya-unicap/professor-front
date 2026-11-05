from functools import wraps

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect

CHAVE_SESSAO = "auth"


def salvar_login(request, dados):
    request.session.cycle_key()
    request.session[CHAVE_SESSAO] = {
        "access": dados["access"],
        "refresh": dados["refresh"],
        "usuario": dados["usuario"],
    }


def usuario_logado(request):
    auth = request.session.get(CHAVE_SESSAO)
    return auth["usuario"] if auth else None


def encerrar_login(request):
    request.session.flush()


def professor_obrigatorio(view):
    from .api import NaoEncontrado, SessaoExpirada

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        usuario = usuario_logado(request)
        if not usuario or usuario.get("papel") != "professor":
            return redirect("core:login")
        request.usuario = usuario
        try:
            return view(request, *args, **kwargs)
        except SessaoExpirada as erro:
            encerrar_login(request)
            messages.info(request, erro.mensagem)
            return redirect("core:login")
        except NaoEncontrado:
            raise Http404

    return wrapper
