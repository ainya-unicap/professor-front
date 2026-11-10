from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .api import ErroAPI, ErroValidacao, autenticar, cadastrar
from .forms import CadastroForm, LoginForm
from .sessao import encerrar_login, salvar_login, usuario_logado


def _professor_logado(request):
    usuario = usuario_logado(request)
    return bool(usuario and usuario.get("papel") == "professor")


def login_view(request):
    if _professor_logado(request):
        return redirect("professor:turmas")

    form = LoginForm(request.POST if request.method == "POST" else None)
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
                return redirect("professor:turmas")

    return render(request, "auth/login.html", {"form": form, "erro": erro})


def cadastro_view(request):
    if _professor_logado(request):
        return redirect("professor:turmas")

    form = CadastroForm(request.POST if request.method == "POST" else None)
    erro = None

    if request.method == "POST" and form.is_valid():
        try:
            dados = cadastrar(
                form.cleaned_data["nome"],
                form.cleaned_data["email"],
                form.cleaned_data["senha"],
            )
        except ErroValidacao as e:
            restantes = form.aplicar_erros_api(e.erros)
            erro = " ".join(restantes) or None
        except ErroAPI as e:
            erro = e.mensagem
        else:
            salvar_login(request, dados)
            return redirect("professor:turmas")

    return render(request, "auth/cadastro.html", {"form": form, "erro": erro})


@require_POST
def logout_view(request):
    encerrar_login(request)
    return redirect("core:login")
