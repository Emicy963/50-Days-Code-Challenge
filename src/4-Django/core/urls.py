from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls import static
from rest_framework.routers import DefaultRouter
from clients import api_views

# Roteador para a API REST

router = DefaultRouter()
# Registrando as views da API
router.register(r'clients', api_views.ClientViewSet)
router.register(r'pedidos', api_views.PedidoViewSet)
router.register(r'groups', api_views.GroupViewSet)
router.register(r'users', api_views.UserViewSet)
router.register(r'permissions', api_views.DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clients/', include('clients.urls')),
    path('auth/', include('accounts.urls')),

    # URLs da API REST
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    