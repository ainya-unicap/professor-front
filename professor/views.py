from django.shortcuts import render

from core.sessao import professor_obrigatorio


@professor_obrigatorio
def painel(request):
    return render(request, "professor/painel.html", {"usuario": request.usuario})
