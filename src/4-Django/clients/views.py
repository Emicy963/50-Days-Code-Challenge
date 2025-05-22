from django.shortcuts import render, redirect, get_object_or_404
from .models import Client
from django.core.exceptions import ValidationError
from django.contrib import messages

def get_clients(request):
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
        return render(request, 'create_client.html')
    else:
        name=request.POST.get('name')
        email=request.POST.get('email')
        age=request.POST.get('age')
        # Salvar o cliente e levantar erros
        try:
            # Criar o cliente
            client = Client.objects.create(
                name=name,
                email=email,
                age=int(age)
            )
            messages.success(request, 'Cliente criado com sucesso!')
            return redirect('clients')
        except ValidationError as err:
            messages.error(request, f'Erro de validação: {str(err)}')
            return redirect('create_client')
        except ValueError:
            messages.error(request, 'Idade deve ser um número válido.')
            return redirect('create_client')

def update_client(request, id):
    """
    Método para atualizar um usuário
    """
    client = get_object_or_404(Client, id=id) # Pegar o cliente que se pretende atualizar via ID

    if request.method=='GET':
        return render(request, 'update_client.html', {'client': client})
    
    if request.method=='POST':
        # Pegar a informações do template
        client.name = request.POST.get('name')
        client.email = request.POST.get('email')
        age = request.POST.get('age')

        try:
            # Salvar as atualizações do cliente
            client.age = int(age)
            client.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('detail_client', id=client.id)
        except ValidationError as err:
            messages.error(request, f'Erro de validação: {str(err)}')
            return render(request, 'update_client.html', {'client': client})
        except ValueError:
            messages.error(request, 'Idade deve ser um número válido.')
            return render(request, 'update_client.html', {'client': client})

def delete_client(request, id):
    """
    Método para apagar um cliente
    """
    client = get_object_or_404(Client, id=id)
    client_name = client.name
    client.delete()
    messages.success(request, f'Cliente {client_name} foi excluído com sucesso!')
    return redirect('clients')

def detail_client(request, id):
    """
    Método para pegar um cliente individualmente
    """
    client = get_object_or_404(Client, id=id)
    return render(request, 'detail_client.html', {'client': client})
