from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from datetime import timezone
from .models import Client, Pedido
from .forms import (
    ClientForm, 
    ClientSearchForm, 
    PedidoForm, 
    PedidoSearchForm, 
    PedidoStatusForm,
    PedidoBulkActionForm)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import datetime

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
    Método para exibir detalhes de um cliente COM seus pedidos
    Todos os grupos podem visualizar detalhes
    """
    client = get_object_or_404(Client, id=id)
    
    # Buscar pedidos do cliente com paginação
    pedidos_list = client.pedidos.all().order_by('-data_pedido')
    paginator = Paginator(pedidos_list, 5)  # 5 pedidos por página
    page_number = request.GET.get('page')
    pedidos = paginator.get_page(page_number)
    
    # Estatísticas dos pedidos do cliente
    pedidos_stats = client.pedidos.aggregate(
        total_pedidos=Count('id'),
        valor_total=Sum('valor_total'),
        valor_medio=Avg('valor_total')
    )
    
    # Pedidos por status
    pedidos_por_status = client.pedidos.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Verificar permissões para mostrar botões na template
    user_groups = request.user.groups.values_list('name', flat=True)
    can_edit = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    can_delete = 'Administradores' in user_groups or request.user.is_superuser
    can_create_pedido = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    
    return render(request, 'detail_client.html', {
        'client': client,
        'pedidos': pedidos,
        'pedidos_stats': pedidos_stats,
        'pedidos_por_status': dict(pedidos_por_status.values_list('status', 'count')),
        'can_edit': can_edit,
        'can_delete': can_delete,
        'can_create_pedido': can_create_pedido,
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

@login_required
@group_required('Administradores')
def delete_pedido(request, id):
    """
    Excluir pedido com confirmação
    Apenas Administradores podem deletar
    """
    pedido = get_object_or_404(Pedido, id=id)
    
    if request.method == 'POST':
        numero_pedido = pedido.numero_pedido
        try:
            pedido.delete()
            messages.success(
                request, 
                f'Pedido {numero_pedido} foi excluído com sucesso!'
            )
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao excluir pedido: {str(e)}'
            )
        return redirect('pedidos')
    
    return render(request, 'delete_pedido.html', {'pedido': pedido})

@login_required
@group_required('Administradores', 'Gerentes', 'Funcionários')
def detail_pedido(request, id):
    """
    Exibir detalhes de um pedido
    Todos os grupos podem visualizar detalhes
    """
    pedido = get_object_or_404(Pedido, id=id)
    
    # Verificar permissões para mostrar botões na template
    user_groups = request.user.groups.values_list('name', flat=True)
    can_edit = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    can_delete = 'Administradores' in user_groups or request.user.is_superuser
    can_change_status = any(group in ['Administradores', 'Gerentes', 'Funcionários'] for group in user_groups) or request.user.is_superuser
    
    return render(request, 'detail_pedido.html', {
        'pedido': pedido,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'can_change_status': can_change_status,
    })

@login_required
@group_required('Administradores', 'Gerentes', 'Funcionários')
def update_pedido_status(request, id):
    """
    Atualizar apenas o status do pedido (formulário rápido)
    Todos os grupos autenticados podem alterar status
    """
    pedido = get_object_or_404(Pedido, id=id)
    
    if request.method == 'POST':
        form = PedidoStatusForm(request.POST)
        if form.is_valid():
            try:
                novo_status = form.cleaned_data['status']
                observacao = form.cleaned_data.get('observacao', '')
                
                # Adicionar observação sobre mudança de status
                if observacao:
                    if pedido.observacoes:
                        pedido.observacoes += f"\n\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Status alterado para '{pedido.get_status_display()}': {observacao}"
                    else:
                        pedido.observacoes = f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Status alterado para '{pedido.get_status_display()}': {observacao}"
                
                pedido.status = novo_status
                pedido.save()
                
                messages.success(
                    request, 
                    f'Status do pedido {pedido.numero_pedido} atualizado para {pedido.get_status_display()}!'
                )
                return redirect('detail_pedido', id=pedido.id)
            except Exception as e:
                messages.error(
                    request, 
                    f'Erro ao atualizar status: {str(e)}'
                )
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = PedidoStatusForm(initial={'status': pedido.status})
    
    return render(request, 'update_pedido_status.html', {
        'form': form,
        'pedido': pedido
    })

@login_required
@group_required('Administradores', 'Gerentes')
def cancel_pedido(request, id):
    """
    Cancelar pedido com motivo
    Apenas Administradores e Gerentes podem cancelar
    """
    pedido = get_object_or_404(Pedido, id=id)
    
    if not pedido.can_be_cancelled():
        messages.error(request, 'Este pedido não pode ser cancelado.')
        return redirect('detail_pedido', id=pedido.id)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        try:
            pedido.cancel_order(motivo)
            messages.success(
                request, 
                f'Pedido {pedido.numero_pedido} foi cancelado com sucesso!'
            )
            return redirect('detail_pedido', id=pedido.id)
        except Exception as e:
            messages.error(
                request, 
                f'Erro ao cancelar pedido: {str(e)}'
            )
    
    return render(request, 'cancel_pedido.html', {'pedido': pedido})

@login_required
@group_required('Administradores')
def bulk_actions_pedidos(request):
    """
    Ações em lote para pedidos
    Apenas Administradores podem fazer ações em lote
    """
    if request.method == 'POST':
        form = PedidoBulkActionForm(request.POST)
        pedido_ids = request.POST.getlist('pedido_ids[]')
        
        if not pedido_ids:
            messages.warning(request, 'Nenhum pedido selecionado.')
            return redirect('pedidos')
        
        if form.is_valid():
            action = form.cleaned_data['action']
            
            try:
                pedidos = Pedido.objects.filter(id__in=pedido_ids)
                count = pedidos.count()
                
                if action == 'update_status':
                    new_status = form.cleaned_data['new_status']
                    pedidos.update(status=new_status)
                    messages.success(
                        request, 
                        f'{count} pedido(s) tiveram o status atualizado para {dict(Pedido.STATUS_CHOICES)[new_status]}!'
                    )
                
                elif action == 'update_priority':
                    new_priority = form.cleaned_data['new_priority']
                    pedidos.update(prioridade=new_priority)
                    messages.success(
                        request, 
                        f'{count} pedido(s) tiveram a prioridade atualizada para {dict(Pedido.PRIORIDADE_CHOICES)[new_priority]}!'
                    )
                
                elif action == 'delete':
                    pedidos.delete()
                    messages.success(
                        request, 
                        f'{count} pedido(s) excluído(s) com sucesso!'
                    )
                
            except Exception as e:
                messages.error(
                    request, 
                    f'Erro ao executar ação em lote: {str(e)}'
                )
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    
    return redirect('pedidos')

@login_required
@group_required('Administradores', 'Gerentes', 'Funcionários')
def dashboard_pedidos(request):
    """
    Dashboard com estatísticas de pedidos
    Todos os grupos podem visualizar
    """
    # Estatísticas gerais
    stats_gerais = Pedido.get_revenue_statistics()
    stats_status = Pedido.get_status_statistics()
    
    # Pedidos por prioridade
    stats_prioridade = Pedido.objects.values('prioridade').annotate(
        count=Count('id')
    ).order_by('prioridade')
    
    # Pedidos atrasados
    pedidos_atrasados = Pedido.objects.filter(
        data_entrega_prevista__lt=timezone.now().date(),
        status__in=['pendente', 'processando', 'enviado']
    ).count()
    
    # Pedidos do mês atual
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    pedidos_mes = Pedido.objects.filter(data_pedido__gte=inicio_mes)
    
    # Top 5 clientes por quantidade de pedidos
    top_clientes = Client.objects.annotate(
        total_pedidos=Count('pedidos')
    ).filter(total_pedidos__gt=0).order_by('-total_pedidos')[:5]
    
    return render(request, 'dashboard_pedidos.html', {
        'stats_gerais': stats_gerais,
        'stats_status': stats_status,
        'stats_prioridade': dict(stats_prioridade.values_list('prioridade', 'count')),
        'pedidos_atrasados': pedidos_atrasados,
        'pedidos_mes_count': pedidos_mes.count(),
        'top_clientes': top_clientes,
    })

# ==================== AJAX VIEWS ====================

@login_required
@require_POST
def ajax_update_pedido_status(request, id):
    """
    Atualizar status via AJAX para interface mais fluida
    """
    pedido = get_object_or_404(Pedido, id=id)
    
    # Verificar permissões
    user_groups = request.user.groups.values_list('name', flat=True)
    if not (any(group in ['Administradores', 'Gerentes', 'Funcionários'] for group in user_groups) or request.user.is_superuser):
        return JsonResponse({'success': False, 'message': 'Sem permissão'}, status=403)
    
    try:
        novo_status = request.POST.get('status')
        if novo_status not in dict(Pedido.STATUS_CHOICES):
            return JsonResponse({'success': False, 'message': 'Status inválido'})
        
        pedido.status = novo_status
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Status atualizado para {pedido.get_status_display()}',
            'new_status': novo_status,
            'new_status_display': pedido.get_status_display(),
            'status_class': pedido.status_display_class
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def ajax_get_client_pedidos(request, client_id):
    """
    Obter pedidos de um cliente via AJAX
    """
    client = get_object_or_404(Client, id=client_id)
    pedidos = client.pedidos.all().order_by('-data_pedido')[:10]  # Últimos 10 pedidos
    
    pedidos_data = []
    for pedido in pedidos:
        pedidos_data.append({
            'id': pedido.id,
            'numero_pedido': pedido.numero_pedido,
            'status': pedido.get_status_display(),
            'status_class': pedido.status_display_class,
            'valor_total': str(pedido.valor_total),
            'data_pedido': pedido.data_pedido.strftime('%d/%m/%Y'),
            'url': pedido.get_absolute_url()
        })
    
    return JsonResponse({
        'pedidos': pedidos_data,
        'client_name': client.name
    })

# ==================== VIEWS ADICIONAIS PARA INTEGRAÇÃO ====================

@login_required
@group_required('Administradores', 'Gerentes')
def create_pedido_for_client(request, client_id):
    """
    Criar pedido para um cliente específico
    Apenas Administradores e Gerentes podem criar
    """
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            try:
                pedido = form.save(commit=False)
                pedido.cliente = client  # Definir o cliente automaticamente
                pedido.save()
                messages.success(
                    request, 
                    f'Pedido {pedido.numero_pedido} criado com sucesso para {client.name}!'
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
        # Inicializar formulário com cliente pré-selecionado
        form = PedidoForm(initial={'cliente': client})
        # Desabilitar campo cliente para que não possa ser alterado
        form.fields['cliente'].widget.attrs['readonly'] = True
        form.fields['cliente'].disabled = True
    
    return render(request, 'create_pedido_for_client.html', {
        'form': form,
        'client': client
    })

@login_required
@group_required('Administradores', 'Gerentes', 'Funcionários')
def client_pedidos(request, client_id):
    """
    Listar todos os pedidos de um cliente específico
    Todos os grupos podem visualizar
    """
    client = get_object_or_404(Client, id=client_id)
    
    # Filtros específicos para pedidos do cliente
    status_filter = request.GET.get('status', '')
    prioridade_filter = request.GET.get('prioridade', '')
    
    pedidos_list = client.pedidos.all().order_by('-data_pedido')
    
    if status_filter:
        pedidos_list = pedidos_list.filter(status=status_filter)
    
    if prioridade_filter:
        pedidos_list = pedidos_list.filter(prioridade=prioridade_filter)
    
    # Paginação
    paginator = Paginator(pedidos_list, 10)
    page_number = request.GET.get('page')
    pedidos = paginator.get_page(page_number)
    
    # Estatísticas
    stats = pedidos_list.aggregate(
        total_pedidos=Count('id'),
        valor_total=Sum('valor_total'),
        valor_medio=Avg('valor_total')
    )
    
    # Verificar permissões
    user_groups = request.user.groups.values_list('name', flat=True)
    can_create = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    can_edit = any(group in ['Administradores', 'Gerentes'] for group in user_groups) or request.user.is_superuser
    
    return render(request, 'client_pedidos.html', {
        'client': client,
        'pedidos': pedidos,
        'stats': stats,
        'status_choices': Pedido.STATUS_CHOICES,
        'prioridade_choices': Pedido.PRIORIDADE_CHOICES,
        'current_status': status_filter,
        'current_prioridade': prioridade_filter,
        'can_create': can_create,
        'can_edit': can_edit,
    })

@login_required
@group_required('Administradores', 'Gerentes', 'Funcionários')
def reports_pedidos(request):
    """
    Relatórios e análises de pedidos
    Todos os grupos podem visualizar
    """
    # Filtros de data para relatórios
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Query base
    pedidos = Pedido.objects.all()
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        try:
            data_inicio_parsed = timezone.datetime.strptime(data_inicio, '%Y-%m-%d').date()
            pedidos = pedidos.filter(data_pedido__date__gte=data_inicio_parsed)
        except ValueError:
            messages.error(request, 'Data de início inválida.')
    
    if data_fim:
        try:
            data_fim_parsed = timezone.datetime.strptime(data_fim, '%Y-%m-%d').date()
            pedidos = pedidos.filter(data_pedido__date__lte=data_fim_parsed)
        except ValueError:
            messages.error(request, 'Data de fim inválida.')
    
    # Estatísticas gerais
    stats_gerais = pedidos.aggregate(
        total_pedidos=Count('id'),
        valor_total=Sum('valor_total'),
        valor_medio=Avg('valor_total')
    )
    
    # Pedidos por status
    pedidos_por_status = pedidos.values('status').annotate(
        count=Count('id'),
        valor_total=Sum('valor_total')
    ).order_by('status')
    
    # Pedidos por prioridade
    pedidos_por_prioridade = pedidos.values('prioridade').annotate(
        count=Count('id'),
        valor_total=Sum('valor_total')
    ).order_by('prioridade')
    
    # Top 10 clientes por valor
    top_clientes_valor = Client.objects.annotate(
        total_pedidos=Count('pedidos', filter=Q(pedidos__in=pedidos)),
        valor_total=Sum('pedidos__valor_total', filter=Q(pedidos__in=pedidos))
    ).filter(total_pedidos__gt=0).order_by('-valor_total')[:10]
    
    # Top 10 clientes por quantidade
    top_clientes_quantidade = Client.objects.annotate(
        total_pedidos=Count('pedidos', filter=Q(pedidos__in=pedidos))
    ).filter(total_pedidos__gt=0).order_by('-total_pedidos')[:10]
    
    # Pedidos por mês (últimos 12 meses)
    from django.db.models.functions import TruncMonth
    pedidos_por_mes = pedidos.filter(
        data_pedido__gte=timezone.now() - timezone.timedelta(days=365)
    ).annotate(
        mes=TruncMonth('data_pedido')
    ).values('mes').annotate(
        count=Count('id'),
        valor_total=Sum('valor_total')
    ).order_by('mes')
    
    # Pedidos atrasados
    pedidos_atrasados = pedidos.filter(
        data_entrega_prevista__lt=timezone.now().date(),
        status__in=['pendente', 'processando', 'enviado']
    )
    
    return render(request, 'reports_pedidos.html', {
        'stats_gerais': stats_gerais,
        'pedidos_por_status': pedidos_por_status,
        'pedidos_por_prioridade': pedidos_por_prioridade,
        'top_clientes_valor': top_clientes_valor,
        'top_clientes_quantidade': top_clientes_quantidade,
        'pedidos_por_mes': pedidos_por_mes,
        'pedidos_atrasados': pedidos_atrasados,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'total_atrasados': pedidos_atrasados.count(),
    })

# ==================== VIEWS PARA RELATÓRIOS PDF ====================

@login_required
@group_required('Administradores', 'Gerentes', 'Funcionários')
def client_pdf_report(request, client_id):
    """
    Gerar relatório PDF de um cliente específico
    """
    client = get_object_or_404(Client, id=client_id)
    
    # Criar o HttpResponse object com PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cliente_{client.name}_{datetime.date.today()}.pdf"'
    
    # Criar o PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Título
    title = Paragraph(f"Relatório do Cliente: {client.name}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Informações do cliente
    client_data = [
        ['Nome:', client.name],
        ['Email:', client.email],
        ['Idade:', f'{client.age} anos'],
        ['Data do Relatório:', datetime.date.today().strftime('%d/%m/%Y')]
    ]
    
    client_table = Table(client_data, colWidths=[2*inch, 4*inch])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(client_table)
    elements.append(Spacer(1, 30))
    
    # Estatísticas dos pedidos
    pedidos_stats = client.pedidos.aggregate(
        total_pedidos=Count('id'),
        valor_total=Sum('valor_total'),
        valor_medio=Avg('valor_total')
    )
    
    stats_title = Paragraph("Estatísticas de Pedidos", styles['Heading2'])
    elements.append(stats_title)
    elements.append(Spacer(1, 12))
    
    stats_data = [
        ['Total de Pedidos:', str(pedidos_stats['total_pedidos'] or 0)],
        ['Valor Total:', f"R$ {pedidos_stats['valor_total'] or 0:.2f}"],
        ['Valor Médio:', f"R$ {pedidos_stats['valor_medio'] or 0:.2f}"]
    ]
    
    stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 30))
    
    # Lista de pedidos recentes (últimos 10)
    pedidos_recentes = client.pedidos.all().order_by('-data_pedido')[:10]
    
    if pedidos_recentes:
        pedidos_title = Paragraph("Pedidos Recentes", styles['Heading2'])
        elements.append(pedidos_title)
        elements.append(Spacer(1, 12))
        
        pedidos_data = [['Número', 'Data', 'Status', 'Valor']]
        
        for pedido in pedidos_recentes:
            pedidos_data.append([
                pedido.numero_pedido,
                pedido.data_pedido.strftime('%d/%m/%Y'),
                pedido.get_status_display(),
                f"R$ {pedido.valor_total:.2f}"
            ])
        
        pedidos_table = Table(pedidos_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        pedidos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(pedidos_table)
    
    # Construir o PDF
    doc.build(elements)
    
    # Obter o valor do buffer e escrever na response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response   
