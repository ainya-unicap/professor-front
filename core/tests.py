from unittest.mock import patch

import requests
from django.test import TestCase
from django.urls import reverse

from .api import ErroAPI, ErroValidacao, autenticar, cadastrar
from .sessao import CHAVE_SESSAO

RESPOSTA_PROFESSOR = {
    "access": "token-access",
    "refresh": "token-refresh",
    "usuario": {
        "id": 1,
        "nome": "Maria Lima",
        "email": "prof@teste.com",
        "matricula": "0000015638",
        "papel": "professor",
    },
}


class TelaLoginTests(TestCase):
    def setUp(self):
        self.url = reverse("core:login")

    def enviar(self, email="prof@teste.com", senha="Senha123!x"):
        return self.client.post(self.url, {"email": email, "senha": senha})

    def test_exibe_a_tela_de_login(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "auth/login.html")
        self.assertContains(resposta, "Fazer login")
        self.assertContains(resposta, 'name="email"')
        self.assertContains(resposta, 'name="senha"')

    def test_raiz_redireciona_para_login(self):
        resposta = self.client.get("/")
        self.assertRedirects(resposta, self.url)

    def test_campos_vazios_mostram_erros(self):
        resposta = self.enviar(email="", senha="")
        self.assertContains(resposta, "Informe seu e-mail.")
        self.assertContains(resposta, "Informe sua senha.")

    def test_email_invalido_mostra_erro(self):
        resposta = self.enviar(email="nao-e-email")
        self.assertContains(resposta, "Informe um e-mail válido.")

    @patch("core.views.autenticar")
    def test_credenciais_erradas_mostram_mensagem(self, autenticar_mock):
        autenticar_mock.side_effect = ErroAPI("E-mail ou senha inválidos.", status=401)
        resposta = self.enviar(senha="errada")
        self.assertContains(resposta, "E-mail ou senha inválidos.")
        self.assertNotIn(CHAVE_SESSAO, self.client.session)

    @patch("core.views.autenticar")
    def test_aluno_nao_entra_na_area_do_professor(self, autenticar_mock):
        dados = {**RESPOSTA_PROFESSOR, "usuario": {**RESPOSTA_PROFESSOR["usuario"], "papel": "aluno"}}
        autenticar_mock.return_value = dados
        resposta = self.enviar()
        self.assertContains(resposta, "Este acesso é exclusivo para professores.")
        self.assertNotIn(CHAVE_SESSAO, self.client.session)

    @patch("core.views.autenticar")
    def test_professor_entra_e_vai_para_o_painel(self, autenticar_mock):
        autenticar_mock.return_value = RESPOSTA_PROFESSOR
        resposta = self.enviar()
        self.assertRedirects(resposta, reverse("professor:painel"))
        self.assertEqual(self.client.session[CHAVE_SESSAO]["usuario"]["nome"], "Maria Lima")
        autenticar_mock.assert_called_once_with("prof@teste.com", "Senha123!x")

    @patch("core.views.autenticar")
    def test_professor_logado_e_redirecionado_ao_abrir_login(self, autenticar_mock):
        autenticar_mock.return_value = RESPOSTA_PROFESSOR
        self.enviar()
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, reverse("professor:painel"))

    @patch("core.views.autenticar")
    def test_logout_encerra_a_sessao(self, autenticar_mock):
        autenticar_mock.return_value = RESPOSTA_PROFESSOR
        self.enviar()
        resposta = self.client.post(reverse("core:logout"))
        self.assertRedirects(resposta, self.url)
        self.assertNotIn(CHAVE_SESSAO, self.client.session)

    def test_link_para_cadastro(self):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, f'href="{reverse("core:cadastro")}"')

    def test_painel_sem_login_volta_para_login(self):
        resposta = self.client.get(reverse("professor:painel"))
        self.assertRedirects(resposta, self.url)


class ClienteAPITests(TestCase):
    def test_ignora_proxy_do_sistema(self):
        from .api import _sessao

        self.assertFalse(_sessao.trust_env)

    @patch("core.api._sessao.request")
    def test_api_fora_do_ar(self, post_mock):
        post_mock.side_effect = requests.ConnectionError()
        with self.assertLogs("core.api", level="WARNING"):
            with self.assertRaisesMessage(ErroAPI, "Não foi possível conectar ao servidor"):
                autenticar("prof@teste.com", "x")

    @patch("core.api._sessao.request")
    def test_api_responde_401(self, post_mock):
        post_mock.return_value.status_code = 401
        post_mock.return_value.ok = False
        with self.assertRaisesMessage(ErroAPI, "E-mail ou senha inválidos."):
            autenticar("prof@teste.com", "x")

    @patch("core.api._sessao.request")
    def test_api_responde_200(self, post_mock):
        post_mock.return_value.status_code = 200
        post_mock.return_value.ok = True
        post_mock.return_value.json.return_value = RESPOSTA_PROFESSOR
        self.assertEqual(autenticar("prof@teste.com", "x"), RESPOSTA_PROFESSOR)
        self.assertEqual(post_mock.call_args.kwargs["json"], {"email": "prof@teste.com", "password": "x"})


