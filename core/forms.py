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


class CadastroForm(forms.Form):
    CAMPOS_API = {"nome": "nome", "email": "email", "password": "senha"}

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

    def clean(self):
        dados = super().clean()
        senha = dados.get("senha")
        confirmacao = dados.get("confirmar_senha")
        if senha and confirmacao and senha != confirmacao:
            self.add_error("confirmar_senha", "As senhas não conferem.")
        return dados

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
