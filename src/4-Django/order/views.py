from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Pedido
from .forms import PedidoForm, PedidoSearchForm, PedidoStatusForm, PedidoBulkActionForm
from .permissions import group_required
from clients.models import Client
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from datetime import datetime
import csv


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def get_pedidos(request):
    """
    Listar pedidos com busca avançada e paginação
    Todos os grupos autenticados podem visualizar
    """
    search_form = PedidoSearchForm(request.GET)
    pedidos_list = Pedido.objects.select_related("cliente").order_by("-data_pedido")

    # Aplicar filtros de busca se o formulário for válido
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get("search")
        cliente = search_form.cleaned_data.get("cliente")
        status = search_form.cleaned_data.get("status")
        prioridade = search_form.cleaned_data.get("prioridade")
        data_inicio = search_form.cleaned_data.get("data_inicio")
        data_fim = search_form.cleaned_data.get("data_fim")
        valor_min = search_form.cleaned_data.get("valor_min")
        valor_max = search_form.cleaned_data.get("valor_max")

        # Filtro de busca textual
        if search_query:
            pedidos_list = pedidos_list.filter(
                Q(numero_pedido__icontains=search_query)
                | Q(cliente__name__icontains=search_query)
                | Q(descricao__icontains=search_query)
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
        total_pedidos=Count("id"),
        valor_total=Sum("valor_total"),
        valor_medio=Avg("valor_total"),
    )

    # Configurar paginação
    paginator = Paginator(pedidos_list, 15)  # 15 pedidos por página
    page_number = request.GET.get("page")
    pedidos = paginator.get_page(page_number)

    # Verificar permissões para mostrar botões na template
    user_groups = request.user.groups.values_list("name", flat=True)
    can_create = (
        any(group in ["Administradores", "Gerentes"] for group in user_groups)
        or request.user.is_superuser
    )
    can_edit = (
        any(group in ["Administradores", "Gerentes"] for group in user_groups)
        or request.user.is_superuser
    )
    can_delete = "Administradores" in user_groups or request.user.is_superuser
    can_bulk_actions = "Administradores" in user_groups or request.user.is_superuser

    return render(
        request,
        "pedidos.html",
        {
            "pedidos": pedidos,
            "search_form": search_form,
            "stats": stats,
            "can_create": can_create,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "can_bulk_actions": can_bulk_actions,
        },
    )


@login_required
@group_required("Administradores", "Gerentes")
def create_pedido(request):
    """
    Criar novo pedido
    Apenas Administradores e Gerentes podem criar
    """
    if request.method == "POST":
        form = PedidoForm(request.POST)
        if form.is_valid():
            try:
                pedido = form.save()
                messages.success(
                    request, f"Pedido {pedido.numero_pedido} criado com sucesso!"
                )
                return redirect("detail_pedido", id=pedido.id)
            except Exception as e:
                messages.error(request, f"Erro ao salvar pedido: {str(e)}")
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = PedidoForm()

    return render(request, "create_pedido.html", {"form": form})


@login_required
@group_required("Administradores", "Gerentes")
def update_pedido(request, id):
    """
    Atualizar pedido existente
    Apenas Administradores e Gerentes podem editar
    """
    pedido = get_object_or_404(Pedido, id=id)

    if request.method == "POST":
        form = PedidoForm(request.POST, instance=pedido)
        if form.is_valid():
            try:
                updated_pedido = form.save()
                messages.success(
                    request,
                    f"Pedido {updated_pedido.numero_pedido} atualizado com sucesso!",
                )
                return redirect("detail_pedido", id=updated_pedido.id)
            except Exception as e:
                messages.error(request, f"Erro ao atualizar pedido: {str(e)}")
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = PedidoForm(instance=pedido)

    return render(request, "update_pedido.html", {"form": form, "pedido": pedido})


