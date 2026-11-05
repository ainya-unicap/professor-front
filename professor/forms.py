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


class CampoData(forms.DateInput):
    input_type = "date"

    def format_value(self, value):
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value


class PrazosForm(forms.Form):
    CAMPOS_API = {
        "inicio_registros": "inicio_registros",
        "encerramento_registros": "encerramento_registros",
        "limite_entrega": "limite_entrega",
        "prazo_correcao": "prazo_correcao",
        "aceitar_atrasadas": "aceitar_atrasadas",
    }
    ETAPAS = [
        ("inicio_registros", "Início dos registros", "O aluno já pode criar registros semanais."),
        (
            "encerramento_registros",
            "Encerramento dos registros",
            "A partir daqui o aluno pode gerar e submeter o relatório. Antes disso o envio fica bloqueado.",
        ),
        ("limite_entrega", "Limite de entrega", "Depois desta data o relatório é marcado como atrasado."),
        ("prazo_correcao", "Prazo de correção", "Só você vê: aparece como lembrete no painel."),
    ]

    inicio_registros = forms.DateField(label="Início dos registros", required=False, widget=CampoData())
    encerramento_registros = forms.DateField(label="Encerramento dos registros", required=False, widget=CampoData())
    limite_entrega = forms.DateField(label="Limite de entrega", required=False, widget=CampoData())
    prazo_correcao = forms.DateField(label="Prazo de correção", required=False, widget=CampoData())
    aceitar_atrasadas = forms.BooleanField(label="Aceitar entregas após o limite", required=False)

    def etapas(self):
        return [
            {"numero": i, "campo": self[campo], "titulo": titulo, "descricao": descricao}
            for i, (campo, titulo, descricao) in enumerate(self.ETAPAS, start=1)
        ]

    def clean(self):
        dados = super().clean()
        anterior = None
        for campo, titulo, _ in self.ETAPAS:
            valor = dados.get(campo)
            if not valor:
                continue
            if anterior and valor < anterior[1]:
                self.add_error(campo, f"{titulo} não pode ser antes de: {anterior[0].lower()}.")
            anterior = (titulo, valor)
        return dados

    def para_api(self):
        dados = self.cleaned_data
        return {
            campo: (dados[campo].isoformat() if dados.get(campo) else None)
            for campo, _, _ in self.ETAPAS
        } | {"aceitar_atrasadas": dados["aceitar_atrasadas"]}

    aplicar_erros_api = NovaTurmaForm.aplicar_erros_api


class AvaliacaoForm(forms.Form):
    CAMPOS_API = {"nota": "nota", "feedback": "feedback"}

    nota = forms.CharField(
        label="Nota (0 a 10)",
        required=False,
        max_length=5,
        widget=forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off", "placeholder": "Ex: 8,5"}),
    )
    feedback = forms.CharField(
        label="Feedback para o aluno",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    def __init__(self, *args, concluir=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.concluir = concluir

    def clean_nota(self):
        valor = self.cleaned_data["nota"].strip().replace(",", ".")
        if not valor:
            if self.concluir:
                raise forms.ValidationError("Informe a nota para marcar como corrigido.")
            return None
        try:
            nota = float(valor)
        except ValueError:
            raise forms.ValidationError("Informe um número, por exemplo 8,5.")
        if not 0 <= nota <= 10:
            raise forms.ValidationError("A nota vai de 0 a 10.")
        return valor

    aplicar_erros_api = NovaTurmaForm.aplicar_erros_api
