from django import forms

SEMESTRES = [("PRIMEIRO", "1º semestre"), ("SEGUNDO", "2º semestre")]


class TurmaForm(forms.Form):
    CODIGO_PARA_CAMPO = {
        "PERIODO_INVALIDO": "period_nome",
        "INSTITUICAO_INVALIDA": "institution_nome",
    }

    name = forms.CharField(
        label="Nome da turma",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Agronomia 2026.1 - Turma A"}),
        error_messages={"required": "Informe o nome da turma."},
    )

    period_nome = forms.CharField(
        label="Período letivo",
        widget=forms.TextInput(attrs={
            "placeholder": "2026.1",
            "list": "lista-periodos",
            "autocomplete": "off",
        }),
        error_messages={"required": "Informe o período letivo."},
    )
    period_novo = forms.BooleanField(
        label="Não encontrei o período letivo na lista — quero cadastrar um novo",
        required=False,
    )
    period_semestre = forms.ChoiceField(
        label="Semestre",
        choices=SEMESTRES,
        required=False,
    )
    period_inicio = forms.DateField(
        label="Início do período",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    period_fim = forms.DateField(
        label="Fim do período",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )

    institution_nome = forms.CharField(
        label="Instituição",
        widget=forms.TextInput(attrs={
            "placeholder": "UFRPE",
            "list": "lista-instituicoes",
            "autocomplete": "off",
        }),
        error_messages={"required": "Informe a instituição."},
    )
    institution_novo = forms.BooleanField(
        label="Não encontrei a instituição na lista — quero cadastrar uma nova",
        required=False,
    )
    institution_sigla = forms.CharField(
        label="Sigla da instituição",
        max_length=20,
        required=False,
    )

    def __init__(self, *args, periodos=(), instituicoes=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.periodos = periodos
        self.instituicoes = instituicoes
        self.periodo_novo = None
        self.instituicao_nova = None

    @staticmethod
    def _buscar(valor, opcoes):
        valor = valor.strip().lower()
        for item in opcoes:
            if item["name"].strip().lower() == valor:
                return item["id"]
            if item.get("abbreviation", "").strip().lower() == valor:
                return item["id"]
        return None

    def _limpar_periodo(self, cleaned):
        nome = cleaned.get("period_nome")
        if not nome:
            return

        if not cleaned.get("period_novo"):
            period_id = self._buscar(nome, self.periodos)
            if period_id:
                cleaned["period_id"] = period_id
            else:
                self.add_error(
                    "period_nome",
                    "Não encontrado. Marque a opção de cadastrar um período novo.",
                )
            return

        faltando = {
            "period_semestre": cleaned.get("period_semestre"),
            "period_inicio": cleaned.get("period_inicio"),
            "period_fim": cleaned.get("period_fim"),
        }
        for campo, valor in faltando.items():
            if not valor:
                self.add_error(campo, "Obrigatório para criar um período novo.")
        if all(faltando.values()):
            self.periodo_novo = {
                "nome": nome.strip(),
                "semestre": faltando["period_semestre"],
                "data_inicio": faltando["period_inicio"],
                "data_fim": faltando["period_fim"],
            }

    def _limpar_instituicao(self, cleaned):
        nome = cleaned.get("institution_nome")
        if not nome:
            return

        if not cleaned.get("institution_novo"):
            institution_id = self._buscar(nome, self.instituicoes)
            if institution_id:
                cleaned["institution_id"] = institution_id
            else:
                self.add_error(
                    "institution_nome",
                    "Não encontrada. Marque a opção de cadastrar uma instituição nova.",
                )
            return

        sigla = cleaned.get("institution_sigla")
        if not sigla:
            self.add_error("institution_sigla", "Obrigatório para cadastrar uma instituição nova.")
        else:
            self.instituicao_nova = {"nome": nome.strip(), "sigla": sigla.strip()}

    def clean(self):
        cleaned = super().clean()
        self._limpar_periodo(cleaned)
        self._limpar_instituicao(cleaned)
        return cleaned

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
