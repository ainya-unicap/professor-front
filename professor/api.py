from core.api import requisicao


def listar_turmas(token):
    return requisicao("GET", "professores/turmas", token=token)


def criar_turma(token, nome, period_id, institution_id=None):
    dados = {"name": nome, "period_id": period_id}
    if institution_id:
        dados["institution_id"] = institution_id
    return requisicao("POST", "professores/turmas", token=token, json=dados)


def apagar_turma(token, turma_id):
    return requisicao("DELETE", f"professores/turmas/{turma_id}", token=token)


def listar_codigos(token, turma_id):
    return requisicao("GET", f"professores/turmas/{turma_id}/codigos", token=token)


def gerar_codigo(token, turma_id):
    return requisicao("POST", f"professores/turmas/{turma_id}/codigos", token=token)


def apagar_codigo(token, turma_id, codigo_id):
    return requisicao("DELETE", f"professores/turmas/{turma_id}/codigos/{codigo_id}", token=token)


def listar_entregas(token, turma_id):
    return requisicao("GET", f"professores/turmas/{turma_id}/entregas", token=token)
