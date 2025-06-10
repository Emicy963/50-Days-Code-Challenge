from django.urls import path
from . import views

urlpatterns = [
    path("pedidos/", views.get_pedidos, name="pedidos"),
    path("pedidos/criar/", views.create_pedido, name="create_pedido"),
    path("pedidos/<int:id>/", views.detail_pedido, name="detail_pedido"),
    path("pedidos/<int:id>/editar/", views.update_pedido, name="update_pedido"),
    path("pedidos/<int:id>/excluir/", views.delete_pedido, name="delete_pedido"),
    path("pedidos/<int:id>/status/", views.update_pedido_status, name="update_pedido_status"),
    path("pedidos/<int:id>/cancelar/", views.cancel_pedido, name="cancel_pedido"),
    path("pedidos/acoes-lote/", views.bulk_actions_pedidos, name="bulk_actions_pedidos"),
    path("pedidos/dashboard/", views.dashboard_pedidos, name="dashboard_pedidos"),
    path("pedidos/pdf/", views.pedidos_pdf_report, name="pedidos_pdf_report"),
    path("pedidos/export-csv/", views.export_pedidos_csv, name="export_pedidos_csv"),
    path("ajax/pedidos/<int:id>/status/", views.ajax_update_pedido_status, name="ajax_update_pedido_status"),
]