@login_required
@group_required("Administradores")
def delete_pedido(request, id):
    """
    Excluir pedido com confirmação
    Apenas Administradores podem deletar
    """
    pedido = get_object_or_404(Pedido, id=id)

    if request.method == "POST":
        numero_pedido = pedido.numero_pedido
        try:
            pedido.delete()
            messages.success(
                request, f"Pedido {numero_pedido} foi excluído com sucesso!"
            )
        except Exception as e:
            messages.error(request, f"Erro ao excluir pedido: {str(e)}")
        return redirect("pedidos")

    return render(request, "delete_pedido.html", {"pedido": pedido})


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def detail_pedido(request, id):
    """
    Exibir detalhes de um pedido
    Todos os grupos podem visualizar detalhes
    """
    pedido = get_object_or_404(Pedido, id=id)

    # Verificar permissões para mostrar botões na template
    user_groups = request.user.groups.values_list("name", flat=True)
    can_edit = (
        any(group in ["Administradores", "Gerentes"] for group in user_groups)
        or request.user.is_superuser
    )
    can_delete = "Administradores" in user_groups or request.user.is_superuser
    can_change_status = (
        any(
            group in ["Administradores", "Gerentes", "Funcionários"]
            for group in user_groups
        )
        or request.user.is_superuser
    )

    return render(
        request,
        "detail_pedido.html",
        {
            "pedido": pedido,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "can_change_status": can_change_status,
        },
    )


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def update_pedido_status(request, id):
    """
    Atualizar apenas o status do pedido (formulário rápido)
    Todos os grupos autenticados podem alterar status
    """
    pedido = get_object_or_404(Pedido, id=id)

    if request.method == "POST":
        form = PedidoStatusForm(request.POST)
        if form.is_valid():
            try:
                novo_status = form.cleaned_data["status"]
                observacao = form.cleaned_data.get("observacao", "")

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
                    f"Status do pedido {pedido.numero_pedido} atualizado para {pedido.get_status_display()}!",
                )
                return redirect("detail_pedido", id=pedido.id)
            except Exception as e:
                messages.error(request, f"Erro ao atualizar status: {str(e)}")
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = PedidoStatusForm(initial={"status": pedido.status})

    return render(
        request, "update_pedido_status.html", {"form": form, "pedido": pedido}
    )


@login_required
@group_required("Administradores", "Gerentes")
def cancel_pedido(request, id):
    """
    Cancelar pedido com motivo
    Apenas Administradores e Gerentes podem cancelar
    """
    pedido = get_object_or_404(Pedido, id=id)

    if not pedido.can_be_cancelled():
        messages.error(request, "Este pedido não pode ser cancelado.")
        return redirect("detail_pedido", id=pedido.id)

    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()
        try:
            pedido.cancel_order(motivo)
            messages.success(
                request, f"Pedido {pedido.numero_pedido} foi cancelado com sucesso!"
            )
            return redirect("detail_pedido", id=pedido.id)
        except Exception as e:
            messages.error(request, f"Erro ao cancelar pedido: {str(e)}")

    return render(request, "cancel_pedido.html", {"pedido": pedido})


