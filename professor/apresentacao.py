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
