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
