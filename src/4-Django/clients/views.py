from django.contrib.auth.models import Group
from django.http import JsonResponse, HttpResponse
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
    PedidoSearchForm
)
from .permissions import group_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import datetime


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def get_clients(request):
    """
    Método para listar clientes com busca e paginação
    Todos os grupos autenticados podem visualizar
    """
    search_form = ClientSearchForm(request.GET)
    clients_list = Client.objects.all().order_by("name")

    # Aplicar filtros de busca se o formulário for válido
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get("search")
        age_min = search_form.cleaned_data.get("age_min")
        age_max = search_form.cleaned_data.get("age_max")

        if search_query:
            clients_list = clients_list.filter(
                Q(name__icontains=search_query) | Q(email__icontains=search_query)
            )

        if age_min:
            clients_list = clients_list.filter(age__gte=age_min)

        if age_max:
            clients_list = clients_list.filter(age__lte=age_max)

    # Configurar paginação
    paginator = Paginator(clients_list, 10)
    page_number = request.GET.get("page")
    clients = paginator.get_page(page_number)

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

    return render(
        request,
        "clients.html",
        {
            "clients": clients,
            "total_clients": clients_list.count(),
            "search_form": search_form,
            "can_create": can_create,
            "can_edit": can_edit,
            "can_delete": can_delete,
        },
    )


@login_required
@group_required("Administradores", "Gerentes")
def create_client(request):
    """
    Método para criar cliente usando ModelForm
    Apenas Administradores e Gerentes podem criar
    """
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            try:
                client = form.save()
                messages.success(request, f"Cliente {client.name} criado com sucesso!")
                return redirect("detail_client", id=client.id)
            except Exception as e:
                messages.error(request, f"Erro ao salvar cliente: {str(e)}")
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = ClientForm()

    return render(request, "create_client.html", {"form": form})


@login_required
@group_required("Administradores", "Gerentes")
def update_client(request, id):
    """
    Método para atualizar cliente usando ModelForm
    Apenas Administradores e Gerentes podem editar
    """
    client = get_object_or_404(Client, id=id)

    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            try:
                updated_client = form.save()
                messages.success(
                    request, f"Cliente {updated_client.name} atualizado com sucesso!"
                )
                return redirect("detail_client", id=updated_client.id)
            except Exception as e:
                messages.error(request, f"Erro ao atualizar cliente: {str(e)}")
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = ClientForm(instance=client)

    return render(request, "update_client.html", {"form": form, "client": client})


@login_required
@group_required("Administradores")
def delete_client(request, id):
    """
    Método para apagar um cliente com confirmação
    Apenas Administradores podem deletar
    """
    client = get_object_or_404(Client, id=id)

    if request.method == "POST":
        client_name = client.name
        try:
            client.delete()
            messages.success(
                request, f"Cliente {client_name} foi excluído com sucesso!"
            )
        except Exception as e:
            messages.error(request, f"Erro ao excluir cliente: {str(e)}")
        return redirect("clients")

    return render(request, "delete_client.html", {"client": client})


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def detail_client(request, id):
    """
    Método para exibir detalhes de um cliente COM seus pedidos
    Todos os grupos podem visualizar detalhes
    """
    client = get_object_or_404(Client, id=id)

    # Buscar pedidos do cliente com paginação
    pedidos_list = client.pedidos.all().order_by("-data_pedido")
    paginator = Paginator(pedidos_list, 5)  # 5 pedidos por página
    page_number = request.GET.get("page")
    pedidos = paginator.get_page(page_number)

    # Estatísticas dos pedidos do cliente
    pedidos_stats = client.pedidos.aggregate(
        total_pedidos=Count("id"),
        valor_total=Sum("valor_total"),
        valor_medio=Avg("valor_total"),
    )

    # Pedidos por status
    pedidos_por_status = (
        client.pedidos.values("status").annotate(count=Count("id")).order_by("status")
    )

    # Verificar permissões para mostrar botões na template
    user_groups = request.user.groups.values_list("name", flat=True)
    can_edit = (
        any(group in ["Administradores", "Gerentes"] for group in user_groups)
        or request.user.is_superuser
    )
    can_delete = "Administradores" in user_groups or request.user.is_superuser
    can_create_pedido = (
        any(group in ["Administradores", "Gerentes"] for group in user_groups)
        or request.user.is_superuser
    )

    return render(
        request,
        "detail_client.html",
        {
            "client": client,
            "pedidos": pedidos,
            "pedidos_stats": pedidos_stats,
            "pedidos_por_status": dict(
                pedidos_por_status.values_list("status", "count")
            ),
            "can_edit": can_edit,
            "can_delete": can_delete,
            "can_create_pedido": can_create_pedido,
        },
    )


