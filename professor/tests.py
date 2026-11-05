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
        self.assertContains(resposta, f'href="{reverse("professor:turma", args=[1])}"')
        self.assertContains(resposta, f'href="{reverse("professor:turma", args=[1])}#prazos"')
        self.assertContains(resposta, f'href="{reverse("professor:correcao", args=[10])}"')

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
        self.assertRedirects(resposta, reverse("professor:turma", args=[3]), fetch_redirect_response=False)
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


TURMA_API = {
    "id": 1,
    "nome": "Turma A",
    "periodo": "2026.1",
    "instituicao": "UNICAP",
    "codigo_convite": "K7MPQ3",
    "link_convite": "https://alunos.exemplo/convite/K7MPQ3",
    "ativa": True,
    "alunos": 5,
    "relatorios_entregues": 2,
    "inicio_registros": "2026-03-02",
    "encerramento_registros": "2026-06-05",
    "limite_entrega": "2026-06-12",
    "prazo_correcao": "2026-06-26",
    "aceitar_atrasadas": False,
    "alunos_lista": [
        {"id": 11, "nome": "Pedro Sá", "status": "entregue", "relatorio_id": 101},
        {"id": 12, "nome": "Ana Souza", "status": "entregue", "relatorio_id": 102},
        {"id": 13, "nome": "Bruno Lima", "status": "corrigido", "relatorio_id": 103},
        {"id": 14, "nome": "Carla Reis", "status": "sem_relatorio", "relatorio_id": None},
        {"id": 15, "nome": "Davi Melo", "status": "sem_relatorio", "relatorio_id": None},
    ],
}


@patch("professor.views.contar_pendentes", return_value=7)
class TurmaTests(Logado):
    url = reverse("professor:turma", args=[1])

    @patch("professor.views.buscar_turma", return_value=TURMA_API)
    def test_mostra_prazos_convite_e_alunos(self, _, __):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "professor/turma.html")
        for texto in (
            "Turma A · 2026.1",
            'value="2026-03-02"',
            'value="2026-06-26"',
            "Só você vê: aparece como lembrete no painel.",
            'value="https://alunos.exemplo/convite/K7MPQ3"',
            'value="K7MPQ3"',
            "5 alunos já entraram",
            "Ver os 5",
            "Aguardando correção",
            "Corrigido",
            "Sem relatório",
            reverse("professor:correcao", args=[101]),
        ):
            self.assertContains(resposta, texto)
        self.assertContains(resposta, 'class="lista__item aluno" hidden', count=1)
        self.assertContains(resposta, "menu__item menu__item--ativo", count=1)

    @patch("professor.views.buscar_turma")
    def test_turma_inexistente_da_404(self, buscar_mock, _):
        from core.api import NaoEncontrado

        buscar_mock.side_effect = NaoEncontrado()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    @patch("professor.views.salvar_prazos")
    def test_salva_prazos(self, salvar_mock, _):
        resposta = self.client.post(
            reverse("professor:turma_prazos", args=[1]),
            {"inicio_registros": "2026-03-02", "prazo_correcao": "2026-06-26", "aceitar_atrasadas": "on"},
        )
        self.assertRedirects(resposta, reverse("professor:turma", args=[1]) + "#prazos", fetch_redirect_response=False)
        self.assertEqual(
            salvar_mock.call_args.args[2],
            {
                "inicio_registros": "2026-03-02",
                "encerramento_registros": None,
                "limite_entrega": None,
                "prazo_correcao": "2026-06-26",
                "aceitar_atrasadas": True,
            },
        )

    @patch("professor.views.buscar_turma", return_value=TURMA_API)
    @patch("professor.views.salvar_prazos")
    def test_prazos_fora_de_ordem_nao_chamam_a_api(self, salvar_mock, _, __):
        resposta = self.client.post(
            reverse("professor:turma_prazos", args=[1]),
            {"inicio_registros": "2026-06-10", "encerramento_registros": "2026-06-05"},
        )
        self.assertContains(resposta, "Encerramento dos registros não pode ser antes de: início dos registros.")
        salvar_mock.assert_not_called()

    @patch("professor.views.buscar_turma", return_value=TURMA_API)
    @patch("professor.views.salvar_prazos")
    def test_erro_da_api_nos_prazos(self, salvar_mock, _, __):
        salvar_mock.side_effect = ErroValidacao({"limite_entrega": ["Limite de entrega não pode ser antes de: encerramento dos registros."]})
        resposta = self.client.post(reverse("professor:turma_prazos", args=[1]), {"limite_entrega": "2026-06-01"})
        self.assertContains(resposta, "Limite de entrega não pode ser antes de")

    @patch("professor.views.gerar_novo_codigo", return_value={"codigo_convite": "NOVO22", "link_convite": "x/NOVO22"})
    def test_gera_novo_codigo(self, gerar_mock, _):
        resposta = self.client.post(reverse("professor:turma_novo_codigo", args=[1]))
        self.assertRedirects(resposta, reverse("professor:turma", args=[1]) + "#convite", fetch_redirect_response=False)
        gerar_mock.assert_called_once()

    def test_novo_codigo_exige_post(self, _):
        self.assertEqual(self.client.get(reverse("professor:turma_novo_codigo", args=[1])).status_code, 405)


