from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from core.api import ErroAPI, ErroValidacao, criar_turma, listar_turmas
from core.sessao import professor_obrigatorio

from .apresentacao import preparar_turmas
from .forms import NovaTurmaForm, periodo_atual


def _contexto_base(request, secao):
    return {"secao": secao, "usuario": request.usuario}


def _render_turmas(request, form=None, abrir_modal=False, erro_modal=None):
    turmas = []
    erro = None
    try:
        turmas = listar_turmas(request)
    except ErroAPI as e:
        if e.status == 401:
            raise
        erro = e.mensagem

    recente = turmas[0] if turmas else None
    contexto = _contexto_base(request, "turmas")
    contexto.update(
        {
            "primeiro_nome": request.usuario["nome"].split()[0],
            "turmas": preparar_turmas(turmas),
            "erro": erro,
            "form": form
            or NovaTurmaForm(
                initial={
                    "periodo": recente["periodo"] if recente else periodo_atual(),
                    "instituicao": recente["instituicao"] if recente else "",
                }
            ),
            "abrir_modal": abrir_modal,
            "erro_modal": erro_modal,
        }
    )
    return render(request, "professor/turmas.html", contexto)


@professor_obrigatorio
@require_GET
def turmas(request):
    return _render_turmas(request)


@professor_obrigatorio
@require_http_methods(["GET", "POST"])
def nova_turma(request):
    if request.method == "GET":
        return _render_turmas(request, abrir_modal=True)

    form = NovaTurmaForm(request.POST)
    erro_modal = None
    if form.is_valid():
        try:
            turma = criar_turma(
                request,
                form.cleaned_data["nome"],
                form.cleaned_data["periodo"],
                form.cleaned_data["instituicao"],
            )
        except ErroValidacao as e:
            erro_modal = " ".join(form.aplicar_erros_api(e.erros)) or None
        except ErroAPI as e:
            if e.status == 401:
                raise
            erro_modal = e.mensagem
        else:
            messages.success(
                request,
                f"Turma “{turma['nome']}” criada. Código de convite: {turma['codigo_convite']}",
            )
            return redirect("professor:turmas")

    return _render_turmas(request, form=form, abrir_modal=True, erro_modal=erro_modal)