@login_required
@group_required("Administradores")
def bulk_actions_pedidos(request):
    """
    Ações em lote para pedidos
    Apenas Administradores podem fazer ações em lote
    """
    if request.method == "POST":
        form = PedidoBulkActionForm(request.POST)
        pedido_ids = request.POST.getlist("pedido_ids[]")

        if not pedido_ids:
            messages.warning(request, "Nenhum pedido selecionado.")
            return redirect("pedidos")

        if form.is_valid():
            action = form.cleaned_data["action"]

            try:
                pedidos = Pedido.objects.filter(id__in=pedido_ids)
                count = pedidos.count()

                if action == "update_status":
                    new_status = form.cleaned_data["new_status"]
                    pedidos.update(status=new_status)
                    messages.success(
                        request,
                        f"{count} pedido(s) tiveram o status atualizado para {dict(Pedido.STATUS_CHOICES)[new_status]}!",
                    )

                elif action == "update_priority":
                    new_priority = form.cleaned_data["new_priority"]
                    pedidos.update(prioridade=new_priority)
                    messages.success(
                        request,
                        f"{count} pedido(s) tiveram a prioridade atualizada para {dict(Pedido.PRIORIDADE_CHOICES)[new_priority]}!",
                    )

                elif action == "delete":
                    pedidos.delete()
                    messages.success(
                        request, f"{count} pedido(s) excluído(s) com sucesso!"
                    )

            except Exception as e:
                messages.error(request, f"Erro ao executar ação em lote: {str(e)}")
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")

    return redirect("pedidos")


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def dashboard_pedidos(request):
    """
    Dashboard com estatísticas de pedidos
    Todos os grupos podem visualizar
    """
    # Estatísticas gerais
    stats_gerais = Pedido.get_revenue_statistics()
    stats_status = Pedido.get_status_statistics()

    # Pedidos por prioridade
    stats_prioridade = (
        Pedido.objects.values("prioridade")
        .annotate(count=Count("id"))
        .order_by("prioridade")
    )

    # Pedidos atrasados
    pedidos_atrasados = Pedido.objects.filter(
        data_entrega_prevista__lt=timezone.now().date(),
        status__in=["pendente", "processando", "enviado"],
    ).count()

    # Pedidos do mês atual
    inicio_mes = timezone.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    pedidos_mes = Pedido.objects.filter(data_pedido__gte=inicio_mes)

    # Top 5 clientes por quantidade de pedidos
    top_clientes = (
        Client.objects.annotate(total_pedidos=Count("pedidos"))
        .filter(total_pedidos__gt=0)
        .order_by("-total_pedidos")[:5]
    )

    return render(
        request,
        "dashboard_pedidos.html",
        {
            "stats_gerais": stats_gerais,
            "stats_status": stats_status,
            "stats_prioridade": dict(
                stats_prioridade.values_list("prioridade", "count")
            ),
            "pedidos_atrasados": pedidos_atrasados,
            "pedidos_mes_count": pedidos_mes.count(),
            "top_clientes": top_clientes,
        },
    )


# ==================== AJAX VIEWS ====================


@login_required
@require_POST
def ajax_update_pedido_status(request, id):
    """
    Atualizar status via AJAX para interface mais fluida
    """
    pedido = get_object_or_404(Pedido, id=id)

    # Verificar permissões
    user_groups = request.user.groups.values_list("name", flat=True)
    if not (
        any(
            group in ["Administradores", "Gerentes", "Funcionários"]
            for group in user_groups
        )
        or request.user.is_superuser
    ):
        return JsonResponse({"success": False, "message": "Sem permissão"}, status=403)

    try:
        novo_status = request.POST.get("status")
        if novo_status not in dict(Pedido.STATUS_CHOICES):
            return JsonResponse({"success": False, "message": "Status inválido"})

        pedido.status = novo_status
        pedido.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Status atualizado para {pedido.get_status_display()}",
                "new_status": novo_status,
                "new_status_display": pedido.get_status_display(),
                "status_class": pedido.status_display_class,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})

# ================ Views adicionais para interação ================

