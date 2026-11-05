from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.api import ErroAPI, ErroValidacao, SessaoExpirada
from core.sessao import CHAVE_SESSAO

USUARIO = {
    "id": 1,
    "nome": "Maria Lima",
    "email": "prof@teste.com",
    "matricula": "0000015638",
    "papel": "professor",
}


def painel_api(**extra):
    prazo = timezone.localdate() + timedelta(days=5)
    dados = {
        "periodo_atual": "2026.1",
        "instituicao": "UNICAP",
        "resumo": {
            "aguardando_correcao": 7,
            "turmas_com_pendencia": 2,
            "turmas_ativas": 2,
            "alunos": 34,
            "prazo_avaliacao": prazo.isoformat(),
        },
        "turmas": [
            {"id": 1, "nome": "Turma A", "periodo": "2026.1", "instituicao": "UNICAP", "codigo_convite": "ABC234", "alunos": 18, "relatorios_entregues": 13},
            {"id": 2, "nome": "Turma B", "periodo": "2026.1", "instituicao": "UNICAP", "codigo_convite": "XYZ789", "alunos": 0, "relatorios_entregues": 0},
        ],
        "aguardando": [
            {"id": 10, "aluno": "Pedro Sá", "planta": "Camelo", "turma": "Turma A", "entregue_em": None},
        ],
    }
    dados.update(extra)
    return dados


PAINEL_VAZIO = {
    "periodo_atual": None,
    "instituicao": None,
    "resumo": {"aguardando_correcao": 0, "turmas_com_pendencia": 0, "turmas_ativas": 0, "alunos": 0, "prazo_avaliacao": None},
    "turmas": [],
    "aguardando": [],
}


class Logado(TestCase):
    def setUp(self):
        sessao = self.client.session
        sessao[CHAVE_SESSAO] = {"access": "a", "refresh": "r", "usuario": USUARIO}
        sessao.save()


class PainelTests(Logado):
    url = reverse("professor:painel")

    @patch("professor.views.buscar_painel")
    def test_mostra_os_dados_do_painel(self, buscar_mock):
        buscar_mock.return_value = painel_api()
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "professor/painel.html")
        prazo = timezone.localdate() + timedelta(days=5)
        for texto in (
            "Olá, Maria",
            "2026.1 · UNICAP",
            "7 relatórios aguardam correção",
            "2 Turmas",
            "Período 2026.1",
            "34",
            "Encerra em breve",
            "Turma A · 2026.1",
            "18 alunos · UNICAP",
            "13 de 18 relatórios entregues",
            "width: 72%",
            "0 de 0 relatórios entregues",
            "Pedro Sá",
            "Camelo · Turma A",
            "0000015638",
        ):
            self.assertContains(resposta, texto)
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        self.assertContains(resposta, f"{prazo.day} {meses[prazo.month - 1]}")
        self.assertContains(resposta, 'class="menu__contador"')

    @patch("professor.views.buscar_painel")
    def test_painel_vazio(self, buscar_mock):
        buscar_mock.return_value = PAINEL_VAZIO
        resposta = self.client.get(self.url)
        self.assertContains(resposta, "Crie sua primeira turma para começar o semestre.")
        self.assertContains(resposta, "Você ainda não tem turmas.")
        self.assertContains(resposta, "Nenhum relatório aguardando correção.")
        self.assertContains(resposta, "Sem prazo definido")
        self.assertNotContains(resposta, 'class="menu__contador"')

    @patch("professor.views.buscar_painel")
    def test_prazo_distante(self, buscar_mock):
        dados = painel_api()
        dados["resumo"]["prazo_avaliacao"] = (timezone.localdate() + timedelta(days=20)).isoformat()
        buscar_mock.return_value = dados
        self.assertContains(self.client.get(self.url), "Em 20 dias")

    @patch("professor.views.buscar_painel")
    def test_api_fora_do_ar_mostra_aviso(self, buscar_mock):
        buscar_mock.side_effect = ErroAPI("Não foi possível conectar ao servidor. Tente novamente.")
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Não foi possível conectar ao servidor")

    @patch("professor.views.buscar_painel")
    def test_sessao_expirada_volta_para_o_login(self, buscar_mock):
        buscar_mock.side_effect = SessaoExpirada()
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, reverse("core:login"), fetch_redirect_response=False)
        self.assertNotIn(CHAVE_SESSAO, self.client.session)
        self.assertContains(self.client.get(reverse("core:login")), "Sua sessão expirou")

    def test_sem_login_volta_para_o_login(self):
        self.client.session.flush()
        self.client.cookies.clear()
        self.assertRedirects(self.client.get(self.url), reverse("core:login"))


@patch("professor.views.buscar_painel", return_value=painel_api())
class NovaTurmaTests(Logado):
    url = reverse("professor:nova_turma")
    dados = {"nome": "Turma C", "periodo": "2026.1", "instituicao": "UNICAP"}

    def test_get_abre_o_modal(self, _):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'id="modal-nova-turma"')
        self.assertContains(resposta, "data-abrir")
        self.assertContains(resposta, 'value="2026.1"')
        self.assertContains(resposta, 'value="UNICAP"')

    def test_painel_nao_abre_o_modal_sozinho(self, _):
        resposta = self.client.get(reverse("professor:painel"))
        self.assertContains(resposta, 'id="modal-nova-turma"')
        self.assertNotContains(resposta, "data-abrir>")

    @patch("professor.views.criar_turma")
    def test_cria_turma_e_mostra_o_codigo(self, criar_mock, _):
        criar_mock.return_value = {"id": 3, "nome": "Turma C", "codigo_convite": "QW3RTY"}
        resposta = self.client.post(self.url, self.dados)
        self.assertRedirects(resposta, reverse("professor:painel"), fetch_redirect_response=False)
        criar_mock.assert_called_once()
        self.assertEqual(criar_mock.call_args.args[1:], ("Turma C", "2026.1", "UNICAP"))
        pagina = self.client.get(reverse("professor:painel"))
        self.assertContains(pagina, "Turma “Turma C” criada. Código de convite: QW3RTY")

    @patch("professor.views.criar_turma")
    def test_campos_vazios(self, criar_mock, _):
        resposta = self.client.post(self.url, {})
        self.assertContains(resposta, "Informe o nome da turma.")
        self.assertContains(resposta, "Informe o período.")
        self.assertContains(resposta, "Informe a instituição.")
        self.assertContains(resposta, "data-abrir")
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
