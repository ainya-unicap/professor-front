from django.urls import path

from . import views

app_name = "professor"

urlpatterns = [
    path("painel/", views.painel, name="painel"),
    path("turmas/", views.turmas, name="turmas"),
    path("turmas/nova/", views.nova_turma, name="nova_turma"),
    path("turmas/<int:turma_id>/", views.turma, name="turma"),
    path("turmas/<int:turma_id>/prazos/", views.turma_prazos, name="turma_prazos"),
    path("turmas/<int:turma_id>/novo-codigo/", views.turma_novo_codigo, name="turma_novo_codigo"),
    path("turmas/<int:turma_id>/correcoes/", views.turma_correcoes, name="turma_correcoes"),
    path("correcoes/", views.correcoes, name="correcoes"),
    path("correcoes/<int:relatorio_id>/", views.correcao, name="correcao"),
    path("correcoes/<int:relatorio_id>/avaliar/", views.correcao_avaliar, name="correcao_avaliar"),
    path("correcoes/<int:relatorio_id>/pdf/", views.correcao_pdf, name="correcao_pdf"),
    path("correcoes/<int:relatorio_id>/fotos/<int:foto_id>/", views.correcao_foto, name="correcao_foto"),
]
