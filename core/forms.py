from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
        error_messages={"required": "Informe seu e-mail.", "invalid": "Informe um e-mail válido."},
    )
    senha = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        error_messages={"required": "Informe sua senha."},
    )
    recaptcha_token = forms.CharField(required=False, widget=forms.HiddenInput())


class CadastroForm(forms.Form):
    CODIGO_PARA_CAMPO = {
        "EMAIL_INVALIDO": "email",
        "EMAIL_JA_CADASTRADO": "email",
        "SENHAS_DIFERENTES": "confirmar_senha",
    }

    nome = forms.CharField(
        label="Nome Completo",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "name", "autofocus": True}),
        error_messages={"required": "Informe seu nome completo."},
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
        error_messages={"required": "Informe seu e-mail.", "invalid": "Informe um e-mail válido."},
    )
    senha = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        error_messages={"required": "Crie uma senha."},
    )
    confirmar_senha = forms.CharField(
        label="Confirmar senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        error_messages={"required": "Confirme sua senha."},
    )
    recaptcha_token = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean(self):
        dados = super().clean()
        senha = dados.get("senha")
        confirmacao = dados.get("confirmar_senha")
        if senha and confirmacao and senha != confirmacao:
            self.add_error("confirmar_senha", "As senhas não conferem.")
        return dados

    def aplicar_erro_api(self, erro):
        """Tenta destacar o campo certo; devolve a mensagem para exibir solta se não der."""
        campo = self.CODIGO_PARA_CAMPO.get(erro.codigo)
        if campo:
            self.add_error(campo, erro.mensagem)
            return None
        return erro.mensagem
