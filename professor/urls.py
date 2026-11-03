from django.urls import path

from . import views

app_name = "professor"

urlpatterns = [
    path("painel/", views.painel, name="painel"),
]