@login_required
@group_required("Administradores", "Gerentes")
def create_pedido_for_client(request, client_id):
    """
    Criar pedido para um cliente específico
    Apenas Administradores e Gerentes podem criar
    """
    client = get_object_or_404(Client, id=client_id)

    if request.method == "POST":
        form = PedidoForm(request.POST)
        if form.is_valid():
            try:
                pedido = form.save(commit=False)
                pedido.cliente = client  # Definir o cliente automaticamente
                pedido.save()
                messages.success(
                    request,
                    f"Pedido {pedido.numero_pedido} criado com sucesso para {client.name}!",
                )
                return redirect("detail_pedido", id=pedido.id)
            except Exception as e:
                messages.error(request, f"Erro ao salvar pedido: {str(e)}")
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        # Inicializar formulário com cliente pré-selecionado
        form = PedidoForm(initial={"cliente": client})
        # Desabilitar campo cliente para que não possa ser alterado
        form.fields["cliente"].widget.attrs["readonly"] = True
        form.fields["cliente"].disabled = True

    return render(
        request, "create_pedido_for_client.html", {"form": form, "client": client}
    )


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def client_pedidos(request, client_id):
    """
    Listar todos os pedidos de um cliente específico
    Todos os grupos podem visualizar
    """
    client = get_object_or_404(Client, id=client_id)

    # Filtros específicos para pedidos do cliente
    status_filter = request.GET.get("status", "")
    prioridade_filter = request.GET.get("prioridade", "")

    pedidos_list = client.pedidos.all().order_by("-data_pedido")

    if status_filter:
        pedidos_list = pedidos_list.filter(status=status_filter)

    if prioridade_filter:
        pedidos_list = pedidos_list.filter(prioridade=prioridade_filter)

    # Paginação
    paginator = Paginator(pedidos_list, 10)
    page_number = request.GET.get("page")
    pedidos = paginator.get_page(page_number)

    # Estatísticas
    stats = pedidos_list.aggregate(
        total_pedidos=Count("id"),
        valor_total=Sum("valor_total"),
        valor_medio=Avg("valor_total"),
    )

    # Verificar permissões
    user_groups = request.user.groups.values_list("name", flat=True)
    can_create = (
        any(group in ["Administradores", "Gerentes"] for group in user_groups)
        or request.user.is_superuser
    )
    can_edit = (
        any(group in ["Administradores", "Gerentes"] for group in user_groups)
        or request.user.is_superuser
    )

    return render(
        request,
        "client_pedidos.html",
        {
            "client": client,
            "pedidos": pedidos,
            "stats": stats,
            "status_choices": Pedido.STATUS_CHOICES,
            "prioridade_choices": Pedido.PRIORIDADE_CHOICES,
            "current_status": status_filter,
            "current_prioridade": prioridade_filter,
            "can_create": can_create,
            "can_edit": can_edit,
        },
    )


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def reports_pedidos(request):
    """
    Relatórios e análises de pedidos
    Todos os grupos podem visualizar
    """
    # Filtros de data para relatórios
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")

    # Query base
    pedidos = Pedido.objects.all()

    # Aplicar filtros de data se fornecidos
    if data_inicio:
        try:
            data_inicio_parsed = timezone.datetime.strptime(
                data_inicio, "%Y-%m-%d"
            ).date()
            pedidos = pedidos.filter(data_pedido__date__gte=data_inicio_parsed)
        except ValueError:
            messages.error(request, "Data de início inválida.")

    if data_fim:
        try:
            data_fim_parsed = timezone.datetime.strptime(data_fim, "%Y-%m-%d").date()
            pedidos = pedidos.filter(data_pedido__date__lte=data_fim_parsed)
        except ValueError:
            messages.error(request, "Data de fim inválida.")

    # Estatísticas gerais
    stats_gerais = pedidos.aggregate(
        total_pedidos=Count("id"),
        valor_total=Sum("valor_total"),
        valor_medio=Avg("valor_total"),
    )

    # Pedidos por status
    pedidos_por_status = (
        pedidos.values("status")
        .annotate(count=Count("id"), valor_total=Sum("valor_total"))
        .order_by("status")
    )

    # Pedidos por prioridade
    pedidos_por_prioridade = (
        pedidos.values("prioridade")
        .annotate(count=Count("id"), valor_total=Sum("valor_total"))
        .order_by("prioridade")
    )

    # Top 10 clientes por valor
    top_clientes_valor = (
        Client.objects.annotate(
            total_pedidos=Count("pedidos", filter=Q(pedidos__in=pedidos)),
            valor_total=Sum("pedidos__valor_total", filter=Q(pedidos__in=pedidos)),
        )
        .filter(total_pedidos__gt=0)
        .order_by("-valor_total")[:10]
    )

    # Top 10 clientes por quantidade
    top_clientes_quantidade = (
        Client.objects.annotate(
            total_pedidos=Count("pedidos", filter=Q(pedidos__in=pedidos))
        )
        .filter(total_pedidos__gt=0)
        .order_by("-total_pedidos")[:10]
    )

    # Pedidos por mês (últimos 12 meses)
    from django.db.models.functions import TruncMonth

    pedidos_por_mes = (
        pedidos.filter(data_pedido__gte=timezone.now() - timezone.timedelta(days=365))
        .annotate(mes=TruncMonth("data_pedido"))
        .values("mes")
        .annotate(count=Count("id"), valor_total=Sum("valor_total"))
        .order_by("mes")
    )

    # Pedidos atrasados
    pedidos_atrasados = pedidos.filter(
        data_entrega_prevista__lt=timezone.now().date(),
        status__in=["pendente", "processando", "enviado"],
    )

    return render(
        request,
        "reports_pedidos.html",
        {
            "stats_gerais": stats_gerais,
            "pedidos_por_status": pedidos_por_status,
            "pedidos_por_prioridade": pedidos_por_prioridade,
            "top_clientes_valor": top_clientes_valor,
            "top_clientes_quantidade": top_clientes_quantidade,
            "pedidos_por_mes": pedidos_por_mes,
            "pedidos_atrasados": pedidos_atrasados,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "total_atrasados": pedidos_atrasados.count(),
        },
    )

