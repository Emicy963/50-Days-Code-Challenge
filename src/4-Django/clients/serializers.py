from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Client
from order.serializers import PedidoListSerializer, PedidoStatsSerializer
from decimal import Decimal


class GroupSerializer(serializers.ModelSerializer):
    """Serializer para grupos de usuários."""

    class Meta:
        model = Group
        fields = ["id", "name"]


class UserSerializer(serializers.ModelSerializer):
    """Serializer para usuários."""

    groups = GroupSerializer(many=True, read_only=True)
    groups_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "groups",
            "group_names",
        ]
        read_only_fields = ["date_joined"]

    def get_group_names(self, obj):
        """Retorna os nomes dos grupos do usuário."""
        return [group.name for group in obj.groups.all()]


class ClientListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de clientes"""

    age_group = serializers.ReadOnlyField(source="get_age_group")
    display_name = serializers.ReadOnlyField()
    total_pedidos = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "email",
            "age",
            "age_group",
            "display_name",
            "total_pedidos",
            "created_at",
            "updated_at",
        ]

    def get_total_pedidos(self, obj):
        return obj.pedidos.count()


class ClientDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do cliente"""

    age_group = serializers.ReadOnlyField(source="get_age_group")
    display_name = serializers.ReadOnlyField()
    total_pedidos = serializers.SerializerMethodField()
    pedidos_stats = serializers.SerializerMethodField()
    pedidos_por_status = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "email",
            "age",
            "age_group",
            "display_name",
            "total_pedidos",
            "pedidos_stats",
            "pedidos_por_status",
            "created_at",
            "updated_at",
        ]

    def get_total_pedidos(self, obj):
        return obj.pedidos.count()

    def get_pedidos_stats(self, obj):
        from django.db.models import Count, Sum, Avg

        stats = obj.pedidos.aggregate(
            total_pedidos=Count("id"),
            valor_total=Sum("valor_total"),
            valor_medio=Avg("valor_total"),
        )
        return {
            "total_pedidos": stats["total_pedidos"] or 0,
            "valor_total": str(stats["valor_total"] or Decimal("0.00")),
            "valor_medio": str(
                round(stats["valor_medio"], 2)
                if stats["valor_medio"]
                else Decimal("0.00")
            ),
        }

    def get_pedidos_por_status(self, obj):
        from django.db.models import Count

        return dict(
            obj.pedidos.values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )


class ClientCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de clientes"""

    class Meta:
        model = Client
        fields = ["name", "email", "age"]

    def validate_age(self, value):
        if value < 18:
            raise serializers.ValidationError(
                "Não aceitamos clientes menores de 18 anos."
            )
        return value

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Nome deve ter pelo menos 2 caracteres.")
        return value.strip()





class ClientStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de clientes"""

    total = serializers.IntegerField()
    average_age = serializers.FloatField()
    youngest = serializers.IntegerField()
    oldest = serializers.IntegerField()
    age_groups = serializers.DictField()


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas do dashboard"""

    client_stats = ClientStatsSerializer()
    pedido_stats = PedidoStatsSerializer()
    recent_orders = PedidoListSerializer(many=True)
    top_clients = ClientListSerializer(many=True)
