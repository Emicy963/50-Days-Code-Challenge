from django.shortcuts import render, redirect
from .models import Client
from django.core.exceptions import ValidationError
from django.contrib import messages

def create_client(request):
    """
    Método para criar usuário apartir do tipo da requisição
    """
    if request.method=='GET':
        # Se a requisição for do tipo GET, retornar o templates que mostra os clientes cadastrados
        clients = Client.objects.all()
        return render(request, 'clients.html', {'clients':clients})
    else:
        name=request.POST.get('name')
        email=request.POST.get('email')
        age=request.POST.get('age')
        # Criar o cliente
        client = Client.objects.create(
            name=name,
            email=email,
            age=age
        )

        try:
            client.save()
            messages.success(request, 'Cliente criado com sucesso!')
            return redirect('clients.html')
        except ValidationError as err:
            messages.error(request, f'Erro de validação: {str(err)}')
            return redirect('create_client.html')
