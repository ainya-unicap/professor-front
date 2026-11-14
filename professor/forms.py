from django import forms


class TurmaForm(forms.Form):
    CODIGO_PARA_CAMPO = {
        "PERIODO_INVALIDO": "period_id",
        "INSTITUICAO_INVALIDA": "institution_id",
    }

    name = forms.CharField(
        label="Nome da turma",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Agronomia 2026.1 - Turma A"}),
        error_messages={"required": "Informe o nome da turma."},
    )
    period_id = forms.ChoiceField(
        label="Período letivo",
        error_messages={"required": "Selecione o período letivo.", "invalid_choice": "Período letivo inválido."},
    )
    institution_id = forms.ChoiceField(label="Instituição (opcional)", required=False)

    def __init__(self, *args, periodos=(), instituicoes=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["period_id"].choices = [(p["id"], p["name"]) for p in periodos]
        self.fields["institution_id"].choices = [("", "—")] + [
            (i["id"], f'{i["name"]} ({i["abbreviation"]})') for i in instituicoes
        ]

    def aplicar_erro_api(self, erro):
        if erro.campos:
            for campo, mensagem in erro.campos.items():
                if campo in self.fields:
                    self.add_error(campo, mensagem)
                else:
                    return mensagem
            return None

        campo = self.CODIGO_PARA_CAMPO.get(erro.codigo)
        if campo:
            self.add_error(campo, erro.mensagem)
            return None
        return erro.mensagem
