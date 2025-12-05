from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from .models import Fornecedor, Item, Movimentacao
from .forms import FornecedorForm, ItemForm, MovimentacaoForm
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, date
from decimal import Decimal
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Case, When
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

def get_historical_stock_value(end_date):
    """
    Calcula o valor total do estoque em uma data específica
    somando o valor de todas as ENTREDAS e subtraindo o valor de todas as SAÍDAS
    até essa data.
    """
    
    # Adiciona o fuso horário à data final
    if not isinstance(end_date, datetime):
        end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

    # --- CORREÇÃO DO ERRO: Adicionar output_field em ExpressionWrapper ---
    
    # Define o custo negativo para as saídas (SAIDA, RETIRADA)
    CUSTO_NEGATIVO = ExpressionWrapper(
        F('quantidade') * F('item__valor_unitario') * Decimal('-1'),
        # Necessário para forçar o resultado da multiplicação a ser Decimal
        output_field=DecimalField() 
    )
    
    # Define o custo positivo para as entradas (ENTRADA, DEVOLUCAO)
    CUSTO_POSITIVO = ExpressionWrapper(
        F('quantidade') * F('item__valor_unitario'),
        # Necessário para forçar o resultado da multiplicação a ser Decimal
        output_field=DecimalField()
    )

    # Calcula a alteração líquida no valor do estoque até a data final
    stock_value = Movimentacao.objects.filter(
        data__lte=end_date
    ).select_related('item').annotate(
        # Cria o campo 'valor_movimentado'
        valor_movimentado=ExpressionWrapper(
            Case(
                # ENTRADA / DEVOLUCAO adiciona valor
                When(tipo__in=['ENTRADA', 'DEVOLUCAO'], 
                     then=CUSTO_POSITIVO),
                # SAIDA / RETIRADA reduz valor
                When(tipo__in=['SAIDA', 'RETIRADA'], 
                     then=CUSTO_NEGATIVO),
                # Garante que o Case inteiro retorne um Decimal
                default=Decimal('0.00'),
                output_field=DecimalField()
            ),
            output_field=DecimalField() # Garante que a anotação final é Decimal
        )
    ).aggregate(
        total_valor_estoque=Sum('valor_movimentado')
    )
    
    return stock_value.get('total_valor_estoque') or Decimal('0.00')


@login_required
@permission_required('estoque.view_movimentacao', raise_exception=True)
def relatorio_inventario_periodico(request):
    # --- 1. DEFINIÇÃO DO PERÍODO ---
    
    # Pega as datas do formulário (GET), ou usa a data de hoje/início do mês como padrão
    data_fim_default = date.today().strftime('%Y-%m-%d')
    data_inicio_default = date.today().replace(day=1).strftime('%Y-%m-%d') # Início do mês atual
    
    data_inicio_str = request.GET.get('data_inicio', data_inicio_default)
    data_fim_str = request.GET.get('data_fim', data_fim_default)
    
    try:
        data_inicio_date = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim_date = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        
        # Cria objetos datetime com horário de início e fim do dia para consultas precisas
        data_inicio = timezone.make_aware(datetime.combine(data_inicio_date, datetime.min.time()))
        data_fim = timezone.make_aware(datetime.combine(data_fim_date, datetime.max.time()))

    except ValueError:
        messages.error(request, "Formato de data inválido. Use AAAA-MM-DD.")
        return render(request, 'estoque/relatorio_cmv.html', {})
        
    # --- 2. CÁLCULO DAS VARIÁVEIS CHAVE ---
    
    # A. Estoque Inicial (EI): Valor total do estoque no final do dia anterior a data_inicio
    valor_estoque_inicial = get_historical_stock_value(data_inicio)
    
    # B. Compras Líquidas (C): Valor de todas as ENTRADAS no período
    compras_no_periodo = Movimentacao.objects.filter(
        tipo='ENTRADA',
        data__range=(data_inicio, data_fim)
    ).select_related('item')
    
    valor_compras_liquidas = Decimal('0.00')
    for mov in compras_no_periodo:
        # Soma o valor total de cada entrada (Quantidade * Custo Unitário)
        valor_compras_liquidas += mov.quantidade * mov.item.valor_unitario
        
    # C. Estoque Disponível para Uso (EDU): EI + C
    valor_estoque_disponivel = valor_estoque_inicial + valor_compras_liquidas
    
    # D. Estoque Final (EF): Valor total do estoque no final do dia de data_fim
    valor_estoque_final_contado = get_historical_stock_value(data_fim)

    # E. Custo de Uso (Saídas): EDU - EF
    # Custo de Uso = Estoque Inicial + Compras - Estoque Final
    custo_uso = valor_estoque_disponivel - valor_estoque_final_contado
    
    # Filtra os itens com estoque final > 0 para detalhamento
    itens_detalhe = Item.objects.all().filter(quantidade_atual__gt=0).order_by('descricao')
    
    context = {
        'data_inicio': data_inicio_str,
        'data_fim': data_fim_str,
        'valor_estoque_inicial': valor_estoque_inicial,
        'valor_compras_liquidas': valor_compras_liquidas,
        'valor_estoque_disponivel': valor_estoque_disponivel,
        'valor_estoque_final_contado': valor_estoque_final_contado,
        'custo_uso': custo_uso, # Variável renomeada
        'itens': itens_detalhe
    }

    return render(request, 'estoque/relatorio_cmv.html', context)