RELATORIO_API = {
    "id": 101,
    "aluno": {"id": 11, "nome": "Pedro Sá"},
    "turma": {"id": 1, "nome": "Turma A", "periodo": "2026.1", "prazo_correcao": "2026-06-26"},
    "planta": "Camelo",
    "status": "entregue",
    "entregue_em": "2026-06-09T10:00:00Z",
    "introducao": "Contexto do canteiro.",
    "objetivo": "Acompanhar o crescimento.",
    "desenvolvimento": "Rebrota uniforme após o corte.",
    "conclusao": "",
    "referencias": "Fontes consultadas.",
    "fotos": [{"id": 7, "legenda": "Semana 3"}],
    "tem_pdf": True,
    "nota": "8.50",
    "feedback": "Bom trabalho",
    "corrigido_em": None,
    "anterior": None,
    "proximo": 102,
}


@patch("professor.views.contar_pendentes", return_value=7)
class CorrecaoTests(Logado):
    url = reverse("professor:correcao", args=[101])

    @patch("professor.views.buscar_relatorio", return_value=RELATORIO_API)
    def test_mostra_o_relatorio(self, _, __):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "professor/correcao.html")
        for texto in (
            "Relatório de Pedro Sá",
            "Camelo · Turma A · 2026.1",
            "Introdução",
            "Contexto do canteiro.",
            "Rebrota uniforme após o corte.",
            "Não preenchido.",
            reverse("professor:correcao_foto", args=[101, 7]),
            reverse("professor:correcao_pdf", args=[101]),
            reverse("professor:correcao", args=[102]),
            'value="8,5"',
            "Bom trabalho",
            "Nota e feedback ficam visíveis apenas para Pedro Sá.",
            "Prazo de correção da turma: 26 jun.",
            "Aguardando correção",
            "Salvar e marcar como corrigido",
            "Salvar sem concluir",
        ):
            self.assertContains(resposta, texto)
        self.assertContains(resposta, "botao-pilula--inativo", count=1)

    @patch("professor.views.salvar_avaliacao")
    def test_marcar_como_corrigido(self, salvar_mock, _):
        salvar_mock.return_value = {**RELATORIO_API, "status": "corrigido"}
        resposta = self.client.post(
            reverse("professor:correcao_avaliar", args=[101]), {"nota": "9,25", "feedback": "Ótimo", "acao": "corrigir"}
        )
        self.assertRedirects(resposta, self.url, fetch_redirect_response=False)
        self.assertEqual(salvar_mock.call_args.args[1:], (101, "9.25", "Ótimo", True))

    @patch("professor.views.salvar_avaliacao")
    def test_salvar_sem_concluir(self, salvar_mock, _):
        salvar_mock.return_value = RELATORIO_API
        self.client.post(reverse("professor:correcao_avaliar", args=[101]), {"nota": "", "feedback": "Rascunho", "acao": "rascunho"})
        self.assertEqual(salvar_mock.call_args.args[1:], (101, None, "Rascunho", False))

    @patch("professor.views.buscar_relatorio", return_value=RELATORIO_API)
    @patch("professor.views.salvar_avaliacao")
    def test_corrigir_sem_nota(self, salvar_mock, _, __):
        resposta = self.client.post(reverse("professor:correcao_avaliar", args=[101]), {"nota": "", "acao": "corrigir"})
        self.assertContains(resposta, "Informe a nota para marcar como corrigido.")
        salvar_mock.assert_not_called()

    @patch("professor.views.buscar_relatorio", return_value=RELATORIO_API)
    @patch("professor.views.salvar_avaliacao")
    def test_nota_invalida(self, salvar_mock, _, __):
        for nota, mensagem in (("11", "A nota vai de 0 a 10."), ("abc", "Informe um número")):
            resposta = self.client.post(reverse("professor:correcao_avaliar", args=[101]), {"nota": nota, "acao": "corrigir"})
            self.assertContains(resposta, mensagem)
        salvar_mock.assert_not_called()

    @patch("professor.views.baixar_arquivo")
    def test_repassa_o_pdf(self, baixar_mock, _):
        from unittest.mock import Mock

        baixar_mock.return_value = Mock(
            content=b"%PDF",
            headers={"Content-Type": "application/pdf", "Content-Disposition": 'attachment; filename="r.pdf"'},
        )
        resposta = self.client.get(reverse("professor:correcao_pdf", args=[101]))
        self.assertEqual(resposta.content, b"%PDF")
        self.assertEqual(resposta["Content-Type"], "application/pdf")
        self.assertIn("attachment", resposta["Content-Disposition"])
        self.assertEqual(baixar_mock.call_args.args[1], "relatorios/101/pdf/")

    @patch("professor.views.baixar_arquivo")
    def test_repassa_a_foto(self, baixar_mock, _):
        from unittest.mock import Mock

        baixar_mock.return_value = Mock(content=b"img", headers={"Content-Type": "image/png"})
        resposta = self.client.get(reverse("professor:correcao_foto", args=[101, 7]))
        self.assertEqual(resposta["Content-Type"], "image/png")
        self.assertEqual(baixar_mock.call_args.args[1], "relatorios/101/fotos/7/")