@login_required
@group_required("Administradores")
def bulk_delete_clients(request):
    """
    Método para exclusão em lote de clientes
    Apenas Administradores podem fazer exclusão em lote
    """
    if request.method == "POST":
        client_ids = request.POST.getlist("client_ids[]")

        if client_ids:
            try:
                deleted_count = Client.objects.filter(id__in=client_ids).count()
                Client.objects.filter(id__in=client_ids).delete()
                messages.success(
                    request, f"{deleted_count} cliente(s) excluído(s) com sucesso!"
                )
            except Exception as e:
                messages.error(request, f"Erro ao excluir clientes: {str(e)}")
        else:
            messages.warning(request, "Nenhum cliente selecionado.")

    return redirect("clients")


# Views para gerenciamento de grupos
@login_required
@group_required("Administradores")
def manage_users(request):
    """
    View para gerenciar usuários e seus grupos
    Apenas Administradores podem acessar
    """
    from django.contrib.auth.models import User

    users = User.objects.all().prefetch_related("groups")
    groups = Group.objects.all()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        group_ids = request.POST.getlist("groups")

        try:
            user = User.objects.get(id=user_id)
            user.groups.clear()

            for group_id in group_ids:
                group = Group.objects.get(id=group_id)
                user.groups.add(group)

            messages.success(
                request, f"Grupos do usuário {user.username} atualizados com sucesso!"
            )
        except Exception as e:
            messages.error(request, f"Erro ao atualizar grupos: {str(e)}")

        return redirect("manage_users")

    return render(
        request,
        "manage_users.html",
        {
            "users": users,
            "groups": groups,
        },
    )


# ==================== VIEWS PARA PEDIDOS ====================


@login_required
def ajax_get_client_pedidos(request, client_id):
    """
    Obter pedidos de um cliente via AJAX
    """
    client = get_object_or_404(Client, id=client_id)
    pedidos = client.pedidos.all().order_by("-data_pedido")[:10]  # Últimos 10 pedidos

    pedidos_data = []
    for pedido in pedidos:
        pedidos_data.append(
            {
                "id": pedido.id,
                "numero_pedido": pedido.numero_pedido,
                "status": pedido.get_status_display(),
                "status_class": pedido.status_display_class,
                "valor_total": str(pedido.valor_total),
                "data_pedido": pedido.data_pedido.strftime("%d/%m/%Y"),
                "url": pedido.get_absolute_url(),
            }
        )

    return JsonResponse({"pedidos": pedidos_data, "client_name": client.name})

