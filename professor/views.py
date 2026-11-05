from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.api import (
    ErroAPI,
    ErroValidacao,
    baixar_arquivo,
    buscar_painel,
    buscar_relatorio,
    buscar_turma,
    contar_pendentes,
    criar_turma,
    gerar_novo_codigo,
    listar_relatorios_da_turma,
    listar_turmas,
    salvar_avaliacao,
    salvar_prazos,
)
from core.sessao import professor_obrigatorio

from .apresentacao import data, nota_para_exibir, preparar_alunos, secoes_relatorio
from .forms import AvaliacaoForm, NovaTurmaForm, PrazosForm, periodo_atual
from .painel import montar_painel, preparar_turmas


def _contexto_base(request, secao, pendentes=None):
    if pendentes is None:
        pendentes = contar_pendentes(request)
    return {"secao": secao, "usuario": request.usuario, "pendentes": pendentes}


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

    contexto = _contexto_base(request, "painel", pendentes=painel["pendentes"] if painel else 0)
    contexto.update(
        {
            "primeiro_nome": request.usuario["nome"].split()[0],
            "painel": painel,
            "erro": erro,
            "form": form or _form_vazio(painel),
            "abrir_modal": abrir_modal,
            "erro_modal": erro_modal,
        }
    )
    return render(request, "professor/painel.html", contexto)


@professor_obrigatorio
def painel(request):
    return _render_painel(request)


@professor_obrigatorio
@require_http_methods(["GET", "POST"])
def nova_turma(request):
    if request.method == "GET":
        return _render_painel(request, abrir_modal=True)

    form = NovaTurmaForm(request.POST)
    origem = request.POST.get("origem")
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
            return redirect("professor:turma", turma_id=turma["id"])

    if origem == "turmas":
        return _render_turmas(request, form=form, abrir_modal=True, erro_modal=erro_modal)
    return _render_painel(request, form=form, abrir_modal=True, erro_modal=erro_modal)


def _render_turmas(request, form=None, abrir_modal=False, erro_modal=None):
    turmas = listar_turmas(request)
    recente = turmas[0] if turmas else None
    contexto = _contexto_base(request, "turmas")
    contexto.update(
        {
            "primeiro_nome": request.usuario["nome"].split()[0],
            "turmas": preparar_turmas(turmas),
            "form": form
            or NovaTurmaForm(
                initial={
                    "periodo": recente["periodo"] if recente else periodo_atual(),
                    "instituicao": recente["instituicao"] if recente else "",
                }
            ),
            "abrir_modal": abrir_modal,
            "erro_modal": erro_modal,
            "origem_modal": "turmas",
        }
    )
    return render(request, "professor/turmas.html", contexto)


@professor_obrigatorio
@require_GET
def turmas(request):
    return _render_turmas(request)


@professor_obrigatorio
@require_GET
def correcoes(request):
    turmas = listar_turmas(request)
    if not turmas:
        messages.info(request, "Crie uma turma para começar a receber relatórios.")
        return redirect("professor:turmas")
    escolhida = max(turmas, key=lambda t: t["aguardando_correcao"])
    if not escolhida["aguardando_correcao"]:
        escolhida = turmas[0]
    return redirect("professor:turma_correcoes", turma_id=escolhida["id"])


@professor_obrigatorio
@require_GET
def turma_correcoes(request, turma_id):
    turma = buscar_turma(request, turma_id)
    relatorios = [
        {**relatorio, "entregue_em_data": data(relatorio["entregue_em"][:10]) if relatorio["entregue_em"] else None}
        for relatorio in listar_relatorios_da_turma(request, turma_id)
    ]
    contexto = _contexto_base(request, "correcoes")
    contexto.update(
        {
            "turma": turma,
            "relatorios": relatorios,
            "outras_turmas": [t for t in listar_turmas(request) if t["id"] != turma["id"]],
        }
    )
    return render(request, "professor/correcoes.html", contexto)


def _render_turma(request, turma_id, form=None, erro=None):
    turma = buscar_turma(request, turma_id)
    if form is None:
        form = PrazosForm(
            initial={
                "inicio_registros": turma["inicio_registros"],
                "encerramento_registros": turma["encerramento_registros"],
                "limite_entrega": turma["limite_entrega"],
                "prazo_correcao": turma["prazo_correcao"],
                "aceitar_atrasadas": turma["aceitar_atrasadas"],
            }
        )
    alunos = preparar_alunos(turma["alunos_lista"])
    contexto = _contexto_base(request, "turmas")
    contexto.update(
        {
            "turma": turma,
            "form": form,
            "erro": erro,
            "alunos": alunos,
            "tem_ocultos": any(aluno["oculto"] for aluno in alunos),
        }
    )
    return render(request, "professor/turma.html", contexto)


