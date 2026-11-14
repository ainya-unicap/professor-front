from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .api import ErroAPI, autenticar, buscar_usuario, cadastrar, encerrar_sessao_api
from .forms import CadastroForm, LoginForm
from .sessao import encerrar_login, salvar_login, usuario_logado


def _professor_logado(request):
    usuario = usuario_logado(request)
    return bool(usuario and usuario.get("role") == "professor")


def _recaptcha_token(form):
    """Usa o token do widget se houver; senão cai no bypass de dev, se configurado."""
    return form.cleaned_data.get("recaptcha_token") or settings.RECAPTCHA_BYPASS_TOKEN or None


def login_view(request):
    if _professor_logado(request):
        return redirect("professor:painel")

    form = LoginForm(request.POST if request.method == "POST" else None)
    erro = None

    if request.method == "POST" and form.is_valid():
        try:
            tokens = autenticar(
                form.cleaned_data["email"],
                form.cleaned_data["senha"],
                _recaptcha_token(form),
            )
        except ErroAPI as e:
            erro = "E-mail ou senha inválidos." if e.status == 401 else e.mensagem
        else:
            if tokens.get("role") != "professor":
                erro = "Este acesso é exclusivo para professores."
            else:
                perfil = buscar_usuario(tokens["id"], tokens["accessToken"])
                salvar_login(request, {
                    "id": tokens["id"],
                    "role": tokens["role"],
                    "accessToken": tokens["accessToken"],
                    "refreshToken": tokens["refreshToken"],
                    "name": perfil.get("name"),
                    "email": perfil.get("email"),
                })
                return redirect("professor:painel")

    return render(request, "auth/login.html", {
        "form": form,
        "erro": erro,
        "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
    })


def cadastro_view(request):
    if _professor_logado(request):
        return redirect("professor:painel")

    form = CadastroForm(request.POST if request.method == "POST" else None)
    erro = None

    if request.method == "POST" and form.is_valid():
        try:
            cadastrar(
                form.cleaned_data["nome"],
                form.cleaned_data["email"],
                form.cleaned_data["senha"],
                form.cleaned_data["confirmar_senha"],
                _recaptcha_token(form),
            )
        except ErroAPI as e:
            erro = form.aplicar_erro_api(e)
        else:
            messages.success(request, "Conta criada! Agora entre com seu e-mail e senha.")
            return redirect("core:login")

    return render(request, "auth/cadastro.html", {
        "form": form,
        "erro": erro,
        "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
    })


@require_POST
def logout_view(request):
    usuario = usuario_logado(request)
    if usuario:
        encerrar_sessao_api(usuario.get("refreshToken"))
    encerrar_login(request)
    return redirect("core:login")