@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def pedidos_pdf_report(request):
    """
    Gerar relatório PDF de pedidos com filtros
    """
    # Obter parâmetros de filtro da URL
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    status = request.GET.get("status", "")
    prioridade = request.GET.get("prioridade", "")

    # Query base
    pedidos = Pedido.objects.select_related("cliente").all()

    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio_parsed = datetime.datetime.strptime(
                data_inicio, "%Y-%m-%d"
            ).date()
            pedidos = pedidos.filter(data_pedido__date__gte=data_inicio_parsed)
        except ValueError:
            pass

    if data_fim:
        try:
            data_fim_parsed = datetime.datetime.strptime(data_fim, "%Y-%m-%d").date()
            pedidos = pedidos.filter(data_pedido__date__lte=data_fim_parsed)
        except ValueError:
            pass

    if status:
        pedidos = pedidos.filter(status=status)

    if prioridade:
        pedidos = pedidos.filter(prioridade=prioridade)

    pedidos = pedidos.order_by("-data_pedido")

    # Criar o PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="relatorio_pedidos_{datetime.date.today()}.pdf"'
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
    )

    # Título
    title = Paragraph("Relatório de Pedidos", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Informações do filtro
    filter_info = []
    if data_inicio:
        filter_info.append(f"Data Início: {data_inicio}")
    if data_fim:
        filter_info.append(f"Data Fim: {data_fim}")
    if status:
        filter_info.append(f"Status: {dict(Pedido.STATUS_CHOICES).get(status, status)}")
    if prioridade:
        filter_info.append(
            f"Prioridade: {dict(Pedido.PRIORIDADE_CHOICES).get(prioridade, prioridade)}"
        )

    if filter_info:
        filter_text = "Filtros aplicados: " + " | ".join(filter_info)
        filter_para = Paragraph(filter_text, styles["Normal"])
        elements.append(filter_para)
        elements.append(Spacer(1, 20))

    # Estatísticas
    stats = pedidos.aggregate(
        total_pedidos=Count("id"),
        valor_total=Sum("valor_total"),
        valor_medio=Avg("valor_total"),
    )

    stats_title = Paragraph("Resumo Estatístico", styles["Heading2"])
    elements.append(stats_title)
    elements.append(Spacer(1, 12))

    stats_data = [
        ["Total de Pedidos:", str(stats["total_pedidos"] or 0)],
        ["Valor Total:", f"R$ {stats['valor_total'] or 0:.2f}"],
        ["Valor Médio:", f"R$ {stats['valor_medio'] or 0:.2f}"],
        ["Data do Relatório:", datetime.date.today().strftime("%d/%m/%Y")],
    ]

    stats_table = Table(stats_data, colWidths=[2 * inch, 3 * inch])
    stats_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(stats_table)
    elements.append(Spacer(1, 30))

    # Lista de pedidos (limitado a 50 para não sobrecarregar o PDF)
    pedidos_lista = pedidos[:50]

    if pedidos_lista:
        pedidos_title = Paragraph("Lista de Pedidos", styles["Heading2"])
        elements.append(pedidos_title)
        elements.append(Spacer(1, 12))

        # Cabeçalho da tabela
        pedidos_data = [["Número", "Cliente", "Data", "Status", "Prioridade", "Valor"]]

        for pedido in pedidos_lista:
            pedidos_data.append(
                [
                    pedido.numero_pedido,
                    (
                        pedido.cliente.name[:20] + "..."
                        if len(pedido.cliente.name) > 20
                        else pedido.cliente.name
                    ),
                    pedido.data_pedido.strftime("%d/%m/%Y"),
                    pedido.get_status_display(),
                    pedido.get_prioridade_display(),
                    f"R$ {pedido.valor_total:.2f}",
                ]
            )

        pedidos_table = Table(
            pedidos_data,
            colWidths=[1 * inch, 1.5 * inch, 1 * inch, 1 * inch, 1 * inch, 1 * inch],
        )
        pedidos_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(pedidos_table)

        if pedidos.count() > 50:
            warning_text = f"Nota: Exibindo apenas os primeiros 50 pedidos de {pedidos.count()} encontrados."
            warning_para = Paragraph(warning_text, styles["Normal"])
            elements.append(Spacer(1, 12))
            elements.append(warning_para)

    # Construir o PDF
    doc.build(elements)

    # Retornar resposta
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def export_pedidos_csv(request):
    """
    Exportar lista de pedidos para CSV com filtros
    """
    # Aplicar os mesmos filtros da view get_pedidos
    search_form = PedidoSearchForm(request.GET)
    pedidos_list = Pedido.objects.select_related("cliente").order_by("-data_pedido")

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get("search")
        cliente = search_form.cleaned_data.get("cliente")
        status = search_form.cleaned_data.get("status")
        prioridade = search_form.cleaned_data.get("prioridade")
        data_inicio = search_form.cleaned_data.get("data_inicio")
        data_fim = search_form.cleaned_data.get("data_fim")
        valor_min = search_form.cleaned_data.get("valor_min")
        valor_max = search_form.cleaned_data.get("valor_max")

        if search_query:
            pedidos_list = pedidos_list.filter(
                Q(numero_pedido__icontains=search_query)
                | Q(cliente__name__icontains=search_query)
                | Q(descricao__icontains=search_query)
            )

        if cliente:
            pedidos_list = pedidos_list.filter(cliente=cliente)

        if status:
            pedidos_list = pedidos_list.filter(status=status)

        if prioridade:
            pedidos_list = pedidos_list.filter(prioridade=prioridade)

        if data_inicio:
            pedidos_list = pedidos_list.filter(data_pedido__date__gte=data_inicio)

        if data_fim:
            pedidos_list = pedidos_list.filter(data_pedido__date__lte=data_fim)

        if valor_min is not None:
            pedidos_list = pedidos_list.filter(valor_total__gte=valor_min)

        if valor_max is not None:
            pedidos_list = pedidos_list.filter(valor_total__lte=valor_max)

    # Criar resposta CSV
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="pedidos_{datetime.date.today()}.csv"'
    )

    # Adicionar BOM para UTF-8
    response.write("\ufeff")

    writer = csv.writer(response, delimiter=";")

    # Cabeçalho
    writer.writerow(
        [
            "ID",
            "Número do Pedido",
            "Cliente",
            "Email do Cliente",
            "Data do Pedido",
            "Data de Entrega Prevista",
            "Status",
            "Prioridade",
            "Valor Total",
            "Descrição",
            "Observações",
        ]
    )

    # Dados dos pedidos
    for pedido in pedidos_list:
        writer.writerow(
            [
                pedido.id,
                pedido.numero_pedido,
                pedido.cliente.name,
                pedido.cliente.email,
                pedido.data_pedido.strftime("%d/%m/%Y %H:%M"),
                (
                    pedido.data_entrega_prevista.strftime("%d/%m/%Y")
                    if pedido.data_entrega_prevista
                    else "N/A"
                ),
                pedido.get_status_display(),
                pedido.get_prioridade_display(),
                f"{pedido.valor_total:.2f}".replace(".", ","),
                pedido.descricao or "",
                pedido.observacoes or "",
            ]
        )

    return response
