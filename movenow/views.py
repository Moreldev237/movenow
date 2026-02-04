from django.shortcuts import render
from django.conf import settings


def index(request):
    """
    Vue pour servir le frontend static/index.html
    """
    return render(request, 'index.html', context={
        'debug': settings.DEBUG,
    })


def health_check(request):
    """
    Vue pour vérifier que le serveur est en marche
    """
    from django.http import JsonResponse
    return JsonResponse({
        'status': 'ok',
        'message': 'MoveNow API is running',
        'version': '1.0.0'
    })

