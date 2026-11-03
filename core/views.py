from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .api import ErroAPI, autenticar
from .forms import LoginForm
from .sessao import encerrar_login, salvar_login, usuario_logado


def login_view(request):
    usuario = usuario_logado(request)
    if usuario and usuario.get("papel") == "professor":
        return redirect("professor:painel")

    form = LoginForm(request.POST or None)
    erro = None

    if request.method == "POST" and form.is_valid():
        try:
            dados = autenticar(form.cleaned_data["email"], form.cleaned_data["senha"])
        except ErroAPI as e:
            erro = e.mensagem
        else:
            if dados["usuario"].get("papel") != "professor":
                erro = "Este acesso é exclusivo para professores."
            else:
                salvar_login(request, dados)
                return redirect("professor:painel")

    return render(request, "auth/login.html", {"form": form, "erro": erro})


@require_POST
def logout_view(request):
    encerrar_login(request)
    return redirect("core:login")
