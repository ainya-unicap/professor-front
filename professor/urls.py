from django.urls import path

from . import views

app_name = "professor"

urlpatterns = [
    path("painel/", views.painel, name="painel"),
    path("turmas/nova/", views.nova_turma, name="nova_turma"),
]