@login_required
def index(request):
    items = Item.objects.all().order_by('descricao')
    paginator = Paginator(items, 20)
    page = request.GET.get('page')
    items = paginator.get_page(page)
    return render(request, 'estoque/item_list.html', {'items': items})

#CRUD PRODUTO

#Criação do Produto
@login_required
@permission_required('estoque.add_item', raise_exception=True)
def item_create(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item criado com sucesso.')
            return redirect('index')
    else:
        form = ItemForm()
    return render(request, 'estoque/item_form.html', {'form': form})

#Alteração do Produto
@login_required
@permission_required('estoque.change_item', raise_exception=True)
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item atualizado com sucesso.')
            return redirect('index')
    else:
        form = ItemForm(instance=item)
    return render(request, 'estoque/item_form.html', {'form': form, 'item': item})

#Exclusão do Produto
@login_required
@permission_required('estoque.delete_item', raise_exception=True)
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    item.delete()
    messages.success(request, 'Item removido.')
    return redirect('index')

@login_required
@permission_required('estoque.add_movimentacao', raise_exception=True)
def movimentacao_create(request):
    if request.method == 'POST':
        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            mov = form.save(commit=False)
            mov.usuario = request.user
            mov.save()
            messages.success(request, 'Movimentação registrada.')
            return redirect('index')
    else:
        form = MovimentacaoForm()
    return render(request, 'estoque/movimentacao_form.html', {'form': form})

@login_required
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    movimentos = Movimentacao.objects.filter(item=item).order_by('-data')[:50]
    return render(request, 'estoque/item_detail.html', {'item': item, 'movimentos': movimentos})



# CRUD FORNECEDORES

@login_required
@permission_required('estoque.view_fornecedor', raise_exception=True)
def fornecedor_list(request):
    fornecedores = Fornecedor.objects.all().order_by('nome')
    paginator = Paginator(fornecedores, 20)
    page = request.GET.get('page')
    fornecedores = paginator.get_page(page)
    return render(request, 'estoque/fornecedor_list.html', {'fornecedores': fornecedores})

@login_required
@permission_required('estoque.add_fornecedor', raise_exception=True)
def fornecedor_create(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor criado com sucesso.')
            return redirect('fornecedor_list')
    else:
        form = FornecedorForm()
    return render(request, 'estoque/fornecedor_form.html', {'form': form})

@login_required
@permission_required('estoque.change_fornecedor', raise_exception=True)
def fornecedor_edit(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor atualizado com sucesso.')
            return redirect('fornecedor_list')
    else:
        form = FornecedorForm(instance=fornecedor)
    return render(request, 'estoque/fornecedor_form.html', {'form': form, 'fornecedor': fornecedor})

@login_required
@permission_required('estoque.delete_fornecedor', raise_exception=True)
def fornecedor_delete(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    
    # Verifica se o fornecedor está sendo usado por algum item
    if Item.objects.filter(fornecedor=fornecedor).exists():
        messages.error(request, 'Este fornecedor não pode ser excluído, pois está associado a um ou mais itens.')
        return redirect('fornecedor_list')
        
    fornecedor.delete()
    messages.success(request, 'Fornecedor removido com sucesso.')
    return redirect('fornecedor_list')



# ================================
# VIEWS DE BUSCA ITEM E FORNECEDOR(HTMX)
# ================================

@login_required
def buscar_item(request):
    search_text = request.GET.get('q', '').strip()

    if search_text:
        # Usamos Q para buscar no código OU na descrição (icontains não diferencia maiúsculas/minúsculas)
        items = Item.objects.filter(
            Q(codigo__icontains=search_text) | 
            Q(descricao__icontains=search_text)
        ).order_by('descricao')
    else:
        # Se a busca estiver vazia, retorna tudo (limitado para não sobrecarregar)
        items = Item.objects.all().order_by('descricao')[:50] 

    # Renderiza APENAS o template parcial com os resultados
    return render(request, 'estoque/partials/tabela_itens.html', {'items': items})


@login_required
@permission_required('estoque.view_fornecedor', raise_exception=True)
def buscar_fornecedor(request):
    search_text = request.GET.get('q', '').strip()

    if search_text:
        # Busca por Nome, CNPJ ou Email
        fornecedores = Fornecedor.objects.filter(
            Q(nome__icontains=search_text) |
            Q(cnpj__icontains=search_text) |
            Q(email__icontains=search_text)
        ).order_by('nome')
    else:
        fornecedores = Fornecedor.objects.all().order_by('nome')[:50]

    # Renderiza APENAS o template parcial
    return render(request, 'estoque/partials/tabela_fornecedores.html', {'fornecedores': fornecedores})


# ================================
# API DE ALERTAS DE ESTOQUE
# ================================

@login_required
@require_http_methods(["GET"])
def api_alertas_estoque(request):
    """
    API REST que retorna todos os alertas de estoque.
    
    Endpoint: GET /api/alertas/
    
    Retorna JSON com:
    - resumo: contadores por tipo de alerta
    - alertas: lista de todos os itens com alertas
    
    Exemplo de resposta:
    {
        "resumo": {
            "total_alertas": 5,
            "criticos": 2,
            "baixos": 2,
            "altos": 1
        },
        "alertas": [
            {
                "status": "CRITICO",
                "item_id": 1,
                "item_codigo": "ITEM001",
                "item_descricao": "Parafuso M6",
                "quantidade_atual": 100,
                "estoque_minimo": 300,
                "estoque_maximo": 1000,
                "percentual": 33.33,
                "requer_acao": true,
                "mensagem": "CRÍTICO: Estoque abaixo de 50% do mínimo (100/300)",
                "nivel_urgencia": 3,
                "quantidade_reposicao_sugerida": 900
            }
        ]
    }
    """
    itens = Item.objects.all()
    alertas = []
    contadores = {
        'criticos': 0,
        'baixos': 0,
        'altos': 0
    }
    
    for item in itens:
        manager = item.estoque_manager
        status_info = manager.get_status_estoque()
        
        # Só adiciona aos alertas se requer ação
        if status_info['requer_acao']:
            status_info['nivel_urgencia'] = manager.get_nivel_urgencia()
            status_info['quantidade_reposicao_sugerida'] = manager.calcular_quantidade_reposicao()
            alertas.append(status_info)
            
            # Atualiza contadores
            if status_info['status'] == 'CRITICO':
                contadores['criticos'] += 1
            elif status_info['status'] == 'BAIXO':
                contadores['baixos'] += 1
            elif status_info['status'] == 'ALTO':
                contadores['altos'] += 1
    
    # Ordena por nível de urgência (mais urgente primeiro)
    alertas.sort(key=lambda x: x['nivel_urgencia'], reverse=True)
    
    response_data = {
        'resumo': {
            'total_alertas': len(alertas),
            'criticos': contadores['criticos'],
            'baixos': contadores['baixos'],
            'altos': contadores['altos']
        },
        'alertas': alertas
    }
    
    return JsonResponse(response_data, safe=False)


@login_required
@require_http_methods(["GET"])
def api_status_item(request, item_id):
    """
    API REST que retorna o status de estoque de um item específico.
    
    Endpoint: GET /api/item/<id>/status/
    
    Parâmetros:
    - item_id: ID do item
    
    Retorna JSON com informações detalhadas do status do estoque do item.
    
    Exemplo de resposta:
    {
        "status": "BAIXO",
        "item_id": 1,
        "item_codigo": "ITEM001",
        "item_descricao": "Parafuso M6",
        "quantidade_atual": 250,
        "estoque_minimo": 300,
        "estoque_maximo": 1000,
        "percentual": 83.33,
        "requer_acao": true,
        "mensagem": "BAIXO: Estoque abaixo do mínimo (250/300)",
        "nivel_urgencia": 2,
        "quantidade_reposicao_sugerida": 750
    }
    """
    item = get_object_or_404(Item, pk=item_id)
    manager = item.estoque_manager
    status_info = manager.get_status_estoque()
    status_info['nivel_urgencia'] = manager.get_nivel_urgencia()
    status_info['quantidade_reposicao_sugerida'] = manager.calcular_quantidade_reposicao()
    
    return JsonResponse(status_info)


@login_required
@require_http_methods(["GET"])
def api_itens_criticos(request):
    """
    API REST que retorna apenas os itens com estoque crítico.
    
    Endpoint: GET /api/itens/criticos/
    
    Retorna JSON com lista de itens em estado crítico (abaixo de 50% do mínimo).
    """
    itens = Item.objects.all()
    itens_criticos = []
    
    for item in itens:
        manager = item.estoque_manager
        if manager.verifica_estoque_critico():
            status_info = manager.get_status_estoque()
            status_info['nivel_urgencia'] = manager.get_nivel_urgencia()
            status_info['quantidade_reposicao_sugerida'] = manager.calcular_quantidade_reposicao()
            itens_criticos.append(status_info)
    
    return JsonResponse({
        'total': len(itens_criticos),
        'itens_criticos': itens_criticos
    })


@login_required
@require_http_methods(["GET"])
def api_itens_reposicao(request):
    """
    API REST que retorna itens que necessitam reposição.
    
    Endpoint: GET /api/itens/reposicao/
    
    Retorna JSON com lista de itens que precisam de reposição (críticos ou baixos).
    """
    itens = Item.objects.all()
    itens_reposicao = []
    
    for item in itens:
        manager = item.estoque_manager
        if manager.requer_reposicao():
            status_info = manager.get_status_estoque()
            status_info['nivel_urgencia'] = manager.get_nivel_urgencia()
            status_info['quantidade_reposicao_sugerida'] = manager.calcular_quantidade_reposicao()
            itens_reposicao.append(status_info)
    
    # Ordena por urgência
    itens_reposicao.sort(key=lambda x: x['nivel_urgencia'], reverse=True)
    
    return JsonResponse({
        'total': len(itens_reposicao),
        'itens': itens_reposicao
    })