@professor_obrigatorio
@require_GET
def turma(request, turma_id):
    return _render_turma(request, turma_id)


@professor_obrigatorio
@require_POST
def turma_prazos(request, turma_id):
    form = PrazosForm(request.POST)
    erro = None
    if form.is_valid():
        try:
            salvar_prazos(request, turma_id, form.para_api())
        except ErroValidacao as e:
            erro = " ".join(form.aplicar_erros_api(e.erros)) or None
        except ErroAPI as e:
            if e.status in (401, 404):
                raise
            erro = e.mensagem
        else:
            messages.success(request, "Prazos salvos.")
            return redirect(reverse("professor:turma", args=[turma_id]) + "#prazos")
    return _render_turma(request, turma_id, form=form, erro=erro)


@professor_obrigatorio
@require_POST
def turma_novo_codigo(request, turma_id):
    try:
        novo = gerar_novo_codigo(request, turma_id)
    except ErroAPI as e:
        if e.status in (401, 404):
            raise
        messages.error(request, e.mensagem)
    else:
        messages.success(
            request,
            f"Novo código gerado: {novo['codigo_convite']}. O link e o código anteriores não funcionam mais.",
        )
    return redirect(reverse("professor:turma", args=[turma_id]) + "#convite")


def _render_correcao(request, relatorio_id, form=None, erro=None):
    relatorio = buscar_relatorio(request, relatorio_id)
    if form is None:
        form = AvaliacaoForm(
            initial={"nota": nota_para_exibir(relatorio["nota"]), "feedback": relatorio["feedback"]}
        )
    contexto = _contexto_base(request, "correcoes")
    contexto.update(
        {
            "relatorio": relatorio,
            "secoes": secoes_relatorio(relatorio),
            "prazo_correcao": data(relatorio["turma"]["prazo_correcao"]),
            "form": form,
            "erro": erro,
        }
    )
    return render(request, "professor/correcao.html", contexto)


@professor_obrigatorio
@require_GET
def correcao(request, relatorio_id):
    return _render_correcao(request, relatorio_id)


@professor_obrigatorio
@require_POST
def correcao_avaliar(request, relatorio_id):
    concluir = request.POST.get("acao") == "corrigir"
    form = AvaliacaoForm(request.POST, concluir=concluir)
    erro = None
    if form.is_valid():
        try:
            relatorio = salvar_avaliacao(
                request,
                relatorio_id,
                form.cleaned_data["nota"],
                form.cleaned_data["feedback"],
                concluir,
            )
        except ErroValidacao as e:
            erro = " ".join(form.aplicar_erros_api(e.erros)) or None
        except ErroAPI as e:
            if e.status in (401, 404):
                raise
            erro = e.mensagem
        else:
            if concluir:
                messages.success(request, f"Relatório de {relatorio['aluno']['nome']} marcado como corrigido.")
            else:
                messages.success(request, "Avaliação salva. O relatório continua aguardando correção.")
            return redirect("professor:correcao", relatorio_id=relatorio_id)
    return _render_correcao(request, relatorio_id, form=form, erro=erro)


def _repassar_arquivo(resposta, cabecalho_padrao=None):
    saida = HttpResponse(resposta.content, content_type=resposta.headers.get("Content-Type", "application/octet-stream"))
    disposicao = resposta.headers.get("Content-Disposition") or cabecalho_padrao
    if disposicao:
        saida["Content-Disposition"] = disposicao
    saida["Cache-Control"] = "private, max-age=300"
    return saida


@professor_obrigatorio
@require_GET
def correcao_pdf(request, relatorio_id):
    return _repassar_arquivo(baixar_arquivo(request, f"relatorios/{relatorio_id}/pdf/"))


@professor_obrigatorio
@require_GET
def correcao_foto(request, relatorio_id, foto_id):
    return _repassar_arquivo(baixar_arquivo(request, f"relatorios/{relatorio_id}/fotos/{foto_id}/"), "inline")
