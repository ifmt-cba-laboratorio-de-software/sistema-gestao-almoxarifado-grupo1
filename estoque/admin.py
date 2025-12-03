from django.contrib import admin

from .models import Fornecedor, Item, Movimentacao, Solicitacao


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'contato')
    search_fields = ('nome', 'cnpj')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'descricao',
        'categoria',
        'quantidade_atual',
        'estoque_minimo',
        'estoque_maximo',
    )
    search_fields = ('codigo', 'descricao', 'categoria')
    list_filter = ('categoria',)


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('item', 'tipo', 'quantidade', 'data', 'usuario')
    list_filter = ('tipo', 'data')
    date_hierarchy = 'data'


@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'quantidade', 'tipo', 'status', 'solicitante', 'data_solicitacao')
    list_filter = ('status', 'tipo')
    search_fields = ('item__descricao', 'solicitante__username', 'solicitante__first_name', 'solicitante__last_name')
    date_hierarchy = 'data_solicitacao'