# ==================== VIEWS PARA RELATÓRIOS PDF ====================


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def client_pdf_report(request, client_id):
    """
    Gerar relatório PDF de um cliente específico
    """
    client = get_object_or_404(Client, id=client_id)

    # Criar o HttpResponse object com PDF headers
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="cliente_{client.name}_{datetime.date.today()}.pdf"'
    )

    # Criar o PDF
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
    title = Paragraph(f"Relatório do Cliente: {client.name}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Informações do cliente
    client_data = [
        ["Nome:", client.name],
        ["Email:", client.email],
        ["Idade:", f"{client.age} anos"],
        ["Data do Relatório:", datetime.date.today().strftime("%d/%m/%Y")],
    ]

    client_table = Table(client_data, colWidths=[2 * inch, 4 * inch])
    client_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.grey),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("BACKGROUND", (1, 0), (1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(client_table)
    elements.append(Spacer(1, 30))

    # Estatísticas dos pedidos
    pedidos_stats = client.pedidos.aggregate(
        total_pedidos=Count("id"),
        valor_total=Sum("valor_total"),
        valor_medio=Avg("valor_total"),
    )

    stats_title = Paragraph("Estatísticas de Pedidos", styles["Heading2"])
    elements.append(stats_title)
    elements.append(Spacer(1, 12))

    stats_data = [
        ["Total de Pedidos:", str(pedidos_stats["total_pedidos"] or 0)],
        ["Valor Total:", f"R$ {pedidos_stats['valor_total'] or 0:.2f}"],
        ["Valor Médio:", f"R$ {pedidos_stats['valor_medio'] or 0:.2f}"],
    ]

    stats_table = Table(stats_data, colWidths=[2 * inch, 2 * inch])
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

    # Lista de pedidos recentes (últimos 10)
    pedidos_recentes = client.pedidos.all().order_by("-data_pedido")[:10]

    if pedidos_recentes:
        pedidos_title = Paragraph("Pedidos Recentes", styles["Heading2"])
        elements.append(pedidos_title)
        elements.append(Spacer(1, 12))

        pedidos_data = [["Número", "Data", "Status", "Valor"]]

        for pedido in pedidos_recentes:
            pedidos_data.append(
                [
                    pedido.numero_pedido,
                    pedido.data_pedido.strftime("%d/%m/%Y"),
                    pedido.get_status_display(),
                    f"R$ {pedido.valor_total:.2f}",
                ]
            )

        pedidos_table = Table(
            pedidos_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]
        )
        pedidos_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(pedidos_table)

    # Construir o PDF
    doc.build(elements)

    # Obter o valor do buffer e escrever na response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response


@login_required
@group_required("Administradores", "Gerentes")
def dashboard_pdf_report(request):
    """
    Gerar relatório PDF do dashboard com estatísticas gerais
    """
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="dashboard_relatorio_{datetime.date.today()}.pdf"'
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
    )

    # Título
    title = Paragraph("Relatório Dashboard - Visão Geral", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Estatísticas gerais de pedidos
    stats_gerais = Pedido.get_revenue_statistics()
    stats_status = Pedido.get_status_statistics()

    # Seção de estatísticas gerais
    stats_title = Paragraph("Estatísticas Gerais", styles["Heading2"])
    elements.append(stats_title)
    elements.append(Spacer(1, 12))

    stats_data = [
        ["Total de Pedidos:", str(stats_gerais.get("total_pedidos", 0))],
        ["Receita Total:", f"R$ {stats_gerais.get('receita_total', 0):.2f}"],
        ["Ticket Médio:", f"R$ {stats_gerais.get('ticket_medio', 0):.2f}"],
        ["Total de Clientes:", str(Client.objects.count())],
        ["Data do Relatório:", datetime.date.today().strftime("%d/%m/%Y")],
    ]

    stats_table = Table(stats_data, colWidths=[2.5 * inch, 2.5 * inch])
    stats_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(stats_table)
    elements.append(Spacer(1, 30))

    # Pedidos por status
    status_title = Paragraph("Pedidos por Status", styles["Heading2"])
    elements.append(status_title)
    elements.append(Spacer(1, 12))

    status_data = [["Status", "Quantidade"]]
    for status_info in stats_status:
        status_data.append([status_info["status_display"], str(status_info["count"])])

    status_table = Table(status_data, colWidths=[2 * inch, 1.5 * inch])
    status_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(status_table)
    elements.append(Spacer(1, 30))

    # Top 5 clientes
    top_clientes = (
        Client.objects.annotate(total_pedidos=Count("pedidos"))
        .filter(total_pedidos__gt=0)
        .order_by("-total_pedidos")[:5]
    )

    if top_clientes:
        clientes_title = Paragraph(
            "Top 5 Clientes (Por Quantidade de Pedidos)", styles["Heading2"]
        )
        elements.append(clientes_title)
        elements.append(Spacer(1, 12))

        clientes_data = [["Cliente", "Total de Pedidos"]]
        for cliente in top_clientes:
            clientes_data.append([cliente.name, str(cliente.total_pedidos)])

        clientes_table = Table(clientes_data, colWidths=[3 * inch, 1.5 * inch])
        clientes_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(clientes_table)

    # Construir o PDF
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response


# ==================== INTEGRAÇÃO COM API VIACEP ====================

import requests
import csv
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json


@login_required
@csrf_exempt
def get_address_by_cep(request):
    """
    Buscar endereço via API ViaCEP
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cep = data.get("cep", "").replace("-", "").replace(" ", "")

            if not cep or len(cep) != 8:
                return JsonResponse(
                    {"success": False, "message": "CEP deve ter 8 dígitos"}
                )

            # Fazer requisição para a API ViaCEP
            response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=10)

            if response.status_code == 200:
                address_data = response.json()

                # Verificar se o CEP foi encontrado
                if "erro" in address_data:
                    return JsonResponse(
                        {"success": False, "message": "CEP não encontrado"}
                    )

                return JsonResponse(
                    {
                        "success": True,
                        "data": {
                            "logradouro": address_data.get("logradouro", ""),
                            "bairro": address_data.get("bairro", ""),
                            "cidade": address_data.get("localidade", ""),
                            "uf": address_data.get("uf", ""),
                            "cep": address_data.get("cep", ""),
                            "complemento": address_data.get("complemento", ""),
                            "ibge": address_data.get("ibge", ""),
                            "gia": address_data.get("gia", ""),
                            "ddd": address_data.get("ddd", ""),
                            "siafi": address_data.get("siafi", ""),
                        },
                    }
                )
            else:
                return JsonResponse(
                    {"success": False, "message": "Erro ao consultar CEP"}
                )

        except requests.RequestException as e:
            return JsonResponse(
                {"success": False, "message": f"Erro de conexão: {str(e)}"}
            )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Dados inválidos"})
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Erro interno: {str(e)}"}
            )

    return JsonResponse({"success": False, "message": "Método não permitido"})


# ==================== EXPORTAÇÃO CSV ====================


@login_required
@group_required("Administradores", "Gerentes", "Funcionários")
def export_clients_csv(request):
    """
    Exportar lista de clientes para CSV
    """
    # Aplicar os mesmos filtros da view get_clients
    search_form = ClientSearchForm(request.GET)
    clients_list = Client.objects.all().order_by("name")

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get("search")
        age_min = search_form.cleaned_data.get("age_min")
        age_max = search_form.cleaned_data.get("age_max")

        if search_query:
            clients_list = clients_list.filter(
                Q(name__icontains=search_query) | Q(email__icontains=search_query)
            )

        if age_min:
            clients_list = clients_list.filter(age__gte=age_min)

        if age_max:
            clients_list = clients_list.filter(age__lte=age_max)

    # Criar resposta CSV
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="clientes_{datetime.date.today()}.csv"'
    )

    # Adicionar BOM para UTF-8 (compatibilidade com Excel)
    response.write("\ufeff")

    writer = csv.writer(response, delimiter=";")

    # Cabeçalho
    writer.writerow(
        [
            "ID",
            "Nome",
            "Email",
            "Idade",
            "Data de Cadastro",
            "Total de Pedidos",
            "Valor Total em Pedidos",
        ]
    )

    # Dados dos clientes
    for client in clients_list:
        # Estatísticas do cliente
        pedidos_stats = client.pedidos.aggregate(
            total_pedidos=Count("id"), valor_total=Sum("valor_total")
        )

        writer.writerow(
            [
                client.id,
                client.name,
                client.email,
                client.age,
                (
                    client.created_at.strftime("%d/%m/%Y %H:%M")
                    if hasattr(client, "created_at")
                    else "N/A"
                ),
                pedidos_stats["total_pedidos"] or 0,
                f"{pedidos_stats['valor_total'] or 0:.2f}".replace(
                    ".", ","
                ),  # Formato brasileiro
            ]
        )

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


@login_required
@group_required("Administradores", "Gerentes")
def export_dashboard_csv(request):
    """
    Exportar dados do dashboard para CSV
    """
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="dashboard_{datetime.date.today()}.csv"'
    )

    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")

    # Estatísticas gerais
    stats_gerais = Pedido.get_revenue_statistics()
    stats_status = Pedido.get_status_statistics()

    # Seção 1: Estatísticas Gerais
    writer.writerow(["=== ESTATÍSTICAS GERAIS ==="])
    writer.writerow(["Métrica", "Valor"])
    writer.writerow(["Total de Pedidos", stats_gerais.get("total_pedidos", 0)])
    writer.writerow(
        [
            "Receita Total",
            f"R$ {stats_gerais.get('receita_total', 0):.2f}".replace(".", ","),
        ]
    )
    writer.writerow(
        [
            "Ticket Médio",
            f"R$ {stats_gerais.get('ticket_medio', 0):.2f}".replace(".", ","),
        ]
    )
    writer.writerow(["Total de Clientes", Client.objects.count()])
    writer.writerow(["Data do Relatório", datetime.date.today().strftime("%d/%m/%Y")])
    writer.writerow([])  # Linha em branco

    # Seção 2: Pedidos por Status
    writer.writerow(["=== PEDIDOS POR STATUS ==="])
    writer.writerow(["Status", "Quantidade"])
    for status_info in stats_status:
        writer.writerow([status_info["status_display"], status_info["count"]])
    writer.writerow([])

    # Seção 3: Top Clientes
    top_clientes = (
        Client.objects.annotate(
            total_pedidos=Count("pedidos"), valor_total=Sum("pedidos__valor_total")
        )
        .filter(total_pedidos__gt=0)
        .order_by("-total_pedidos")[:10]
    )

    writer.writerow(["=== TOP 10 CLIENTES ==="])
    writer.writerow(["Cliente", "Total de Pedidos", "Valor Total"])
    for cliente in top_clientes:
        writer.writerow(
            [
                cliente.name,
                cliente.total_pedidos,
                f"{cliente.valor_total or 0:.2f}".replace(".", ","),
            ]
        )

    return response
