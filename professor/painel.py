from datetime import date

from django.utils import timezone

DIAS_ENCERRA_EM_BREVE = 7


def _data(valor):
    return date.fromisoformat(valor) if valor else None


def _plural(quantidade, singular, plural):
    return singular if quantidade == 1 else plural


def preparar_turmas(turmas):
    preparadas = []
    for turma in turmas:
        alunos = turma["alunos"]
        entregues = turma["relatorios_entregues"]
        preparadas.append(
            {
                **turma,
                "alunos_legenda": f"{alunos} {_plural(alunos, 'aluno', 'alunos')}",
                "progresso": round(entregues * 100 / alunos) if alunos else 0,
                "entregues_legenda": f"{entregues} de {alunos} {_plural(alunos, 'relatório entregue', 'relatórios entregues')}",
            }
        )
    return preparadas


def montar_painel(dados):
    resumo = dados["resumo"]
    pendentes = resumo["aguardando_correcao"]
    turmas_pendentes = resumo["turmas_com_pendencia"]
    prazo = _data(resumo["prazo_avaliacao"])
    dias_ate_prazo = (prazo - timezone.localdate()).days if prazo else None

    if prazo is None:
        prazo_legenda = "Sem prazo definido"
    elif dias_ate_prazo <= DIAS_ENCERRA_EM_BREVE:
        prazo_legenda = "Encerra em breve"
    else:
        prazo_legenda = f"Em {dias_ate_prazo} dias"

    if pendentes:
        resumo_pendentes = f"{pendentes} {_plural(pendentes, 'relatório aguarda', 'relatórios aguardam')} correção"
    else:
        resumo_pendentes = "Nenhum relatório aguardando correção"

    turmas = preparar_turmas(dados["turmas"])

    return {
        "periodo_atual": dados["periodo_atual"],
        "instituicao": dados["instituicao"],
        "pendentes": pendentes,
        "resumo_pendentes": resumo_pendentes,
        "turmas_pendentes_legenda": (
            f"{turmas_pendentes} {_plural(turmas_pendentes, 'Turma', 'Turmas')}" if turmas_pendentes else "Tudo em dia"
        ),
        "turmas_ativas": resumo["turmas_ativas"],
        "alunos": resumo["alunos"],
        "prazo": prazo,
        "prazo_legenda": prazo_legenda,
        "turmas": turmas,
        "aguardando": dados["aguardando"],
    }
