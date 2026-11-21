from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST

from core.api import ErroAPI, criar_instituicao, criar_periodo, listar_instituicoes, listar_periodos
from core.sessao import com_renovacao, professor_obrigatorio

from . import api as turmas_api
from .forms import TurmaForm


def _opcoes_formulario(request):
    try:
        periodos = com_renovacao(request, listar_periodos)
    except ErroAPI:
        periodos = []
    try:
        instituicoes = listar_instituicoes()
    except ErroAPI:
        instituicoes = []
    return periodos, instituicoes


def _preencher_contagens(request, turmas):
    for turma in turmas:
        turma_id = turma.get("id")
        alunos = []
        entregas = None

        if turma_id:
            try:
                alunos = com_renovacao(request, turmas_api.listar_alunos, turma_id)
            except ErroAPI:
                alunos = []

            try:
                entregas = com_renovacao(request, turmas_api.listar_entregas, turma_id)
            except ErroAPI:
                entregas = None

        total_alunos = len(alunos) if isinstance(alunos, list) else 0

        if isinstance(entregas, list):
            relatorios_entregues = len(entregas)
        elif isinstance(alunos, list):
            relatorios_entregues = sum(
                1 for aluno in alunos
                if any(
                    aluno.get(chave)
                    for chave in ("relatorio", "entrega", "report", "arquivo", "arquivo_url", "url", "data_entrega", "submittedAt")
                )
            )
        else:
            relatorios_entregues = 0

        turma["total_alunos"] = total_alunos
        turma["relatorios_entregues"] = relatorios_entregues


@professor_obrigatorio
def painel(request):
    erro = None
    turmas = []
    try:
        turmas = com_renovacao(request, turmas_api.listar_turmas)
    except ErroAPI as e:
        erro = e.mensagem

    periodos, instituicoes = _opcoes_formulario(request)
    form_turma = TurmaForm(periodos=periodos, instituicoes=instituicoes)
    _preencher_contagens(request, turmas)

    return render(request, "professor/painel.html", {
        "usuario": request.usuario,
        "turmas": turmas,
        "erro": erro,
        "form_turma": form_turma,
        "periodos": periodos,
        "instituicoes": instituicoes,
    })


@professor_obrigatorio
@require_POST
def turma_criar(request):
    periodos, instituicoes = _opcoes_formulario(request)
    form = TurmaForm(request.POST, periodos=periodos, instituicoes=instituicoes)
    erro = None

    if form.is_valid():
        try:
            period_id = form.cleaned_data.get("period_id")
            if not period_id:
                periodo = com_renovacao(
                    request,
                    criar_periodo,
                    form.periodo_novo["nome"],
                    form.periodo_novo["semestre"],
                    form.periodo_novo["data_inicio"].isoformat(),
                    form.periodo_novo["data_fim"].isoformat(),
                )
                period_id = periodo["id"]

            institution_id = form.cleaned_data.get("institution_id")
            if not institution_id:
                instituicao = com_renovacao(
                    request,
                    criar_instituicao,
                    form.instituicao_nova["nome"],
                    form.instituicao_nova["sigla"],
                )
                institution_id = instituicao["id"]

            com_renovacao(
                request,
                turmas_api.criar_turma,
                form.cleaned_data["name"],
                period_id,
                institution_id,
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

    _preencher_contagens(request, turmas)

    return render(request, "professor/painel.html", {
        "usuario": request.usuario,
        "turmas": turmas,
        "erro": erro,
        "form_turma": form,
        "periodos": periodos,
        "instituicoes": instituicoes,
    })


def _canteiros_por_aluno(canteiros):
    """Mapeia user_id -> lista de "Planta (Canteiro)" a partir de
    GET /professores/turmas/:id/canteiros (canteiros etiquetados com a turma)."""
    por_aluno = {}
    if not isinstance(canteiros, list):
        return por_aluno

    for canteiro in canteiros:
        planta = (canteiro.get("plant") or {}).get("name")
        nome_canteiro = canteiro.get("name")
        if planta and nome_canteiro:
            texto = f"{planta} ({nome_canteiro})"
        else:
            texto = planta or nome_canteiro or ""
        if not texto:
            continue

        for usuario in canteiro.get("users") or []:
            user_id = str(usuario.get("id"))
            if user_id:
                por_aluno.setdefault(user_id, []).append(texto)

    return por_aluno


@professor_obrigatorio
def turma_detalhe(request, turma_id):
    erro = None
    turma = None
    codigos = []
    alunos = []
    entregas = []
    try:
        turmas = com_renovacao(request, turmas_api.listar_turmas)
        turma = next((t for t in turmas if str(t.get("id")) == str(turma_id)), None)
        codigos = com_renovacao(request, turmas_api.listar_codigos, turma_id)
        alunos = com_renovacao(request, turmas_api.listar_alunos, turma_id)
    except ErroAPI as e:
        erro = e.mensagem

    try:
        entregas = com_renovacao(request, turmas_api.listar_entregas, turma_id)
    except ErroAPI:
        entregas = []

    try:
        canteiros = com_renovacao(request, turmas_api.listar_canteiros, turma_id)
    except ErroAPI:
        canteiros = []

    entregas_por_aluno = {}
    if isinstance(entregas, list):
        for item in entregas:
            chave_aluno = item.get("student_id") or item.get("aluno_id") or item.get("user_id")
            if chave_aluno:
                entregas_por_aluno[str(chave_aluno)] = item

    plantas_por_aluno = _canteiros_por_aluno(canteiros)

    for aluno in alunos:
        entrega = aluno.get("entrega") or entregas_por_aluno.get(str(aluno.get("id")))
        if isinstance(entrega, dict):
            aluno["entrega"] = entrega
            bruto = entrega.get("submittedAt") or entrega.get("deliveredAt") or entrega.get("createdAt")
            if bruto:
                dt = parse_datetime(str(bruto))
                if dt is not None:
                    if timezone.is_naive(dt):
                        dt = timezone.make_aware(dt, timezone.utc)
                    entrega["data_local"] = timezone.localtime(dt)

        aluno["planta_canteiro"] = "; ".join(plantas_por_aluno.get(str(aluno.get("id")), []))

    return render(request, "professor/turma_detalhe.html", {
        "usuario": request.usuario,
        "turma": turma,
        "turma_id": turma_id,
        "codigos": codigos,
        "alunos": alunos,
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