from django.shortcuts import render, redirect, get_object_or_404
from .models import Client
from django.core.exceptions import ValidationError
from django.contrib import messages

def get_client(request):
    """
    Método para fazer o pegar os clientes cadastrados
    """
    if request.method=='GET':
        clients = Client.objects.all() # Pegar todos os clientes cadastrados
        return render(request, 'clients.html', {'clients': clients})
    
def create_client(request):
    """
    Método para criar usuário apartir do tipo da requisição
    """
    if request.method=='GET':
        return render(request, 'creat_client.html')
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
        # Salvar o cliente e levantar erros
        try:
            client.save()
            messages.success(request, 'Cliente criado com sucesso!')
            return redirect('clients.html')
        except ValidationError as err:
            messages.error(request, f'Erro de validação: {str(err)}')
            return redirect('create_client.html')

def update_client(request, id:int):
    """
    Método para atualizar um usuário
    """
    client = get_object_or_404(Client, id=id) # Pegar o cliente que se pretende atualizar via ID
    if request=='POST':
        # Pegar a informações do template
        client.name = request.POST.get('name')
        client.email = request.POST.get('email')
        client.age = request.POST.get('age')
        try:
            # Salvar as atualizações do cliente
            client.save()
            messages.success(request, 'Cliente criado com sucesso!')
            return redirect('clients.html')
        except ValidationError as err:
            messages.error(request, f'Erro de validação: {str(err)}')
            return redirect('update_clien.html')
