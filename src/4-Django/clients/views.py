from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Client
from .forms import ClientForm, ClientSearchForm

# Decorator personalizado para verificar grupos
def group_required(*group_names):
    """
    Decorator para verificar se o usuário pertence a um dos grupos especificados
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
                
                user_groups = request.user.groups.values_list('name', flat=True)
                if any(group in user_groups for group in group_names):
                    return view_func(request, *args, **kwargs)
            
            return HttpResponseForbidden("Você não tem permissão para acessar esta página.")
        return _wrapped_view
    return decorator

@group_required('Administradores', 'Gerentes', 'Funcionários')
def get_clients(request):
    """
    Método para listar clientes com busca e paginação
    Todos os grupos autenticados podem visualizar
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
    
    # Verificar permissões para mostrar botões na template
    user_groups = request.user.groups.values_list('name', flat=True)
    can_create = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    can_edit = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    can_delete = 'Administradores' in user_groups or request.user.is_superuser
    
    return render(request, 'clients.html', {
        'clients': clients,
        'total_clients': clients_list.count(),
        'search_form': search_form,
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required
@group_required('Administradores', 'Gerentes')
def create_client(request):
    """
    Método para criar cliente usando ModelForm
    Apenas Administradores e Gerentes podem criar
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

@login_required
@group_required('Administradores', 'Gerentes')
def update_client(request, id):
    """
    Método para atualizar cliente usando ModelForm
    Apenas Administradores e Gerentes podem editar
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

@login_required
@group_required('Administradores')
def delete_client(request, id):
    """
    Método para apagar um cliente com confirmação
    Apenas Administradores podem deletar
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

@login_required
@group_required('Administradores', 'Gerentes', 'Funcionários')
def detail_client(request, id):
    """
    Método para exibir detalhes de um cliente
    Todos os grupos podem visualizar detalhes
    """
    client = get_object_or_404(Client, id=id)
    
    # Verificar permissões para mostrar botões na template
    user_groups = request.user.groups.values_list('name', flat=True)
    can_edit = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    can_delete = 'Administradores' in user_groups or request.user.is_superuser
    
    return render(request, 'detail_client.html', {
        'client': client,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required
@group_required('Administradores')
def bulk_delete_clients(request):
    """
    Método para exclusão em lote de clientes
    Apenas Administradores podem fazer exclusão em lote
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