class TelaCadastroTests(TestCase):
    def setUp(self):
        self.url = reverse("core:cadastro")
        self.dados = {
            "nome": "Maria Lima",
            "email": "prof@teste.com",
            "senha": "canteiro-forte-2026",
            "confirmar_senha": "canteiro-forte-2026",
        }

    def test_exibe_a_tela_de_cadastro(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "auth/cadastro.html")
        self.assertContains(resposta, "Criar conta")
        for campo in ("nome", "email", "senha", "confirmar_senha"):
            self.assertContains(resposta, f'name="{campo}"')
        self.assertContains(resposta, f'href="{reverse("core:login")}"')

    def test_campos_vazios_mostram_erros(self):
        resposta = self.client.post(self.url, {})
        self.assertContains(resposta, "Informe seu nome completo.")
        self.assertContains(resposta, "Informe seu e-mail.")
        self.assertContains(resposta, "Crie uma senha.")
        self.assertContains(resposta, "Confirme sua senha.")

    @patch("core.views.cadastrar")
    def test_senhas_diferentes_nao_chamam_a_api(self, cadastrar_mock):
        resposta = self.client.post(self.url, {**self.dados, "confirmar_senha": "outra"})
        self.assertContains(resposta, "As senhas não conferem.")
        cadastrar_mock.assert_not_called()

    @patch("core.views.cadastrar")
    def test_cadastro_ok_loga_e_vai_para_o_painel(self, cadastrar_mock):
        cadastrar_mock.return_value = RESPOSTA_PROFESSOR
        resposta = self.client.post(self.url, self.dados)
        self.assertRedirects(resposta, reverse("professor:painel"))
        self.assertEqual(self.client.session[CHAVE_SESSAO]["usuario"]["nome"], "Maria Lima")
        cadastrar_mock.assert_called_once_with("Maria Lima", "prof@teste.com", "canteiro-forte-2026")

    @patch("core.views.cadastrar")
    def test_erros_da_api_aparecem_nos_campos(self, cadastrar_mock):
        cadastrar_mock.side_effect = ErroValidacao(
            {
                "email": ["Já existe uma conta com este e-mail."],
                "password": ["Esta senha é muito comum."],
            }
        )
        resposta = self.client.post(self.url, self.dados)
        self.assertContains(resposta, "Já existe uma conta com este e-mail.")
        self.assertContains(resposta, "Esta senha é muito comum.")
        self.assertNotIn(CHAVE_SESSAO, self.client.session)

    @patch("core.views.cadastrar")
    def test_erro_geral_da_api_aparece_no_alerta(self, cadastrar_mock):
        cadastrar_mock.side_effect = ErroValidacao({"non_field_errors": ["Cadastro indisponível."]})
        resposta = self.client.post(self.url, self.dados)
        self.assertContains(resposta, "Cadastro indisponível.")

    @patch("core.views.cadastrar")
    def test_api_fora_do_ar(self, cadastrar_mock):
        cadastrar_mock.side_effect = ErroAPI("Não foi possível conectar ao servidor. Tente novamente.")
        resposta = self.client.post(self.url, self.dados)
        self.assertContains(resposta, "Não foi possível conectar ao servidor")


class ClienteAPICadastroTests(TestCase):
    @patch("core.api._sessao.request")
    def test_envia_os_campos_esperados(self, post_mock):
        post_mock.return_value.status_code = 201
        post_mock.return_value.ok = True
        post_mock.return_value.json.return_value = RESPOSTA_PROFESSOR
        self.assertEqual(cadastrar("Maria Lima", "prof@teste.com", "x"), RESPOSTA_PROFESSOR)
        self.assertEqual(
            post_mock.call_args.kwargs["json"],
            {"nome": "Maria Lima", "email": "prof@teste.com", "password": "x"},
        )

    @patch("core.api._sessao.request")
    def test_400_vira_erro_de_validacao(self, post_mock):
        post_mock.return_value.status_code = 400
        post_mock.return_value.ok = False
        post_mock.return_value.json.return_value = {"email": ["Já existe uma conta com este e-mail."]}
        with self.assertRaises(ErroValidacao) as ctx:
            cadastrar("Maria Lima", "prof@teste.com", "x")
        self.assertEqual(ctx.exception.erros, {"email": ["Já existe uma conta com este e-mail."]})
