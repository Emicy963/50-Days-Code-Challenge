from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Client, Pedido
from decimal import Decimal

class GroupSerializer(serializers.ModelSerializer):
    """Serializer para grupos de usuários."""
    class Meta:
        model = Group
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    """Serializer para usuários."""
    groups = GroupSerializer(many=True, read_only=True)
    groups_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name','last_name', 'is_active', 'date_joined', 'groups', 'group_names']
        read_only_fields = ['date_joined']

    def get_group_names(self, obj):
        """Retorna os nomes dos grupos do usuário."""
        return [group.name for group in obj.groups.all()]
    
class ClientListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de clientes"""
    age_group = serializers.ReadOnlyField(source='get_age_group')
    display_name = serializers.ReadOnlyField()
    total_pedidos = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'age', 'age_group', 'display_name',
                 'total_pedidos', 'created_at', 'updated_at']
    
    def get_total_pedidos(self, obj):
        return obj.pedidos.count()

class ClientDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do cliente"""
    age_group = serializers.ReadOnlyField(source='get_age_group')
    display_name = serializers.ReadOnlyField()
    total_pedidos = serializers.SerializerMethodField()
    pedidos_stats = serializers.SerializerMethodField()
    pedidos_por_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'age', 'age_group', 'display_name',
                 'total_pedidos', 'pedidos_stats', 'pedidos_por_status',
                 'created_at', 'updated_at']
    
    def get_total_pedidos(self, obj):
        return obj.pedidos.count()
    
    def get_pedidos_stats(self, obj):
        from django.db.models import Count, Sum, Avg
        stats = obj.pedidos.aggregate(
            total_pedidos=Count('id'),
            valor_total=Sum('valor_total'),
            valor_medio=Avg('valor_total')
        )
        return {
            'total_pedidos': stats['total_pedidos'] or 0,
            'valor_total': str(stats['valor_total'] or Decimal('0.00')),
            'valor_medio': str(round(stats['valor_medio'], 2) if stats['valor_medio'] else Decimal('0.00'))
        }
    
    def get_pedidos_por_status(self, obj):
        from django.db.models import Count
        return dict(
            obj.pedidos.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )

class ClientCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de clientes"""
    
    class Meta:
        model = Client
        fields = ['name', 'email', 'age']
    
    def validate_age(self, value):
        if value < 18:
            raise serializers.ValidationError("Não aceitamos clientes menores de 18 anos.")
        return value
    
    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Nome deve ter pelo menos 2 caracteres.")
        return value.strip()

class PedidoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de pedidos"""
    cliente_nome = serializers.ReadOnlyField(source='cliente.name')
    cliente_email = serializers.ReadOnlyField(source='cliente.email')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    prioridade_display = serializers.ReadOnlyField(source='get_prioridade_display')
    status_display_class = serializers.ReadOnlyField()
    prioridade_display_class = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    days_until_delivery = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    
    class Meta:
        model = Pedido
        fields = ['id', 'numero_pedido', 'cliente', 'cliente_nome', 'cliente_email',
                 'descricao', 'valor_total', 'status', 'status_display', 
                 'status_display_class', 'prioridade', 'prioridade_display',
                 'prioridade_display_class', 'data_pedido', 'data_entrega_prevista',
                 'is_overdue', 'days_until_delivery', 'can_be_cancelled',
                 'created_at', 'updated_at']
        
class PedidoDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes do pedido"""
    cliente = ClientListSerializer(read_only=True)
    status_display = serializers.ReadOnlyField(source='get_status_display')
    prioridade_display = serializers.ReadOnlyField(source='get_prioridade_display')
    status_display_class = serializers.ReadOnlyField()
    prioridade_display_class = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    days_until_delivery = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    
    class Meta:
        model = Pedido
        fields = ['id', 'numero_pedido', 'cliente', 'descricao', 'valor_total',
                 'status', 'status_display', 'status_display_class',
                 'prioridade', 'prioridade_display', 'prioridade_display_class',
                 'data_pedido', 'data_entrega_prevista', 'data_entrega_realizada',
                 'observacoes', 'is_overdue', 'days_until_delivery',
                 'can_be_cancelled', 'created_at', 'updated_at']
        
class PedidoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de pedidos"""
    
    class Meta:
        model = Pedido
        fields = ['cliente', 'descricao', 'valor_total', 'status', 'prioridade',
                 'data_entrega_prevista', 'observacoes']
    
    def validate_valor_total(self, value):
        if value < 0:
            raise serializers.ValidationError("O valor total não pode ser negativo.")
        return value
    
    def validate_descricao(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Descrição deve ter pelo menos 10 caracteres.")
        return value.strip()
    
    def validate_data_entrega_prevista(self, value):
        if value:
            from django.utils import timezone
            if value < timezone.now().date():
                raise serializers.ValidationError("A data de entrega prevista não pode ser no passado.")
        return value
    
    def validate(self, attrs):
        # Validação para pedidos entregues
        if attrs.get('status') == 'entregue' and not attrs.get('data_entrega_realizada'):
            from django.utils import timezone
            attrs['data_entrega_realizada'] = timezone.now()
        return attrs