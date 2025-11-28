from rest_framework import serializers
from .models import Item, Movimentacao, Fornecedor, Categoria, RetiradaTemporaria
from django.contrib.auth.models import User


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = '__all__'


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class ItemSerializer(serializers.ModelSerializer):
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    esta_abaixo_minimo = serializers.BooleanField(read_only=True)
    valor_total_estoque = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['quantidade_atual', 'criado_em', 'atualizado_em']


class MovimentacaoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.username', read_only=True)
    item_descricao = serializers.CharField(source='item.descricao', read_only=True)
    item_codigo = serializers.CharField(source='item.codigo', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    valor_total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Movimentacao
        fields = '__all__'
        read_only_fields = ['usuario', 'estoque_anterior', 'estoque_posterior', 'data_movimentacao']


class MovimentacaoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimentacao
        fields = ['item', 'tipo', 'quantidade', 'observacao', 'numero_documento', 'valor_unitario']
    
    def validate(self, data):
        item = data.get('item')
        tipo = data.get('tipo')
        quantidade = data.get('quantidade')
        
        if tipo == 'S' and item.quantidade_atual < quantidade:
            raise serializers.ValidationError(
                f"Estoque insuficiente. Disponível: {item.quantidade_atual} {item.unidade_medida}"
            )
        
        return data


class RetiradaTemporariaSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario_retirada.username', read_only=True)
    item_descricao = serializers.CharField(source='item.descricao', read_only=True)
    quantidade_pendente = serializers.IntegerField(read_only=True)
    esta_atrasada = serializers.BooleanField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = RetiradaTemporaria
        fields = '__all__'
        read_only_fields = ['usuario_retirada', 'data_retirada', 'quantidade_devolvida']


class DevolucaoSerializer(serializers.Serializer):
    quantidade = serializers.IntegerField(min_value=1)
    observacao = serializers.CharField(required=False, allow_blank=True)
    
    def validate_quantidade(self, value):
        retirada = self.context['retirada']
        if value > retirada.quantidade_pendente:
            raise serializers.ValidationError(
                f"Quantidade inválida. Pendente: {retirada.quantidade_pendente}"
            )
        return value