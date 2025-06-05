from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

# Roteador para a API REST

router = DefaultRouter()
# Registrando as views da API
router.register(r'clients', api_views.ClientViewSet)
router.register(r'pedidos', api_views.PedidoViewSet)
router.register(r'groups', api_views.GroupViewSet)
router.register(r'users', api_views.UserViewSet)
router.register(r'permissions', api_views.DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', views.get_clients, name='clients'),
    path('create_client/', views.create_client, name='create_client'),
    path('update_client/<int:id>/', views.update_client, name='update_client'),
    path('delete_client/<int:id>/', views.delete_client, name='delete_client'),
    path('detail_client/<int:id>/', views.detail_client, name='detail_client'),
    path('bulk-delete/', views.bulk_delete_clients, name='bulk_delete_clients'),

    # ==================== URLS PARA PEDIDOS ====================
    path('pedidos/', views.get_pedidos, name='pedidos'),
    path('pedidos/criar/', views.create_pedido, name='create_pedido'),
    path('pedidos/<int:id>/', views.detail_pedido, name='detail_pedido'),
    path('pedidos/<int:id>/editar/', views.update_pedido, name='update_pedido'),
    path('pedidos/<int:id>/excluir/', views.delete_pedido, name='delete_pedido'),
    path('pedidos/<int:id>/status/', views.update_pedido_status, name='update_pedido_status'),
    path('pedidos/<int:id>/cancelar/', views.cancel_pedido, name='cancel_pedido'),
    path('pedidos/acoes-lote/', views.bulk_actions_pedidos, name='bulk_actions_pedidos'),
    path('pedidos/dashboard/', views.dashboard_pedidos, name='dashboard_pedidos'), 

    # URLs de Integração Cliente-Pedidos
    path('clientes/<int:client_id>/pedidos/', views.client_pedidos, name='client_pedidos'),
    path('clientes/<int:client_id>/pedidos/criar/', views.create_pedido_for_client, name='create_pedido_for_client'),

    # URLs para relatórios PDF
    path('cliente/<int:client_id>/pdf/', views.client_pdf_report, name='client_pdf_report'),
    path('pedidos/pdf/', views.pedidos_pdf_report, name='pedidos_pdf_report'),
    path('dashboard/pdf/', views.dashboard_pdf_report, name='dashboard_pdf_report'),

    # URLs para exportação de dados em CSV
    path('clients/export-csv/', views.export_clients_csv, name='export_clients_csv'),
    path('pedidos/export-csv/', views.export_pedidos_csv, name='export_pedidos_csv'),
    path('dashboard/export-csv/', views.export_dashboard_csv, name='export_dashboard_csv'),

    # URLs AJAX
    path('ajax/buscar-cep/', views.get_address_by_cep, name='buscar_cep'),
    path('ajax/pedidos/<int:id>/status/', views.ajax_update_pedido_status, name='ajax_update_pedido_status'),
    path('ajax/clientes/<int:client_id>/pedidos/', views.ajax_get_client_pedidos, name='ajax_get_client_pedidos'),

    # URLs da API REST
    path('api/', include(router.urls)),
]
