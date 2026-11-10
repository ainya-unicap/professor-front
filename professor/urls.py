from django.urls import path

from . import views

app_name = "professor"

urlpatterns = [
    path("turmas/", views.turmas, name="turmas"),
    path("turmas/nova/", views.nova_turma, name="nova_turma"),
]
