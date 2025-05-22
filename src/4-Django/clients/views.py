from django.shortcuts import render, redirect, get_object_or_404
from .models import Client
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.core.paginator import Paginator

def get_clients(request):
    """
    Método para pegar os clientes cadastrados com paginação
    """
    if request.method == 'GET':
        clients_list = Client.objects.all().order_by('name')  # Ordenar por nome
        
        # Configurar paginação - 10 clientes por página
        paginator = Paginator(clients_list, 1)
        page_number = request.GET.get('page')
        clients = paginator.get_page(page_number)
        
        return render(request, 'clients.html', {
            'clients': clients,
            'total_clients': clients_list.count()
        })

def create_client(request):
    """
    Método para criar usuário apartir do tipo da requisição
    """
    if request.method == 'GET':
        return render(request, 'create_client.html')
    else:
        name = request.POST.get('name')
        email = request.POST.get('email')
        age = request.POST.get('age')
        
        try:
            # Criar o cliente
            client = Client.objects.create(
                name=name,
                email=email,
                age=int(age)  # Converter para inteiro
            )
            client.save()
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
    client = get_object_or_404(Client, id=id)  # Pegar o cliente que se pretende atualizar via ID
    
    if request.method == 'GET':
        return render(request, 'update_client.html', {'client': client})
    
    elif request.method == 'POST':
        # Pegar as informações do template
        client.name = request.POST.get('name')
        client.email = request.POST.get('email')
        age = request.POST.get('age')
        
        try:
            client.age = int(age)  # Converter para inteiro
            client.save()  # Salvar as atualizações do cliente
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
    client_name = client.name  # Guardar o nome para a mensagem
    client.delete()
    messages.success(request, f'Cliente {client_name} foi excluído com sucesso!')
    return redirect('clients')

def detail_client(request, id):
    """
    Método para pegar um cliente individualmente
    """
    client = get_object_or_404(Client, id=id)
    return render(request, 'detail_client.html', {'client': client})
