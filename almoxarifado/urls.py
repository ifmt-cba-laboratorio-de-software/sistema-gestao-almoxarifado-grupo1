from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    # Views de Templates
    index,
    itens_list,
    item_create,
    item_detail,
    item_update,
    item_delete,
    movimentacao_estoque,
    movimentacao_list,
    inventario_periodico,
    relatorio,
    requisicoes_list,
    requisicao_nova,
    gestao_dashboard,
    relatorios,
    user_login,
    # ViewSets da API
    ItemViewSet,
    MovimentacaoViewSet,
    FornecedorViewSet,
    CategoriaViewSet,
    RetiradaTemporariaViewSet
)

# Configuração do Router para API REST
router = DefaultRouter()
router.register(r'itens-api', ItemViewSet, basename='api-item')
router.register(r'movimentacoes-api', MovimentacaoViewSet, basename='api-movimentacao')
router.register(r'fornecedores-api', FornecedorViewSet, basename='api-fornecedor')
router.register(r'categorias-api', CategoriaViewSet, basename='api-categoria')
router.register(r'retiradas-api', RetiradaTemporariaViewSet, basename='api-retirada')

urlpatterns = [
    # ==================== PÁGINA INICIAL ====================
    path('', itens_list, name='home'),  # Mudei para itens_list como página inicial
    path('index/', index, name='index'),
    
    # ==================== ITENS ====================
    path('itens/', itens_list, name='itens_list'),
    path('itens/', itens_list, name='item_list'),  # ALIAS
    path('itens/cadastro/', item_create, name='item_create'),
    path('itens/<int:pk>/', item_detail, name='item_detail'),
    path('itens/<int:pk>/editar/', item_update, name='item_update'),
    path('itens/<int:pk>/deletar/', item_delete, name='item_delete'),
    
    # ==================== FORNECEDORES ====================
    path('fornecedor/', itens_list, name='fornecedor_list'),  # Placeholder
    
    # ==================== MOVIMENTAÇÕES ====================
    path('movimentacao/', movimentacao_estoque, name='movimentacao_estoque'),
    path('movimentacao/novo/', movimentacao_estoque, name='movimentacao_create'),
    path('movimentacoes/', movimentacao_list, name='movimentacao_list'),
    
    # ==================== INVENTÁRIO ====================
    path('inventario/', inventario_periodico, name='inventario_periodico'),
    
    # ==================== REQUISIÇÕES ====================
    path('requisicoes/', requisicoes_list, name='requisicoes_list'),
    path('solicitar/', requisicao_nova, name='requisicao_nova'),
    
    # ==================== GESTÃO E RELATÓRIOS ====================
    path('gestao/', gestao_dashboard, name='gestao_dashboard'),
    path('relatorios/', relatorios, name='relatorios'),
    path('relatorio/', relatorio, name='relatorio'),
    
    # ==================== LOGIN / LOGOUT ====================
    path('login/', user_login, name='login'),
    path('logout/', user_login, name='logout'),  # Placeholder
    
    # ==================== ROTAS DA API REST ====================
    path('api/', include(router.urls)),
]