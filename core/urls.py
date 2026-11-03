from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "core"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="core:login", permanent=False)),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
