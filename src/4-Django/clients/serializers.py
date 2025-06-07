from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User, Group
from .models import Client, Pedido
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


class ClientStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de clientes"""

    total = serializers.IntegerField()
    average_age = serializers.FloatField()
    youngest = serializers.IntegerField()
    oldest = serializers.IntegerField()
    age_groups = serializers.DictField()


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


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas do dashboard"""

    client_stats = ClientStatsSerializer()
    pedido_stats = PedidoStatsSerializer()
    recent_orders = PedidoListSerializer(many=True)
    top_clients = ClientListSerializer(many=True)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para JWT token com informações adicionais do usuário
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Adicionar claims customizados
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        
        # Adicionar grupos do usuário
        token['groups'] = [group.name for group in user.groups.all()]
        
        # Adicionar permissões específicas
        permissions = []
        if user.groups.filter(name='Administradores').exists():
            permissions = ['all']
        elif user.groups.filter(name='Gerentes').exists():
            permissions = ['read', 'write', 'update']
        elif user.groups.filter(name='Funcionários').exists():
            permissions = ['read', 'update_status']
        
        token['permissions'] = permissions
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Adicionar informações do usuário na resposta
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'groups': [group.name for group in self.user.groups.all()],
            'last_login': self.user.last_login,
        }
        
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de novos usuários
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'As senhas não coincidem.'
            })
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email já está em uso.')
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Este nome de usuário já está em uso.')
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Adicionar ao grupo padrão (Funcionários)
        from django.contrib.auth.models import Group
        funcionarios_group, created = Group.objects.get_or_create(name='Funcionários')
        user.groups.add(funcionarios_group)
        
        return user

