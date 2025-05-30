from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.contrib.auth.decorators import login_required
from .models import Client, Pedido
from .forms import ClientForm, ClientSearchForm, PedidoForm, PedidoSearchForm

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

@login_required
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

# Views para gerenciamento de grupos
@login_required
@group_required('Administradores')
def manage_users(request):
    """
    View para gerenciar usuários e seus grupos
    Apenas Administradores podem acessar
    """
    from django.contrib.auth.models import User
    
    users = User.objects.all().prefetch_related('groups')
    groups = Group.objects.all()
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        group_ids = request.POST.getlist('groups')
        
        try:
            user = User.objects.get(id=user_id)
            user.groups.clear()
            
            for group_id in group_ids:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)
            
            messages.success(request, f'Grupos do usuário {user.username} atualizados com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar grupos: {str(e)}')
        
        return redirect('manage_users')
    
    return render(request, 'manage_users.html', {
        'users': users,
        'groups': groups,
    })

# ==================== VIEWS PARA PEDIDOS ====================

@login_required
@group_required('Administradores', 'Gerentes', 'Funcionários')
def get_pedidos(request):
    """
    Listar pedidos com busca avançada e paginação
    Todos os grupos autenticados podem visualizar
    """
    search_form = PedidoSearchForm(request.GET)
    pedidos_list = Pedido.objects.select_related('cliente').order_by('-data_pedido')
    
    # Aplicar filtros de busca se o formulário for válido
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        cliente = search_form.cleaned_data.get('cliente')
        status = search_form.cleaned_data.get('status')
        prioridade = search_form.cleaned_data.get('prioridade')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')
        valor_min = search_form.cleaned_data.get('valor_min')
        valor_max = search_form.cleaned_data.get('valor_max')
        
        # Filtro de busca textual
        if search_query:
            pedidos_list = pedidos_list.filter(
                Q(numero_pedido__icontains=search_query) | 
                Q(cliente__name__icontains=search_query) |
                Q(descricao__icontains=search_query)
            )
        
        # Filtro por cliente
        if cliente:
            pedidos_list = pedidos_list.filter(cliente=cliente)
        
        # Filtro por status
        if status:
            pedidos_list = pedidos_list.filter(status=status)
        
        # Filtro por prioridade
        if prioridade:
            pedidos_list = pedidos_list.filter(prioridade=prioridade)
        
        # Filtro por intervalo de datas
        if data_inicio:
            pedidos_list = pedidos_list.filter(data_pedido__date__gte=data_inicio)
        
        if data_fim:
            pedidos_list = pedidos_list.filter(data_pedido__date__lte=data_fim)
        
        # Filtro por intervalo de valores
        if valor_min is not None:
            pedidos_list = pedidos_list.filter(valor_total__gte=valor_min)
        
        if valor_max is not None:
            pedidos_list = pedidos_list.filter(valor_total__lte=valor_max)
    
    # Calcular estatísticas dos resultados filtrados
    stats = pedidos_list.aggregate(
        total_pedidos=Count('id'),
        valor_total=Sum('valor_total'),
        valor_medio=Avg('valor_total')
    )
    
    # Configurar paginação
    paginator = Paginator(pedidos_list, 15)  # 15 pedidos por página
    page_number = request.GET.get('page')
    pedidos = paginator.get_page(page_number)
    
    # Verificar permissões para mostrar botões na template
    user_groups = request.user.groups.values_list('name', flat=True)
    can_create = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    can_edit = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    can_delete = 'Administradores' in user_groups or request.user.is_superuser
    can_bulk_actions = 'Administradores' in user_groups or request.user.is_superuser
    
    return render(request, 'pedidos.html', {
        'pedidos': pedidos,
        'search_form': search_form,
        'stats': stats,
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'can_bulk_actions': can_bulk_actions,
    })

@login_required
@group_required('Administradores', 'Gerentes')
def create_pedido(request):
    """
    Criar novo pedido
    Apenas Administradores e Gerentes podem criar
    """
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            try:
                pedido = form.save()
                messages.success(
                    request, 
                    f'Pedido {pedido.numero_pedido} criado com sucesso!'
                )
                return redirect('detail_pedido', id=pedido.id)
            except Exception as e:
                messages.error(
                    request, 
                    f'Erro ao salvar pedido: {str(e)}'
                )
        else:
            messages.error(
                request, 
                'Por favor, corrija os erros abaixo.'
            )
    else:
        form = PedidoForm()
    
    return render(request, 'create_pedido.html', {'form': form})

@login_required
@group_required('Administradores', 'Gerentes')
def update_pedido(request, id):
    """
    Atualizar pedido existente
    Apenas Administradores e Gerentes podem editar
    """
    pedido = get_object_or_404(Pedido, id=id)
    
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            try:
                updated_pedido = form.save()
                messages.success(
                    request, 
                    f'Pedido {updated_pedido.numero_pedido} atualizado com sucesso!'
                )
                return redirect('detail_pedido', id=updated_pedido.id)
            except Exception as e:
                messages.error(
                    request, 
                    f'Erro ao atualizar pedido: {str(e)}'
                )
        else:
            messages.error(
                request, 
                'Por favor, corrija os erros abaixo.'
            )
    else:
        form = PedidoForm(instance=pedido)
    
    return render(request, 'update_pedido.html', {
        'form': form,
        'pedido': pedido
    })
