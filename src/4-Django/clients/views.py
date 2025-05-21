from django.shortcuts import render
from .models import Client

def create_client(request):
    """
    Método para criar usuário apartir do tipo da requisição
    """
    if request.method=='GET':
        # Se a requisição for do tipo GET, retornar o templates que mostra os clientes cadastrados
        clients = Client.objects.all()
        return render(request, 'clients.html', {'clients':clients})

