from django.urls import path

from . import views

app_name = "professor"

urlpatterns = [
    path("painel/", views.painel, name="painel"),
    path("turmas/nova/", views.turma_criar, name="turma_criar"),
    path("turmas/<uuid:turma_id>/", views.turma_detalhe, name="turma_detalhe"),
    path("turmas/<uuid:turma_id>/apagar/", views.turma_apagar, name="turma_apagar"),
    path("turmas/<uuid:turma_id>/codigos/novo/", views.codigo_gerar, name="codigo_gerar"),
    path("turmas/<uuid:turma_id>/codigos/<uuid:codigo_id>/apagar/", views.codigo_apagar, name="codigo_apagar"),
]
