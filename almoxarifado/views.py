from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.utils import timezone
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Item, Movimentacao, Fornecedor, Categoria, RetiradaTemporaria
from .serializers import (
    ItemSerializer, MovimentacaoSerializer, MovimentacaoCreateSerializer,
    FornecedorSerializer, CategoriaSerializer, RetiradaTemporariaSerializer,
    DevolucaoSerializer
)
from .forms import ItemForm, MovimentacaoForm


# ==================== VIEWS DE TEMPLATES HTML ====================

def index(request):
    """Página inicial - usando seu template index.html"""
    return render(request, 'almoxarifado/index.html', {})


def itens_list(request):
    """Lista de itens - usando seu template itens_list.html"""
    itens = Item.objects.filter(ativo=True).select_related('categoria', 'fornecedor')
    
    context = {
        'itens': itens,
    }
    return render(request, 'almoxarifado/itens_list.html', context)


def item_create(request):
    """Cadastro de item - usando seu template cadastro.html"""
    if request.method == 'POST':
        # Processar dados do formulário
        codigo = request.POST.get('codigo')
        descricao = request.POST.get('descricao')
        unidade_medida = request.POST.get('unidade_medida')
        valor_unitario = request.POST.get('valor_unitario')
        fornecedor_id = request.POST.get('fornecedor')
        novo_fornecedor = request.POST.get('novo_fornecedor')
        estoque_minimo = request.POST.get('estoque_minimo', 0)
        estoque_maximo = request.POST.get('estoque_maximo', 0)
        quantidade_inicial = request.POST.get('quantidade_inicial', 0)
        
        # Criar ou usar fornecedor
        if novo_fornecedor:
            fornecedor = Fornecedor.objects.create(
                nome=novo_fornecedor,
                cnpj='00000000000000'  # Placeholder
            )
        else:
            fornecedor = Fornecedor.objects.get(id=fornecedor_id)
        
        # Criar categoria padrão se não existir
        categoria, _ = Categoria.objects.get_or_create(
            nome='Geral',
            defaults={'descricao': 'Categoria geral'}
        )
        
        # Criar item
        Item.objects.create(
            codigo=codigo,
            descricao=descricao,
            categoria=categoria,
            unidade_medida=unidade_medida,
            valor_unitario=valor_unitario,
            fornecedor=fornecedor,
            estoque_minimo=estoque_minimo or 0,
            estoque_maximo=estoque_maximo or 0,
            quantidade_atual=quantidade_inicial or 0
        )
        
        messages.success(request, 'Item cadastrado com sucesso!')
        return redirect('itens_list')
    
    fornecedores = Fornecedor.objects.filter(ativo=True)
    context = {
        'fornecedores': fornecedores,
    }
    return render(request, 'almoxarifado/cadastro.html', context)


def item_detail(request, pk):
    """Detalhes do item"""
    item = get_object_or_404(Item, pk=pk)
    movimentacoes = item.movimentacoes.all()[:20]
    
    context = {
        'item': item,
        'movimentacoes': movimentacoes,
    }
    return render(request, 'almoxarifado/item_detail.html', context)


def item_update(request, pk):
    """Atualizar item"""
    item = get_object_or_404(Item, pk=pk)
    
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item atualizado com sucesso!')
            return redirect('item_detail', pk=pk)
    else:
        form = ItemForm(instance=item)
    
    return render(request, 'almoxarifado/item_form.html', {'form': form, 'title': 'Editar Item'})


def item_delete(request, pk):
    """Deletar item (desativar)"""
    item = get_object_or_404(Item, pk=pk)
    item.ativo = False
    item.save()
    messages.success(request, 'Item removido com sucesso!')
    return redirect('itens_list')


def movimentacao_estoque(request):
    """Movimentação de estoque - usando seu template movimentacao_estoque.html"""
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo')  # 'entrada' ou 'saida'
        item_id = request.POST.get('item')
        quantidade = int(request.POST.get('quantidade'))
        referencia = request.POST.get('referencia')
        data = request.POST.get('data')
        
        item = Item.objects.get(id=item_id)
        
        # Criar usuário padrão se não existir
        from django.contrib.auth.models import User
        usuario, _ = User.objects.get_or_create(
            username='sistema',
            defaults={'password': 'sistema123'}
        )
        
        if tipo == 'entrada':
            Movimentacao.objects.create(
                item=item,
                tipo='E',
                quantidade=quantidade,
                usuario=usuario,
                observacao=f'Entrada - {referencia}'
            )
            messages.success(request, 'Entrada registrada com sucesso!')
        elif tipo == 'saida':
            try:
                Movimentacao.objects.create(
                    item=item,
                    tipo='S',
                    quantidade=quantidade,
                    usuario=usuario,
                    observacao=f'Saída - {referencia}'
                )
                messages.success(request, 'Saída registrada com sucesso!')
            except ValueError as e:
                messages.error(request, str(e))
        
        return redirect('movimentacao_estoque')
    
    itens = Item.objects.filter(ativo=True)
    movimentacoes_recentes = Movimentacao.objects.all()[:10]
    
    context = {
        'itens': itens,
        'movimentacoes': movimentacoes_recentes,
    }
    return render(request, 'almoxarifado/movimentacao_estoque.html', context)


