from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.api import ErroAPI, ErroValidacao, buscar_painel, criar_turma
from core.sessao import professor_obrigatorio

from .forms import NovaTurmaForm, periodo_atual
from .painel import montar_painel


def _form_vazio(painel):
    return NovaTurmaForm(
        initial={
            "periodo": (painel or {}).get("periodo_atual") or periodo_atual(),
            "instituicao": (painel or {}).get("instituicao") or "",
        }
    )


def _render_painel(request, form=None, abrir_modal=False, erro_modal=None):
    painel = None
    erro = None
    try:
        painel = montar_painel(buscar_painel(request))
    except ErroAPI as e:
        if e.status == 401:
            raise
        erro = e.mensagem

    return render(
        request,
        "professor/painel.html",
        {
            "secao": "painel",
            "usuario": request.usuario,
            "primeiro_nome": request.usuario["nome"].split()[0],
            "painel": painel,
            "pendentes": painel["pendentes"] if painel else None,
            "erro": erro,
            "form": form or _form_vazio(painel),
            "abrir_modal": abrir_modal,
            "erro_modal": erro_modal,
        },
    )


@professor_obrigatorio
def painel(request):
    return _render_painel(request)


@professor_obrigatorio
@require_http_methods(["GET", "POST"])
def nova_turma(request):
    if request.method == "GET":
        return _render_painel(request, abrir_modal=True)

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
            return redirect("professor:painel")

    return _render_painel(request, form=form, abrir_modal=True, erro_modal=erro_modal)
