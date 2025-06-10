# myapp/permissions.py
from rest_framework import permissions
from django.http import HttpResponseForbidden


class GroupPermission(permissions.BasePermission):
    """
    Permissão baseada em grupos do Django
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Se não especificar grupos obrigatórios, permite acesso
        required_groups = getattr(view, "required_groups", None)
        if not required_groups:
            return True

        # Verificar se o usuário pertence a algum dos grupos obrigatórios
        user_groups = request.user.groups.values_list("name", flat=True)
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


# Decorator personalizado para verificar grupos
def group_required(*group_names):
    """
    Decorator para verificar se o usuário pertence a um dos grupos especificados
    """

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.is_superuser:
                    return view_func(request, *args, **kwargs)

                user_groups = request.user.groups.values_list("name", flat=True)
                if any(group in user_groups for group in group_names):
                    return view_func(request, *args, **kwargs)

            return HttpResponseForbidden(
                "Você não tem permissão para acessar esta página."
            )

        return _wrapped_view

    return decorator
