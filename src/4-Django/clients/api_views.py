from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
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
    PedidoBulkActionSerializer,
    PedidoCreateUpdateSerializer,
    PedidoDetailSerializer,
    PedidoStatusUpdateSerializer,
    PedidoStatsSerializer,
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


class PedidoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de pedidos

    Operações disponíveis:
    - list: Listar pedidos com busca e filtros
    - create: Criar novo pedido (Admin/Gerente)
    - retrieve: Obter detalhes de um pedido
    - update: Atualizar pedido (Admin/Gerente)
    - partial_update: Atualização parcial (Admin/Gerente)
    - destroy: Excluir pedido (Admin apenas)
    - update_status: Atualizar apenas status
    - cancel: Cancelar pedido (Admin/Gerente)
    - bulk_actions: Ações em lote (Admin apenas)
    - stats: Estatísticas de pedidos
    - overdue: Pedidos atrasados
    """

    queryset = Pedido.objects.select_related("cliente").all()
    permission_classes = [IsAuthenticated, GroupPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "prioridade", "cliente"]
    search_fields = ["numero_pedido", "cliente__name", "descricao"]
    ordering_fields = ["data_pedido", "valor_total", "data_entrega_prevista"]
    ordering = ["-data_pedido"]

    def get_serializer_class(self):
        if self.action == "list":
            return PedidoListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return PedidoCreateUpdateSerializer
        elif self.action == "update_status":
            return PedidoStatusUpdateSerializer
        elif self.action == "bulk_actions":
            return PedidoBulkActionSerializer
        return PedidoDetailSerializer

    def get_permissions(self):
        """
        Permissões baseadas na ação:
        - list, retrieve: todos os grupos
        - create, update, partial_update, cancel: Admin/Gerente
        - destroy, bulk_actions: Admin apenas
        - update_status: todos os grupos
        """
        permission_classes = [IsAuthenticated]

        if self.action in ["create", "update", "partial_update", "cancel"]:
            permission_classes.append(GroupPermission)
            self.required_groups = ["Administradores", "Gerentes"]
        elif self.action in ["destroy", "bulk_actions"]:
            permission_classes.append(GroupPermission)
            self.required_groups = ["Administradores"]
        else:
            permission_classes.append(GroupPermission)
            self.required_groups = ["Administradores", "Gerentes", "Funcionários"]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = Pedido.objects.select_related("cliente").all()

        # Filtros adicionais via query params
        data_inicio = self.request.query_params.get("data_inicio")
        data_fim = self.request.query_params.get("data_fim")
        valor_min = self.request.query_params.get("valor_min")
        valor_max = self.request.query_params.get("valor_max")

        if data_inicio:
            queryset = queryset.filter(data_pedido__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_pedido__date__lte=data_fim)
        if valor_min:
            queryset = queryset.filter(valor_total__gte=valor_min)
        if valor_max:
            queryset = queryset.filter(valor_total__lte=valor_max)

        return queryset

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        """
        Atualizar apenas o status do pedido
        PATCH /api/pedidos/{id}/update_status/
        Body: {"status": "enviado", "observacao": "Enviado via correios"}
        """
        pedido = self.get_object()
        serializer = PedidoStatusUpdateSerializer(
            pedido, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": f"Status do pedido {pedido.numero_pedido} atualizado com sucesso",
                    "pedido": PedidoDetailSerializer(pedido).data,
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancelar pedido
        POST /api/pedidos/{id}/cancel/
        Body: {"motivo": "Cliente desistiu"}
        """
        pedido = self.get_object()

        if not pedido.can_be_cancelled():
            return Response(
                {"error": "Este pedido não pode ser cancelado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        motivo = request.data.get("motivo", "")

        try:
            pedido.cancel_order(motivo)
            return Response(
                {
                    "message": f"Pedido {pedido.numero_pedido} cancelado com sucesso",
                    "pedido": PedidoDetailSerializer(pedido).data,
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Erro ao cancelar pedido: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def bulk_actions(self, request):
        """
        Ações em lote para pedidos
        POST /api/pedidos/bulk_actions/
        Body: {
            "pedido_ids": [1, 2, 3],
            "action": "update_status",
            "new_status": "enviado"
        }
        """
        serializer = PedidoBulkActionSerializer(data=request.data)

        if serializer.is_valid():
            pedido_ids = serializer.validated_data["pedido_ids"]
            action = serializer.validated_data["action"]

            try:
                pedidos = Pedido.objects.filter(id__in=pedido_ids)
                count = pedidos.count()

                if action == "update_status":
                    new_status = serializer.validated_data["new_status"]
                    pedidos.update(status=new_status)
                    message = f"{count} pedido(s) tiveram o status atualizado"

                elif action == "update_priority":
                    new_priority = serializer.validated_data["new_priority"]
                    pedidos.update(prioridade=new_priority)
                    message = f"{count} pedido(s) tiveram a prioridade atualizada"

                elif action == "delete":
                    pedidos.delete()
                    message = f"{count} pedido(s) excluído(s) com sucesso"

                return Response({"message": message, "affected_count": count})

            except Exception as e:
                return Response(
                    {"error": f"Erro ao executar ação em lote: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Estatísticas gerais de pedidos
        GET /api/pedidos/stats/
        """
        # Estatísticas de receita
        revenue_stats = Pedido.get_revenue_statistics()

        # Estatísticas por status
        status_stats = Pedido.get_status_statistics()

        # Estatísticas por prioridade
        priority_stats = dict(
            Pedido.objects.values("prioridade")
            .annotate(count=Count("id"))
            .values_list("prioridade", "count")
        )

        # Pedidos atrasados
        overdue_count = Pedido.objects.filter(
            data_entrega_prevista__lt=timezone.now().date(),
            status__in=["pendente", "processando", "enviado"],
        ).count()

        stats_data = {
            "total_orders": revenue_stats["total_orders"],
            "total_revenue": revenue_stats["total_revenue"],
            "average_order_value": revenue_stats["average_order_value"],
            "monthly_orders": revenue_stats["monthly_orders"],
            "monthly_revenue": revenue_stats["monthly_revenue"],
            "status_distribution": status_stats,
            "priority_distribution": priority_stats,
            "overdue_orders": overdue_count,
        }

        serializer = PedidoStatsSerializer(stats_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """
        Listar pedidos atrasados
        GET /api/pedidos/overdue/
        """
        overdue_pedidos = (
            Pedido.objects.filter(
                data_entrega_prevista__lt=timezone.now().date(),
                status__in=["pendente", "processando", "enviado"],
            )
            .select_related("cliente")
            .order_by("data_entrega_prevista")
        )

        page = self.paginate_queryset(overdue_pedidos)
        if page is not None:
            serializer = PedidoListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PedidoListSerializer(overdue_pedidos, many=True)
        return Response(serializer.data)


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
