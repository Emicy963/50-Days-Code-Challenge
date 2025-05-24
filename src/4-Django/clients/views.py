from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Client
from .forms import ClientForm, ClientSearchForm

def get_clients(request):
    """
    Método para listar clientes com busca e paginação
    """
    search_form = ClientSearchForm(request.GET)
    clients_list = Client.objects.all().order_by('name')
    
    # Aplicar filtros de busca se o formulário for válido
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        age_min = search_form.cleaned_data.get('age_min')
        age_max = search_form.cleaned_data.get('age_max')
        
        if search_query:
            clients_list = clients_list.filter(
                Q(name__icontains=search_query) | 
                Q(email__icontains=search_query)
            )
        
        if age_min:
            clients_list = clients_list.filter(age__gte=age_min)
        
        if age_max:
            clients_list = clients_list.filter(age__lte=age_max)
    
    # Configurar paginação
    paginator = Paginator(clients_list, 10)
    page_number = request.GET.get('page')
    clients = paginator.get_page(page_number)
    
    return render(request, 'clients.html', {
        'clients': clients,
        'total_clients': clients_list.count(),
        'search_form': search_form,
    })

def create_client(request):
    """
    Método para criar cliente usando ModelForm
    """
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            try:
                client = form.save()
                messages.success(
                    request, 
                    f'Cliente {client.name} criado com sucesso!'
                )
                return redirect('detail_client', id=client.id)
            except Exception as e:
                messages.error(
                    request, 
                    f'Erro ao salvar cliente: {str(e)}'
                )
        else:
            messages.error(
                request, 
                'Por favor, corrija os erros abaixo.'
            )
    else:
        form = ClientForm()
    
    return render(request, 'create_client.html', {'form': form})

def update_client(request, id):
    """
    Método para atualizar cliente usando ModelForm
    """
    client = get_object_or_404(Client, id=id)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            try:
                updated_client = form.save()
                messages.success(
                    request, 
                    f'Cliente {updated_client.name} atualizado com sucesso!'
                )
                return redirect('detail_client', id=updated_client.id)
            except Exception as e:
                messages.error(
                    request, 
                    f'Erro ao atualizar cliente: {str(e)}'
                )
        else:
            messages.error(
                request, 
                'Por favor, corrija os erros abaixo.'
            )
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'update_client.html', {
        'form': form,
        'client': client
    })

def delete_client(request, id):
    """
    Método para apagar um cliente com confirmação
    """
    client = get_object_or_404(Client, id=id)
    
    if request.method == 'POST':
        client_name = client.name
        try:
            client.delete()
            messages.success(
                request, 
                f'Cliente {client_name} foi excluído com sucesso!'
            )
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao excluir cliente: {str(e)}'
            )
        return redirect('clients')
    
    return render(request, 'delete_client.html', {'client': client})

def detail_client(request, id):
    """
    Método para exibir detalhes de um cliente
    """
    client = get_object_or_404(Client, id=id)
    return render(request, 'detail_client.html', {'client': client})

def bulk_delete_clients(request):
    """
    Método para exclusão em lote de clientes
    """
    if request.method == 'POST':
        client_ids = request.POST.getlist('client_ids[]')
        
        if client_ids:
            try:
                deleted_count = Client.objects.filter(id__in=client_ids).count()
                Client.objects.filter(id__in=client_ids).delete()
                messages.success(
                    request, 
                    f'{deleted_count} cliente(s) excluído(s) com sucesso!'
                )
            except Exception as e:
                messages.error(
                    request, 
                    f'Erro ao excluir clientes: {str(e)}'
                )
        else:
            messages.warning(request, 'Nenhum cliente selecionado.')
    
    return redirect('clients')