def inventario_periodico(request):
    """Inventário periódico - usando seu template inventario_periodico.html"""
    return render(request, 'almoxarifado/inventario_periodico.html', {})


def movimentacao_list(request):
    """Lista todas as movimentações"""
    tipo = request.GET.get('tipo', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    movimentacoes = Movimentacao.objects.all().select_related('item', 'usuario')
    
    if tipo:
        movimentacoes = movimentacoes.filter(tipo=tipo)
    
    if data_inicio:
        movimentacoes = movimentacoes.filter(data_movimentacao__gte=data_inicio)
    
    if data_fim:
        movimentacoes = movimentacoes.filter(data_movimentacao__lte=data_fim)
    
    context = {
        'movimentacoes': movimentacoes[:100],
    }
    return render(request, 'almoxarifado/movimentacao_list.html', context)


def relatorio(request):
    """Página de relatórios"""
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    total_itens = Item.objects.filter(ativo=True).count()
    itens_abaixo_minimo = Item.objects.filter(
        quantidade_atual__lt=F('estoque_minimo'),
        ativo=True
    )
    
    movimentacoes = Movimentacao.objects.all()
    
    if data_inicio:
        movimentacoes = movimentacoes.filter(data_movimentacao__gte=data_inicio)
    
    if data_fim:
        movimentacoes = movimentacoes.filter(data_movimentacao__lte=data_fim)
    
    total_entradas = movimentacoes.filter(tipo='E').aggregate(
        total=Sum('quantidade')
    )['total'] or 0
    
    total_saidas = movimentacoes.filter(tipo='S').aggregate(
        total=Sum('quantidade')
    )['total'] or 0
    
    context = {
        'total_itens': total_itens,
        'itens_abaixo_minimo': itens_abaixo_minimo,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'almoxarifado/relatorio.html', context)


# Placeholder views necessárias pelos seus templates
def requisicoes_list(request):
    return render(request, 'almoxarifado/requisicoes_list.html', {})

def requisicao_nova(request):
    return render(request, 'almoxarifado/requisicao_nova.html', {})

def gestao_dashboard(request):
    return render(request, 'almoxarifado/gestao_dashboard.html', {})

def relatorios(request):
    return relatorio(request)

def user_login(request):
    return redirect('index')


# ==================== API REST VIEWSETS ====================

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.filter(ativo=True).select_related('fornecedor', 'categoria')
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['categoria', 'fornecedor', 'ativo']
    search_fields = ['codigo', 'descricao', 'categoria__nome']
    
    @action(detail=False, methods=['get'])
    def abaixo_minimo(self, request):
        itens = self.queryset.filter(quantidade_atual__lt=F('estoque_minimo'))
        serializer = self.get_serializer(itens, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historico(self, request, pk=None):
        item = self.get_object()
        movimentacoes = item.movimentacoes.all()[:50]
        serializer = MovimentacaoSerializer(movimentacoes, many=True)
        return Response(serializer.data)


class MovimentacaoViewSet(viewsets.ModelViewSet):
    queryset = Movimentacao.objects.all().select_related('item', 'usuario')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['tipo', 'item', 'usuario']
    search_fields = ['item__descricao', 'item__codigo', 'numero_documento']
    ordering = ['-data_movimentacao']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MovimentacaoCreateSerializer
        return MovimentacaoSerializer
    
    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class FornecedorViewSet(viewsets.ModelViewSet):
    queryset = Fornecedor.objects.filter(ativo=True)
    serializer_class = FornecedorSerializer
    permission_classes = [IsAuthenticated]


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.filter(ativo=True)
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated]


class RetiradaTemporariaViewSet(viewsets.ModelViewSet):
    queryset = RetiradaTemporaria.objects.all().select_related('item', 'usuario_retirada')
    serializer_class = RetiradaTemporariaSerializer
    permission_classes = [IsAuthenticated]