from datetime import date

STATUS_ALUNO = {
    "entregue": ("Aguardando correção", "pendente"),
    "corrigido": ("Corrigido", "corrigido"),
    "sem_relatorio": ("Sem relatório", "sem-relatorio"),
}

LIMITE_ALUNOS_VISIVEIS = 4


def data(valor):
    return date.fromisoformat(valor) if valor else None


def preparar_alunos(alunos):
    preparados = []
    for posicao, aluno in enumerate(alunos):
        rotulo, classe = STATUS_ALUNO[aluno["status"]]
        preparados.append(
            {
                **aluno,
                "status_rotulo": rotulo,
                "status_classe": classe,
                "oculto": posicao >= LIMITE_ALUNOS_VISIVEIS,
            }
        )
    return preparados


def secoes_relatorio(relatorio):
    return [
        {"numero": 1, "titulo": "Introdução", "texto": relatorio["introducao"]},
        {"numero": 2, "titulo": "Objetivo", "texto": relatorio["objetivo"]},
        {"numero": 3, "titulo": "Desenvolvimento", "texto": relatorio["desenvolvimento"], "fotos": True},
        {"numero": 4, "titulo": "Conclusão", "texto": relatorio["conclusao"]},
        {"numero": 5, "titulo": "Referências", "texto": relatorio["referencias"]},
    ]


def nota_para_exibir(nota):
    if nota in (None, ""):
        return ""
    texto = f"{float(nota):.2f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")
