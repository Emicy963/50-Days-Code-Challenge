from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from clients.api_views import ClientViewSet, GroupViewSet, UserViewSet, DashboardViewSet
from order.api_views import PedidoViewSet

# Roteador para a API REST
router = DefaultRouter()

# Registrando as views da API
router.register(r"clients", ClientViewSet)
router.register(r"pedidos", PedidoViewSet)
router.register(r"groups", GroupViewSet)
router.register(r"users", UserViewSet)
router.register(r"dashboard", DashboardViewSet, basename="dashboard")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("clients/", include("clients.urls")),
    path("order/", include("order.urls")),
    # URLs de autenticação JWT
    path("api/auth/", include("accounts.urls")),
    # URLs da API REST
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
