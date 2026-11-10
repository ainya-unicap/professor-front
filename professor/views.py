from datetime import datetime

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from core.api import (
    ErroAPI,
    ErroValidacao,
    baixar_pdf_do_relatorio,
    buscar_turma,
    criar_turma,
    listar_relatorios_da_turma,
    listar_turmas,
)
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


@professor_obrigatorio
@require_GET
def turma(request, turma_id):
    turma = buscar_turma(request, turma_id)
    relatorios = []
    erro = None
    try:
        relatorios = [
            {
                **relatorio,
                "entregue_em": datetime.fromisoformat(relatorio["entregue_em"]) if relatorio["entregue_em"] else None,
            }
            for relatorio in listar_relatorios_da_turma(request, turma_id)
        ]
    except ErroAPI as e:
        if e.status in (401, 404):
            raise
        erro = e.mensagem

    contexto = _contexto_base(request, "turmas")
    contexto.update({"turma": turma, "relatorios": relatorios, "erro": erro})
    return render(request, "professor/turma.html", contexto)


@professor_obrigatorio
@require_GET
def relatorio_pdf(request, relatorio_id):
    resposta = baixar_pdf_do_relatorio(request, relatorio_id)
    saida = HttpResponse(resposta.content, content_type="application/pdf")
    saida["Content-Disposition"] = resposta.headers.get("Content-Disposition", "attachment")
    saida["Cache-Control"] = "private, no-store"
    return saida
