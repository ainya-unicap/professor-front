from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone


def periodo_atual():
    hoje = timezone.localdate()
    return f"{hoje.year}.{1 if hoje.month <= 6 else 2}"


class NovaTurmaForm(forms.Form):
    CAMPOS_API = {"nome": "nome", "periodo": "periodo", "instituicao": "instituicao"}

    nome = forms.CharField(
        label="Nome da turma",
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Ex: Turma C", "autocomplete": "off"}),
        error_messages={"required": "Informe o nome da turma."},
    )
    periodo = forms.CharField(
        label="Período",
        max_length=6,
        validators=[RegexValidator(r"^\d{4}\.[12]$", "Use o formato ano.semestre, por exemplo 2026.1.")],
        widget=forms.TextInput(attrs={"placeholder": "2026.1", "autocomplete": "off", "inputmode": "decimal"}),
        error_messages={"required": "Informe o período."},
    )
    instituicao = forms.CharField(
        label="Instituição",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Instituição", "autocomplete": "organization"}),
        error_messages={"required": "Informe a instituição."},
    )

    def aplicar_erros_api(self, erros):
        restantes = []
        for campo_api, mensagens in erros.items():
            if isinstance(mensagens, str):
                mensagens = [mensagens]
            campo = self.CAMPOS_API.get(campo_api)
            if campo:
                for mensagem in mensagens:
                    self.add_error(campo, mensagem)
            else:
                restantes.extend(mensagens)
        return restantes
