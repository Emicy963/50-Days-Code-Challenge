from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User, Group
from django.db.models import Count, Sum
from django.utils import timezone
from clients.models import Client, Pedido
from .serializers import (
    ClientListSerializer,
    ClientStatsSerializer,
    ClientCreateUpdateSerializer,
    ClientDetailSerializer,
    PedidoListSerializer,
    UserSerializer,
    GroupSerializer,
    DashboardStatsSerializer,
)
from .permissions import GroupPermission


class StandardResultsSetPagination(PageNumberPagination):
    """Paginação padrão para a API"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de clientes

    Operações disponíveis:
    - list: Listar clientes com busca e filtros
    - create: Criar novo cliente (Admin/Gerente)
    - retrieve: Obter detalhes de um cliente
    - update: Atualizar cliente (Admin/Gerente)
    - partial_update: Atualização parcial (Admin/Gerente)
    - destroy: Excluir cliente (Admin apenas)
    - pedidos: Listar pedidos de um cliente
    - stats: Estatísticas de clientes
    - bulk_delete: Exclusão em lote (Admin apenas)
    """

    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated, GroupPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["age"]
    search_fields = ["name", "email"]
    ordering_fields = ["name", "email", "age", "created_at"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return ClientListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ClientCreateUpdateSerializer
        return ClientDetailSerializer

    def get_permissions(self):
        """
        Permissões baseadas na ação:
        - list, retrieve: todos os grupos
        - create, update, partial_update: Admin/Gerente
        - destroy, bulk_delete: Admin apenas
        """
        permission_classes = [IsAuthenticated]

        if self.action in ["create", "update", "partial_update"]:
            permission_classes.append(GroupPermission)
            self.required_groups = ["Administradores", "Gerentes"]
        elif self.action in ["destroy", "bulk_delete"]:
            permission_classes.append(GroupPermission)
            self.required_groups = ["Administradores"]
        else:
            permission_classes.append(GroupPermission)
            self.required_groups = ["Administradores", "Gerentes", "Funcionários"]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = Client.objects.all()

        # Filtros adicionais via query params
        age_min = self.request.query_params.get("age_min")
        age_max = self.request.query_params.get("age_max")

        if age_min:
            queryset = queryset.filter(age__gte=age_min)
        if age_max:
            queryset = queryset.filter(age__lte=age_max)

        return queryset

    @action(detail=True, methods=["get"])
    def pedidos(self, request, pk=None):
        """
        Listar pedidos de um cliente específico
        GET /api/clients/{id}/pedidos/
        """
        client = self.get_object()
        pedidos = client.pedidos.all().order_by("-data_pedido")

        # Filtros específicos para pedidos
        status_filter = request.query_params.get("status")
        prioridade_filter = request.query_params.get("prioridade")

        if status_filter:
            pedidos = pedidos.filter(status=status_filter)
        if prioridade_filter:
            pedidos = pedidos.filter(prioridade=prioridade_filter)

        page = self.paginate_queryset(pedidos)
        if page is not None:
            serializer = PedidoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PedidoListSerializer(pedidos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Estatísticas gerais de clientes
        GET /api/clients/stats/
        """
        stats = Client.get_age_statistics()

        # Estatísticas por faixa etária
        age_groups = {}
        for client in Client.objects.all():
            group = client.get_age_group()
            age_groups[group] = age_groups.get(group, 0) + 1

        stats["age_groups"] = age_groups

        serializer = ClientStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """
        Exclusão em lote de clientes
        POST /api/clients/bulk_delete/
        Body: {"client_ids": [1, 2, 3]}
        """
        client_ids = request.data.get("client_ids", [])

        if not client_ids:
            return Response(
                {"error": "Nenhum cliente selecionado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            deleted_count = Client.objects.filter(id__in=client_ids).count()
            Client.objects.filter(id__in=client_ids).delete()

            return Response(
                {
                    "message": f"{deleted_count} cliente(s) excluído(s) com sucesso",
                    "deleted_count": deleted_count,
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Erro ao excluir clientes: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de usuários
    Apenas Administradores podem acessar
    """

    queryset = User.objects.all().prefetch_related("groups")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, GroupPermission]
    required_groups = ["Administradores"]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "email", "date_joined"]
    ordering = ["username"]


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de grupos
    Apenas Administradores podem acessar
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, GroupPermission]
    required_groups = ["Administradores"]


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para dados do dashboard
    """

    permission_classes = [IsAuthenticated, GroupPermission]
    required_groups = ["Administradores", "Gerentes", "Funcionários"]

    @action(detail=False, methods=["get"])
    def overview(self, request):
        """
        Visão geral do dashboard
        GET /api/dashboard/overview/
        """
        # Estatísticas de clientes
        client_stats = Client.get_age_statistics()
        age_groups = {}
        for client in Client.objects.all():
            group = client.get_age_group()
            age_groups[group] = age_groups.get(group, 0) + 1
        client_stats["age_groups"] = age_groups

        # Estatísticas de pedidos
        revenue_stats = Pedido.get_revenue_statistics()
        status_stats = Pedido.get_status_statistics()
        priority_stats = dict(
            Pedido.objects.values("prioridade")
            .annotate(count=Count("id"))
            .values_list("prioridade", "count")
        )
        overdue_count = Pedido.objects.filter(
            data_entrega_prevista__lt=timezone.now().date(),
            status__in=["pendente", "processando", "enviado"],
        ).count()

        pedido_stats = {
            "total_orders": revenue_stats["total_orders"],
            "total_revenue": revenue_stats["total_revenue"],
            "average_order_value": revenue_stats["average_order_value"],
            "monthly_orders": revenue_stats["monthly_orders"],
            "monthly_revenue": revenue_stats["monthly_revenue"],
            "status_distribution": status_stats,
            "priority_distribution": priority_stats,
            "overdue_orders": overdue_count,
        }

        # Pedidos recentes (últimos 10)
        recent_orders = Pedido.objects.select_related("cliente").order_by(
            "-data_pedido"
        )[:10]

        # Top 5 clientes por valor total de pedidos
        top_clients = (
            Client.objects.annotate(total_spent=Sum("pedidos__valor_total"))
            .filter(total_spent__gt=0)
            .order_by("-total_spent")[:5]
        )

        dashboard_data = {
            "client_stats": client_stats,
            "pedido_stats": pedido_stats,
            "recent_orders": recent_orders,
            "top_clients": top_clients,
        }

        serializer = DashboardStatsSerializer(dashboard_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def quick_stats(self, request):
        """
        Estatísticas rápidas para widgets do dashboard
        GET /api/dashboard/quick_stats/
        """
        today = timezone.now().date()
        current_month = timezone.now().replace(day=1).date()

        # Estatísticas rápidas
        stats = {
            "total_clients": Client.objects.count(),
            "total_orders": Pedido.objects.count(),
            "orders_today": Pedido.objects.filter(data_pedido__date=today).count(),
            "orders_this_month": Pedido.objects.filter(
                data_pedido__date__gte=current_month
            ).count(),
            "overdue_orders": Pedido.objects.filter(
                data_entrega_prevista__lt=today,
                status__in=["pendente", "processando", "enviado"],
            ).count(),
            "pending_orders": Pedido.objects.filter(status="pendente").count(),
            "total_revenue": Pedido.objects.filter(status="entregue").aggregate(
                total=Sum("valor_total")
            )["total"]
            or 0,
            "monthly_revenue": Pedido.objects.filter(
                data_pedido__date__gte=current_month, status="entregue"
            ).aggregate(total=Sum("valor_total"))["total"]
            or 0,
        }

        return Response(stats)

    @action(detail=False, methods=["get"])
    def charts_data(self, request):
        """
        Dados para gráficos do dashboard
        GET /api/dashboard/charts_data/
        """
        from datetime import datetime, timedelta
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncDate, TruncMonth

        # Gráfico de pedidos dos últimos 30 dias
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        daily_orders = (
            Pedido.objects.filter(data_pedido__date__gte=thirty_days_ago)
            .extra({"date": "date(data_pedido)"})
            .values("date")
            .annotate(count=Count("id"), revenue=Sum("valor_total"))
            .order_by("date")
        )

        # Gráfico de receita mensal dos últimos 12 meses
        twelve_months_ago = timezone.now().replace(day=1).date() - timedelta(days=365)
        monthly_revenue = (
            Pedido.objects.filter(
                data_pedido__date__gte=twelve_months_ago, status="entregue"
            )
            .extra({"month": "DATE_FORMAT(data_pedido, '%%Y-%%m')"})
            .values("month")
            .annotate(revenue=Sum("valor_total"), orders=Count("id"))
            .order_by("month")
        )

        # Distribuição por status
        status_distribution = dict(
            Pedido.objects.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )

        # Distribuição por prioridade
        priority_distribution = dict(
            Pedido.objects.values("prioridade")
            .annotate(count=Count("id"))
            .values_list("prioridade", "count")
        )

        # Top 10 clientes por valor
        top_clients_data = (
            Client.objects.annotate(
                total_spent=Sum("pedidos__valor_total"), total_orders=Count("pedidos")
            )
            .filter(total_spent__gt=0)
            .order_by("-total_spent")[:10]
            .values("id", "name", "total_spent", "total_orders")
        )

        charts_data = {
            "daily_orders": list(daily_orders),
            "monthly_revenue": list(monthly_revenue),
            "status_distribution": status_distribution,
            "priority_distribution": priority_distribution,
            "top_clients": list(top_clients_data),
        }

        return Response(charts_data)
