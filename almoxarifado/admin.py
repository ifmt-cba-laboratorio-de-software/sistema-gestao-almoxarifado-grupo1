from django.contrib import admin
from .models import Item, Movimentacao, Fornecedor, Categoria, RetiradaTemporaria


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'telefone', 'email', 'ativo']
    search_fields = ['nome', 'cnpj']
    list_filter = ['ativo']


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao', 'ativo']
    search_fields = ['nome']
    list_filter = ['ativo']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'descricao', 'categoria', 'quantidade_atual', 
        'estoque_minimo', 'estoque_maximo', 'fornecedor', 'ativo'
    ]
    search_fields = ['codigo', 'descricao']
    list_filter = ['categoria', 'fornecedor', 'ativo']
    readonly_fields = ['quantidade_atual', 'criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('codigo', 'descricao', 'categoria', 'unidade_medida')
        }),
        ('Valores', {
            'fields': ('valor_unitario', 'fornecedor')
        }),
        ('Controle de Estoque', {
            'fields': ('quantidade_atual', 'estoque_minimo', 'estoque_maximo', 'localizacao')
        }),
        ('Status', {
            'fields': ('ativo', 'criado_em', 'atualizado_em')
        }),
    )


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = [
        'data_movimentacao', 'item', 'tipo', 'quantidade', 
        'usuario', 'estoque_anterior', 'estoque_posterior'
    ]
    search_fields = ['item__codigo', 'item__descricao', 'numero_documento']
    list_filter = ['tipo', 'data_movimentacao', 'usuario']
    readonly_fields = ['estoque_anterior', 'estoque_posterior', 'data_movimentacao']
    date_hierarchy = 'data_movimentacao'
    
    fieldsets = (
        ('Movimentação', {
            'fields': ('item', 'tipo', 'quantidade', 'usuario')
        }),
        ('Detalhes', {
            'fields': ('numero_documento', 'valor_unitario', 'observacao')
        }),
        ('Controle', {
            'fields': ('estoque_anterior', 'estoque_posterior', 'data_movimentacao')
        }),
    )


@admin.register(RetiradaTemporaria)
class RetiradaTemporariaAdmin(admin.ModelAdmin):
    list_display = [
        'data_retirada', 'item', 'usuario_retirada', 'quantidade_retirada',
        'quantidade_devolvida', 'quantidade_pendente', 'status', 'esta_atrasada'
    ]
    search_fields = ['item__codigo', 'item__descricao', 'usuario_retirada__username']
    list_filter = ['status', 'data_retirada', 'data_prevista_devolucao']
    readonly_fields = ['data_retirada', 'quantidade_pendente', 'esta_atrasada']
    date_hierarchy = 'data_retirada'
    
    fieldsets = (
        ('Retirada', {
            'fields': ('item', 'usuario_retirada', 'quantidade_retirada', 'setor_destino')
        }),
        ('Datas', {
            'fields': ('data_retirada', 'data_prevista_devolucao', 'data_devolucao')
        }),
        ('Devolução', {
            'fields': ('quantidade_devolvida', 'quantidade_pendente', 'status')
        }),
        ('Observações', {
            'fields': ('observacao',)
        }),
    )