from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_clients, name='clients'),
    path('create_client/', views.create_client, name='create_client'),
    path('update_client/<int:id>/', views.update_client, name='update_client'),
    path('delete_client/<int:id>/', views.delete_client, name='delete_client'),
    path('detail_client/<int:id>/', views.detail_client, name='detail_client'),
    path('bulk-delete/', views.bulk_delete_clients, name='bulk_delete_clients'),
]
