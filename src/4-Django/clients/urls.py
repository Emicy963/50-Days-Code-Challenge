from django.urls import path
from . import views
from order.views import client_pedidos, create_pedido_for_client

urlpatterns = [
    path("", views.get_clients, name="clients"),
    path("create_client/", views.create_client, name="create_client"),
    path("update_client/<int:id>/", views.update_client, name="update_client"),
    path("delete_client/<int:id>/", views.delete_client, name="delete_client"),
    path("detail_client/<int:id>/", views.detail_client, name="detail_client"),
    path("bulk-delete/", views.bulk_delete_clients, name="bulk_delete_clients"),
    # URLs de Integração Cliente-Pedidos
    path("clientes/<int:client_id>/pedidos/", client_pedidos, name="client_pedidos"),
    path("clientes/<int:client_id>/pedidos/criar/", create_pedido_for_client, name="create_pedido_for_client"),
    # URLs para relatórios PDF
    path("cliente/<int:client_id>/pdf/", views.client_pdf_report, name="client_pdf_report"),
    path("dashboard/pdf/", views.dashboard_pdf_report, name="dashboard_pdf_report"),
    # URLs para exportação de dados em CSV
    path("clients/export-csv/", views.export_clients_csv, name="export_clients_csv"),

    path("dashboard/export-csv/", views.export_dashboard_csv, name="export_dashboard_csv"),
    # URLs AJAX
    path("ajax/buscar-cep/", views.get_address_by_cep, name="buscar_cep"),
    path("ajax/clientes/<int:client_id>/pedidos/", views.ajax_get_client_pedidos,name="ajax_get_client_pedidos"),
]
