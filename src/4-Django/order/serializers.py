from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import Pedido
from clients.serializers import ClientListSerializer


class GroupSerializer(serializers.ModelSerializer):
    """Serializer para grupos de usuários."""

    class Meta:
        model = Group
        fields = ["id", "name"]

class PedidoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de pedidos"""

    cliente_nome = serializers.ReadOnlyField(source="cliente.name")
    cliente_email = serializers.ReadOnlyField(source="cliente.email")
    status_display = serializers.ReadOnlyField(source="get_status_display")
    prioridade_display = serializers.ReadOnlyField(source="get_prioridade_display")
    status_display_class = serializers.ReadOnlyField()
    prioridade_display_class = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    days_until_delivery = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()

    class Meta:
        model = Pedido
        fields = [
            "id",
            "numero_pedido",
            "cliente",
            "cliente_nome",
            "cliente_email",
            "descricao",
            "valor_total",
            "status",
            "status_display",
            "status_display_class",
            "prioridade",
            "prioridade_display",
            "prioridade_display_class",
            "data_pedido",
            "data_entrega_prevista",
            "is_overdue",
            "days_until_delivery",
            "can_be_cancelled",
            "created_at",
            "updated_at",
        ]


class PedidoDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do pedido"""

    cliente = ClientListSerializer(read_only=True)
    status_display = serializers.ReadOnlyField(source="get_status_display")
    prioridade_display = serializers.ReadOnlyField(source="get_prioridade_display")
    status_display_class = serializers.ReadOnlyField()
    prioridade_display_class = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    days_until_delivery = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()

    class Meta:
        model = Pedido
        fields = [
            "id",
            "numero_pedido",
            "cliente",
            "descricao",
            "valor_total",
            "status",
            "status_display",
            "status_display_class",
            "prioridade",
            "prioridade_display",
            "prioridade_display_class",
            "data_pedido",
            "data_entrega_prevista",
            "data_entrega_realizada",
            "observacoes",
            "is_overdue",
            "days_until_delivery",
            "can_be_cancelled",
            "created_at",
            "updated_at",
        ]


class PedidoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de pedidos"""

    class Meta:
        model = Pedido
        fields = [
            "cliente",
            "descricao",
            "valor_total",
            "status",
            "prioridade",
            "data_entrega_prevista",
            "observacoes",
        ]

    def validate_valor_total(self, value):
        if value < 0:
            raise serializers.ValidationError("O valor total não pode ser negativo.")
        return value

    def validate_descricao(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Descrição deve ter pelo menos 10 caracteres."
            )
        return value.strip()

    def validate_data_entrega_prevista(self, value):
        if value:
            from django.utils import timezone

            if value < timezone.now().date():
                raise serializers.ValidationError(
                    "A data de entrega prevista não pode ser no passado."
                )
        return value

    def validate(self, attrs):
        # Validação para pedidos entregues
        if attrs.get("status") == "entregue" and not attrs.get(
            "data_entrega_realizada"
        ):
            from django.utils import timezone

            attrs["data_entrega_realizada"] = timezone.now()
        return attrs


class PedidoStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização apenas do status do pedido"""

    observacao = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Observação sobre a mudança de status",
    )

    class Meta:
        model = Pedido
        fields = ["status", "observacao"]

    def update(self, instance, validated_data):
        observacao = validated_data.pop("observacao", "")

        # Adicionar observação sobre mudança de status
        if observacao:
            from django.utils import timezone

            timestamp = timezone.now().strftime("%d/%m/%Y %H:%M")
            new_observation = f"[{timestamp}] Status alterado para '{instance.get_status_display()}': {observacao}"

            if instance.observacoes:
                instance.observacoes += f"\n\n{new_observation}"
            else:
                instance.observacoes = new_observation

        # Atualizar status
        instance.status = validated_data["status"]
        instance.save()

        return instance


class PedidoBulkActionSerializer(serializers.Serializer):
    """Serializer para ações em lote nos pedidos"""

    ACTION_CHOICES = [
        ("update_status", "Atualizar Status"),
        ("update_priority", "Atualizar Prioridade"),
        ("delete", "Excluir"),
    ]

    pedido_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="IDs dos pedidos para aplicar a ação",
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    new_status = serializers.ChoiceField(
        choices=Pedido.STATUS_CHOICES,
        required=False,
        help_text="Novo status (obrigatório para action='update_status')",
    )
    new_priority = serializers.ChoiceField(
        choices=Pedido.PRIORIDADE_CHOICES,
        required=False,
        help_text="Nova prioridade (obrigatório para action='update_priority')",
    )

    def validate(self, attrs):
        action = attrs.get("action")

        if action == "update_status" and not attrs.get("new_status"):
            raise serializers.ValidationError(
                {
                    "new_status": 'Este campo é obrigatório quando a ação é "update_status".'
                }
            )

        if action == "update_priority" and not attrs.get("new_priority"):
            raise serializers.ValidationError(
                {
                    "new_priority": 'Este campo é obrigatório quando a ação é "update_priority".'
                }
            )

        return attrs
    
class PedidoStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de pedidos"""

    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    monthly_orders = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    status_distribution = serializers.DictField()
    priority_distribution = serializers.DictField()
    overdue_orders = serializers.IntegerField()