LISTA_TURMAS = [
    {**{k: v for k, v in TURMA_API.items() if k != "alunos_lista"}, "id": 1, "nome": "Turma A", "alunos": 18, "relatorios_entregues": 13, "aguardando_correcao": 0},
    {**{k: v for k, v in TURMA_API.items() if k != "alunos_lista"}, "id": 2, "nome": "Turma B", "alunos": 16, "relatorios_entregues": 6, "aguardando_correcao": 3},
]


@patch("professor.views.contar_pendentes", return_value=3)
class MenuLateralTests(Logado):
    @patch("professor.views.listar_turmas", return_value=LISTA_TURMAS)
    def test_menu_tem_links_para_turmas_e_correcoes(self, _, __):
        resposta = self.client.get(reverse("professor:turmas"))
        self.assertContains(resposta, f'href="{reverse("professor:turmas")}"')
        self.assertContains(resposta, f'href="{reverse("professor:correcoes")}"')
        self.assertContains(resposta, f'href="{reverse("professor:painel")}"')


@patch("professor.views.contar_pendentes", return_value=3)
class TurmasTests(Logado):
    url = reverse("professor:turmas")

    @patch("professor.views.listar_turmas", return_value=LISTA_TURMAS)
    def test_lista_as_turmas(self, _, __):
        resposta = self.client.get(self.url)
        self.assertTemplateUsed(resposta, "professor/turmas.html")
        for texto in (
            "Olá, Maria",
            "Gerencie alunos, convites e relatórios.",
            "2026.1 · 18 alunos",
            "13 de 18 relatórios entregues",
            "3 aguardando correção",
            f'href="{reverse("professor:turma", args=[2])}"',
            'id="modal-nova-turma"',
            'name="origem" value="turmas"',
        ):
            self.assertContains(resposta, texto)

    @patch("professor.views.listar_turmas", return_value=[])
    def test_sem_turmas(self, _, __):
        self.assertContains(self.client.get(self.url), "Você ainda não tem turmas.")

    @patch("professor.views.listar_turmas", return_value=LISTA_TURMAS)
    def test_erro_no_modal_volta_para_a_lista(self, _, __):
        resposta = self.client.post(reverse("professor:nova_turma"), {"origem": "turmas"})
        self.assertTemplateUsed(resposta, "professor/turmas.html")
        self.assertContains(resposta, "Informe o nome da turma.")
        self.assertContains(resposta, "data-abrir")


