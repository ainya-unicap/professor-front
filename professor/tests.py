from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from core.api import ErroAPI, ErroValidacao, SessaoExpirada
from core.sessao import CHAVE_SESSAO

USUARIO = {
    "id": 1,
    "nome": "Maria Lima",
    "email": "prof@teste.com",
    "matricula": "0000015638",
    "papel": "professor",
}

TURMA = {
    "id": 1,
    "nome": "Turma A",
    "periodo": "2026.1",
    "instituicao": "UNICAP",
    "codigo_convite": "K7MPQ3",
    "link_convite": "https://alunos.exemplo/convite/K7MPQ3",
    "ativa": True,
    "alunos": 18,
    "relatorios_entregues": 13,
}

LISTA_TURMAS = [
    TURMA,
    {**TURMA, "id": 2, "nome": "Turma B", "alunos": 0, "relatorios_entregues": 0, "codigo_convite": "XYZ789"},
]


class Logado(TestCase):
    def setUp(self):
        sessao = self.client.session
        sessao[CHAVE_SESSAO] = {"access": "a", "refresh": "r", "usuario": USUARIO}
        sessao.save()


class TurmasTests(Logado):
    url = reverse("professor:turmas")

    @patch("professor.views.listar_turmas", return_value=LISTA_TURMAS)
    def test_lista_as_turmas(self, _):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "professor/turmas.html")
        for texto in (
            "Olá, Maria",
            "Gerencie alunos, convites e relatórios.",
            "Turma A",
            "2026.1 · 18 alunos",
            "13 de 18 relatórios entregues",
            "width: 72%",
            "0 de 0 relatórios entregues",
            "Maria Lima",
            "0000015638",
            'id="modal-nova-turma"',
        ):
            self.assertContains(resposta, texto)
        self.assertContains(resposta, "menu__item menu__item--ativo", count=1)
        self.assertNotContains(resposta, "data-abrir>")

    @patch("professor.views.listar_turmas", return_value=[])
    def test_sem_turmas(self, _):
        self.assertContains(self.client.get(self.url), "Você ainda não tem turmas.")

    @patch("professor.views.listar_turmas")
    def test_api_fora_do_ar(self, listar_mock):
        listar_mock.side_effect = ErroAPI("Não foi possível conectar ao servidor. Tente novamente.")
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Não foi possível conectar ao servidor")

    @patch("professor.views.listar_turmas")
    def test_sessao_expirada_volta_para_o_login(self, listar_mock):
        listar_mock.side_effect = SessaoExpirada()
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, reverse("core:login"), fetch_redirect_response=False)
        self.assertNotIn(CHAVE_SESSAO, self.client.session)
        self.assertContains(self.client.get(reverse("core:login")), "Sua sessão expirou")

    def test_sem_login_volta_para_o_login(self):
        self.client.session.flush()
        self.client.cookies.clear()
        self.assertRedirects(self.client.get(self.url), reverse("core:login"))


@patch("professor.views.listar_turmas", return_value=LISTA_TURMAS)
class NovaTurmaTests(Logado):
    url = reverse("professor:nova_turma")
    dados = {"nome": "Turma C", "periodo": "2026.1", "instituicao": "UNICAP"}

    def test_get_abre_o_modal_preenchido(self, _):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "data-abrir")
        self.assertContains(resposta, 'value="2026.1"')
        self.assertContains(resposta, 'value="UNICAP"')

    @patch("professor.views.criar_turma")
    def test_cria_turma_e_mostra_o_codigo(self, criar_mock, _):
        criar_mock.return_value = {**TURMA, "id": 3, "nome": "Turma C", "codigo_convite": "QW3RTY"}
        resposta = self.client.post(self.url, self.dados)
        self.assertRedirects(resposta, reverse("professor:turmas"), fetch_redirect_response=False)
        self.assertEqual(criar_mock.call_args.args[1:], ("Turma C", "2026.1", "UNICAP"))
        self.assertContains(self.client.get(reverse("professor:turmas")), "Código de convite: QW3RTY")

    @patch("professor.views.criar_turma")
    def test_campos_vazios(self, criar_mock, _):
        resposta = self.client.post(self.url, {})
        for texto in ("Informe o nome da turma.", "Informe o período.", "Informe a instituição.", "data-abrir"):
            self.assertContains(resposta, texto)
        criar_mock.assert_not_called()

    @patch("professor.views.criar_turma")
    def test_periodo_em_formato_errado(self, criar_mock, _):
        resposta = self.client.post(self.url, {**self.dados, "periodo": "2026/1"})
        self.assertContains(resposta, "Use o formato ano.semestre")
        criar_mock.assert_not_called()

    @patch("professor.views.criar_turma")
    def test_erros_da_api_aparecem_no_campo(self, criar_mock, _):
        criar_mock.side_effect = ErroValidacao({"nome": ["Você já tem uma turma com esse nome neste período."]})
        resposta = self.client.post(self.url, self.dados)
        self.assertContains(resposta, "Você já tem uma turma com esse nome neste período.")
        self.assertContains(resposta, 'value="Turma C"')

    @patch("professor.views.criar_turma")
    def test_api_fora_do_ar_no_modal(self, criar_mock, _):
        criar_mock.side_effect = ErroAPI("Não foi possível conectar ao servidor. Tente novamente.")
        resposta = self.client.post(self.url, self.dados)
        self.assertContains(resposta, "Não foi possível conectar ao servidor")
        self.assertContains(resposta, "data-abrir")
