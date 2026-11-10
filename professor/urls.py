from django.urls import path

from . import views

app_name = "professor"

urlpatterns = [
    path("turmas/", views.turmas, name="turmas"),
    path("turmas/nova/", views.nova_turma, name="nova_turma"),
    path("turmas/<int:turma_id>/", views.turma, name="turma"),
    path("relatorios/<int:relatorio_id>/pdf/", views.relatorio_pdf, name="relatorio_pdf"),
]