RELATORIOS_TURMA = [
    {"id": 101, "aluno": "Pedro Sá", "planta": "Camelo", "status": "entregue", "entregue_em": "2026-06-09T10:00:00Z", "tem_pdf": True},
    {"id": 103, "aluno": "Bruno Lima", "planta": "Aruana", "status": "corrigido", "entregue_em": "2026-06-08T10:00:00Z", "tem_pdf": False},
]


@patch("professor.views.contar_pendentes", return_value=3)
class CorrecoesTests(Logado):
    @patch("professor.views.listar_turmas", return_value=LISTA_TURMAS)
    def test_abre_a_turma_com_mais_pendencias(self, _, __):
        resposta = self.client.get(reverse("professor:correcoes"))
        self.assertRedirects(resposta, reverse("professor:turma_correcoes", args=[2]), fetch_redirect_response=False)

    @patch("professor.views.listar_turmas")
    def test_sem_pendencias_abre_a_primeira(self, listar_mock, _):
        listar_mock.return_value = [{**t, "aguardando_correcao": 0} for t in LISTA_TURMAS]
        resposta = self.client.get(reverse("professor:correcoes"))
        self.assertRedirects(resposta, reverse("professor:turma_correcoes", args=[1]), fetch_redirect_response=False)

    @patch("professor.views.listar_turmas", return_value=[])
    def test_sem_turmas_vai_para_a_lista(self, _, __):
        resposta = self.client.get(reverse("professor:correcoes"))
        self.assertRedirects(resposta, reverse("professor:turmas"), fetch_redirect_response=False)

    @patch("professor.views.listar_turmas", return_value=LISTA_TURMAS)
    @patch("professor.views.listar_relatorios_da_turma", return_value=RELATORIOS_TURMA)
    @patch("professor.views.buscar_turma", return_value=TURMA_API)
    def test_tabela_de_relatorios(self, _, __, ___, ____):
        resposta = self.client.get(reverse("professor:turma_correcoes", args=[1]))
        self.assertTemplateUsed(resposta, "professor/correcoes.html")
        for texto in (
            "Relatórios submetidos pelos alunos da sua turma.",
            "Copiar Link da Turma",
            'value="https://alunos.exemplo/convite/K7MPQ3"',
            "Pedro Sá",
            "Camelo",
            "09 Junho",
            reverse("professor:correcao", args=[101]),
            reverse("professor:correcao_pdf", args=[101]),
            "selo--mini",
            "botao-baixar--inativo",
            "Turma B · 2026.1 (3)",
        ):
            self.assertContains(resposta, texto)
        self.assertContains(resposta, "menu__item menu__item--ativo", count=1)
