from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.api import ErroAPI, listar_instituicoes, listar_periodos
from core.sessao import com_renovacao, professor_obrigatorio

from . import api as turmas_api
from .forms import TurmaForm


def _opcoes_formulario():
    try:
        return listar_periodos(), listar_instituicoes()
    except ErroAPI:
        return [], []


@professor_obrigatorio
def painel(request):
    erro = None
    turmas = []
    try:
        turmas = com_renovacao(request, turmas_api.listar_turmas)
    except ErroAPI as e:
        erro = e.mensagem

    periodos, instituicoes = _opcoes_formulario()
    form_turma = TurmaForm(periodos=periodos, instituicoes=instituicoes)

    return render(request, "professor/painel.html", {
        "usuario": request.usuario,
        "turmas": turmas,
        "erro": erro,
        "form_turma": form_turma,
    })


@professor_obrigatorio
@require_POST
def turma_criar(request):
    periodos, instituicoes = _opcoes_formulario()
    form = TurmaForm(request.POST, periodos=periodos, instituicoes=instituicoes)
    erro = None

    if form.is_valid():
        try:
            com_renovacao(
                request,
                turmas_api.criar_turma,
                form.cleaned_data["name"],
                form.cleaned_data["period_id"],
                form.cleaned_data.get("institution_id") or None,
            )
        except ErroAPI as e:
            erro = form.aplicar_erro_api(e)
        else:
            messages.success(request, "Turma criada com sucesso.")
            return redirect("professor:painel")

    try:
        turmas = com_renovacao(request, turmas_api.listar_turmas)
    except ErroAPI:
        turmas = []

    return render(request, "professor/painel.html", {
        "usuario": request.usuario,
        "turmas": turmas,
        "erro": erro,
        "form_turma": form,
    })


@professor_obrigatorio
def turma_detalhe(request, turma_id):
    erro = None
    codigos = []
    entregas = []
    try:
        codigos = com_renovacao(request, turmas_api.listar_codigos, turma_id)
        entregas = com_renovacao(request, turmas_api.listar_entregas, turma_id)
    except ErroAPI as e:
        erro = e.mensagem

    return render(request, "professor/turma_detalhe.html", {
        "usuario": request.usuario,
        "turma_id": turma_id,
        "codigos": codigos,
        "entregas": entregas,
        "erro": erro,
    })


@professor_obrigatorio
@require_POST
def turma_apagar(request, turma_id):
    try:
        com_renovacao(request, turmas_api.apagar_turma, turma_id)
    except ErroAPI as e:
        messages.error(request, e.mensagem)
    else:
        messages.success(request, "Turma apagada com sucesso.")
    return redirect("professor:painel")


@professor_obrigatorio
@require_POST
def codigo_gerar(request, turma_id):
    try:
        com_renovacao(request, turmas_api.gerar_codigo, turma_id)
    except ErroAPI as e:
        messages.error(request, e.mensagem)
    else:
        messages.success(request, "Novo código gerado.")
    return redirect("professor:turma_detalhe", turma_id=turma_id)


@professor_obrigatorio
@require_POST
def codigo_apagar(request, turma_id, codigo_id):
    try:
        com_renovacao(request, turmas_api.apagar_codigo, turma_id, codigo_id)
    except ErroAPI as e:
        messages.error(request, e.mensagem)
    else:
        messages.success(request, "Código apagado.")
    return redirect("professor:turma_detalhe", turma_id=turma_id)
