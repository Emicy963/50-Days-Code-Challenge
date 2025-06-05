# myapp/permissions.py
from rest_framework import permissions
from django.contrib.auth.models import Group

class GroupPermission(permissions.BasePermission):
    """
    Permissão baseada em grupos do Django
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Se não especificar grupos obrigatórios, permite acesso
        required_groups = getattr(view, 'required_groups', None)
        if not required_groups:
            return True
        
        # Verificar se o usuário pertence a algum dos grupos obrigatórios
        user_groups = request.user.groups.values_list('name', flat=True)
        return any(group in user_groups for group in required_groups)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissão para apenas o dono do objeto poder editá-lo
    """
    
    def has_object_permission(self, request, view, obj):
        # Leitura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escrita apenas para o dono
        return obj.owner == request.user
