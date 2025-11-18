# estoque/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Rotas de Item
    path('', views.index, name='index'),
    path('item/novo/', views.item_create, name='item_create'),
    path('item/<int:pk>/editar/', views.item_edit, name='item_edit'),
    path('item/<int:pk>/excluir/', views.item_delete, name='item_delete'),
    path('item/<int:pk>/', views.item_detail, name='item_detail'),
    path('buscar/item/', views.buscar_item, name='buscar_item'), # <-- NOVA ROTA

    # Rota de Movimentação
    path('movimentacao/novo/', views.movimentacao_create, name='movimentacao_create'),
    
    # Rotas de Fornecedor
    path('fornecedores/', views.fornecedor_list, name='fornecedor_list'),
    path('fornecedor/novo/', views.fornecedor_create, name='fornecedor_create'),
    path('fornecedor/<int:pk>/editar/', views.fornecedor_edit, name='fornecedor_edit'),
    path('fornecedor/<int:pk>/excluir/', views.fornecedor_delete, name='fornecedor_delete'),
    path('buscar/fornecedor/', views.buscar_fornecedor, name='buscar_fornecedor'), #
    path('inventario/periodico/', views.relatorio_inventario_periodico, name='relatorio_inventario_periodico'),
]