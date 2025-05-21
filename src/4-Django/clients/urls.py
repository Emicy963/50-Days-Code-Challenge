from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_clients, name='clients'),
    path('create_client/', views.create_client, name='create_client'),
    path('update_client/<id>', views.update_client, name='update_client'),
    path('delete_client/<id>', views.delete_client, name='delete_client'),
    path('detail_client/<id>', views.detail_client, name='detail_client')
]
