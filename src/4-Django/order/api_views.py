from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from .models import Pedido
from .serializers import (
    PedidoListSerializer,
    PedidoCreateUpdateSerializer,
    PedidoDetailSerializer,
    PedidoStatusUpdateSerializer,
    PedidoBulkActionSerializer,
    PedidoStatsSerializer,
)
from clients.permissions import GroupPermission


class StandardResultsSetPagination(PageNumberPagination):
    """Paginação padrão para a API"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


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
