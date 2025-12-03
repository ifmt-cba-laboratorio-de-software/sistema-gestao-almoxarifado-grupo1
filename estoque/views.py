from datetime import datetime, date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, DecimalField, ExpressionWrapper, Case, When
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from openpyxl import Workbook

from .forms import (
    FornecedorForm,
    ItemForm,
    MovimentacaoForm,
    SolicitacaoForm,
)
from .models import Fornecedor, Item, Movimentacao, Solicitacao


# ----------------------------------------------------------------------
# Helper para valor de estoque em uma data (histórico)
# ----------------------------------------------------------------------
def get_historical_stock_value(end_date: date, categoria: str | None = None) -> Decimal:
    """
    Calcula o valor do estoque em uma data de corte usando as movimentações
    registradas até o final desse dia.

    Considera:
        - ENTRADA / DEVOLUCAO => +quantidade * valor_unitario
        - SAIDA / RETIRADA    => -quantidade * valor_unitario
    """
    if not isinstance(end_date, date):
        raise ValueError("end_date deve ser date")

    dt_end = timezone.make_aware(
        datetime.combine(end_date, datetime.max.time())
    )

    qs = Movimentacao.objects.filter(data__lte=dt_end).select_related('item')

    if categoria:
        qs = qs.filter(item__categoria=categoria)

    valor_movimentado = ExpressionWrapper(
        F('quantidade') * F('item__valor_unitario'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    qs = qs.annotate(
        valor_movimentado=Case(
            When(tipo__in=['ENTRADA', 'DEVOLUCAO'], then=valor_movimentado),
            When(tipo__in=['SAIDA', 'RETIRADA'], then=-valor_movimentado),
            default=Decimal('0.00'),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    )

    total = qs.aggregate(
        total_valor_estoque=Sum('valor_movimentado')
    )['total_valor_estoque'] or Decimal('0.00')

    return total


# ----------------------------------------------------------------------
# Itens – tela central / CRUD
# ----------------------------------------------------------------------
@login_required
@permission_required('estoque.view_item', raise_exception=True)
def index(request):
    """
    Tela central do almoxarifado: lista de itens com busca, paginação
    e resumo de alertas de estoque.
    """
    search_text = request.GET.get('q', '').strip()

    itens_qs = Item.objects.all().order_by('descricao')
    if search_text:
        itens_qs = itens_qs.filter(
            Q(codigo__icontains=search_text) |
            Q(descricao__icontains=search_text)
        )

    paginator = Paginator(itens_qs, 20)
    page_number = request.GET.get('page')
    items_page = paginator.get_page(page_number)

    # Resumo de alertas (para badge no topo)
    total = itens_qs.count()
    criticos = 0
    baixos = 0
    altos = 0

    for item in itens_qs:
        status_info = item.estoque_manager.get_status_estoque()
        if status_info['status'] == item.estoque_manager.STATUS_CRITICO:
            criticos += 1
        elif status_info['status'] == item.estoque_manager.STATUS_BAIXO:
            baixos += 1
        elif status_info['status'] == item.estoque_manager.STATUS_ALTO:
            altos += 1

    contexto = {
        'items': items_page,
        'resumo_alertas': {
            'total_itens': total,
            'criticos': criticos,
            'baixos': baixos,
            'altos': altos,
        },
        'search_text': search_text,
    }
    return render(request, 'estoque/item_list.html', contexto)


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


@login_required
@permission_required('estoque.delete_item', raise_exception=True)
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        nome = item.descricao
        item.delete()
        messages.success(request, f"Item '{nome}' excluído com sucesso.")
        return redirect('index')
    # Confirmar exclusão via tela simples (SweetAlert na UI principal também pode ser usado)
    return render(request, 'estoque/item_detail.html', {'item': item})


@login_required
@permission_required('estoque.view_item', raise_exception=True)
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    movimentos = Movimentacao.objects.filter(item=item).order_by('-data')[:50]
    status = item.estoque_manager.get_status_estoque()
    return render(
        request,
        'estoque/item_detail.html',
        {'item': item, 'movimentos': movimentos, 'status_estoque': status},
    )


@login_required
@permission_required('estoque.view_item', raise_exception=True)
def buscar_item(request):
    """
    Usado por HTMX para atualizar a tabela de itens.
    """
    search_text = request.GET.get('q', '').strip()

    items = Item.objects.all().order_by('descricao')
    if search_text:
        items = items.filter(
            Q(codigo__icontains=search_text) |
            Q(descricao__icontains=search_text)
        )

    return render(
        request,
        'estoque/partials/tabela_itens.html',
        {'items': items},
    )


# ----------------------------------------------------------------------
# Movimentações
# ----------------------------------------------------------------------
@login_required
@permission_required('estoque.add_movimentacao', raise_exception=True)
def movimentacao_create(request):
    if request.method == 'POST':
        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            mov = form.save(commit=False)
            mov.usuario = request.user
            mov.save()
            messages.success(request, 'Movimentação registrada com sucesso.')
            return redirect('index')
    else:
        form = MovimentacaoForm()
    return render(request, 'estoque/movimentacao_form.html', {'form': form})


# ----------------------------------------------------------------------
# Fornecedores – CRUD
# ----------------------------------------------------------------------
@login_required
@permission_required('estoque.view_fornecedor', raise_exception=True)
def fornecedor_list(request):
    fornecedores_qs = Fornecedor.objects.all().order_by('nome')

    search_text = request.GET.get('q', '').strip()
    if search_text:
        fornecedores_qs = fornecedores_qs.filter(
            Q(nome__icontains=search_text) |
            Q(cnpj__icontains=search_text)
        )

    paginator = Paginator(fornecedores_qs, 20)
    page_number = request.GET.get('page')
    fornecedores_page = paginator.get_page(page_number)

    return render(
        request,
        'estoque/fornecedor_list.html',
        {'fornecedores': fornecedores_page},
    )


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
    return render(
        request,
        'estoque/fornecedor_form.html',
        {'form': form, 'fornecedor': fornecedor},
    )


@login_required
@permission_required('estoque.delete_fornecedor', raise_exception=True)
def fornecedor_delete(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        nome = fornecedor.nome
        fornecedor.delete()
        messages.success(request, f"Fornecedor '{nome}' excluído com sucesso.")
        return redirect('fornecedor_list')
    return render(request, 'estoque/fornecedor_list.html', {})


@login_required
@permission_required('estoque.view_fornecedor', raise_exception=True)
def buscar_fornecedor(request):
    search_text = request.GET.get('q', '').strip()
    fornecedores = Fornecedor.objects.all().order_by('nome')

    if search_text:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=search_text) |
            Q(cnpj__icontains=search_text)
        )

    return render(
        request,
        'estoque/partials/tabela_fornecedores.html',
        {'fornecedores': fornecedores},
    )


# ----------------------------------------------------------------------
# Relatório de Inventário Periódico (US1, US2, US3)
# ----------------------------------------------------------------------
@login_required
@permission_required('estoque.view_movimentacao', raise_exception=True)
def relatorio_inventario_periodico(request):
    # Datas padrão: início do mês até hoje
    data_fim_default = date.today()
    data_inicio_default = data_fim_default.replace(day=1)

    data_inicio_str = request.GET.get('data_inicio', data_inicio_default.strftime('%Y-%m-%d'))
    data_fim_str = request.GET.get('data_fim', data_fim_default.strftime('%Y-%m-%d'))
    categoria_selecionada = request.GET.get('categoria') or ''

    try:
        data_inicio_date = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim_date = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Datas inválidas. Use o formato AAAA-MM-DD.')
        data_inicio_date = data_inicio_default
        data_fim_date = data_fim_default

    # Estoque inicial (dia anterior ao início do período)
    dia_anterior_inicio = data_inicio_date - timedelta(days=1)
    valor_estoque_inicial = get_historical_stock_value(
        dia_anterior_inicio,
        categoria=categoria_selecionada or None,
    )

    # Compras (entradas) no período
    entradas_qs = Movimentacao.objects.filter(
        tipo='ENTRADA',
        data__date__range=(data_inicio_date, data_fim_date),
    ).select_related('item')

    if categoria_selecionada:
        entradas_qs = entradas_qs.filter(item__categoria=categoria_selecionada)

    valor_compras_liquidas = Decimal('0.00')
    for mov in entradas_qs:
        valor_compras_liquidas += mov.quantidade * (mov.item.valor_unitario or Decimal('0.00'))

    # Estoque disponível para uso
    valor_estoque_disponivel = valor_estoque_inicial + valor_compras_liquidas

    # Estoque final (na data_fim)
    valor_estoque_final_contado = get_historical_stock_value(
        data_fim_date,
        categoria=categoria_selecionada or None,
    )

    # Custo de uso
    custo_uso = valor_estoque_disponivel - valor_estoque_final_contado

    # Detalhamento de itens (estoque atual)
    itens_qs = Item.objects.all()
    if categoria_selecionada:
        itens_qs = itens_qs.filter(categoria=categoria_selecionada)

    itens_qs = itens_qs.order_by('descricao')

    # Exportação Excel
    export = request.GET.get('export')
    if export == 'excel':
        return _exportar_relatorio_excel(
            itens_qs,
            data_inicio_date,
            data_fim_date,
            valor_estoque_inicial,
            valor_compras_liquidas,
            valor_estoque_final_contado,
            custo_uso,
            categoria_selecionada,
        )

    # Lista de categorias distintas
    categorias = (
        Item.objects.exclude(categoria__isnull=True)
        .exclude(categoria__exact='')
        .values_list('categoria', flat=True)
        .distinct()
        .order_by('categoria')
    )

    context = {
        'data_inicio': data_inicio_str,
        'data_fim': data_fim_str,
        'categoria_selecionada': categoria_selecionada,
        'categorias': categorias,
        'valor_estoque_inicial': valor_estoque_inicial,
        'valor_compras_liquidas': valor_compras_liquidas,
        'valor_estoque_disponivel': valor_estoque_disponivel,
        'valor_estoque_final_contado': valor_estoque_final_contado,
        'custo_uso': custo_uso,
        'itens': itens_qs,
    }
    return render(request, 'estoque/relatorio_cmv.html', context)


def _exportar_relatorio_excel(
    itens_qs,
    data_inicio_date,
    data_fim_date,
    valor_estoque_inicial,
    valor_compras_liquidas,
    valor_estoque_final_contado,
    custo_uso,
    categoria,
):
    """
    Gera um arquivo Excel com resumo e detalhamento do relatório.
    """
    wb = Workbook()
    ws_resumo = wb.active
    ws_resumo.title = "Resumo"

    ws_resumo.append(["Relatório de Inventário Periódico"])
    ws_resumo.append([f"Período: {data_inicio_date} a {data_fim_date}"])
    if categoria:
        ws_resumo.append([f"Categoria: {categoria}"])
    ws_resumo.append([])

    ws_resumo.append(["Descrição", "Valor"])
    ws_resumo.append(["Estoque Inicial", float(valor_estoque_inicial)])
    ws_resumo.append(["Compras (Entradas)", float(valor_compras_liquidas)])
    ws_resumo.append(["Estoque Final", float(valor_estoque_final_contado)])
    ws_resumo.append(["Custo de Uso", float(custo_uso)])

    # Aba de Itens
    ws_itens = wb.create_sheet("Itens")
    ws_itens.append(["Código", "Descrição", "Categoria", "Qtd. Atual", "Valor Unitário", "Valor Total"])

    for item in itens_qs:
        ws_itens.append([
            item.codigo,
            item.descricao,
            item.categoria or "",
            item.quantidade_atual,
            float(item.valor_unitario or 0),
            float(item.valor_total_estoque),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"relatorio_estoque_{data_inicio_date}_{data_fim_date}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


# ----------------------------------------------------------------------
# Solicitações – acompanhamento de status
# ----------------------------------------------------------------------
@login_required
def solicitacao_list(request):
    """
    Lista de solicitações.
    - Usuário com permissão 'view_solicitacao' vê tudo.
    - Demais usuários veem apenas as próprias solicitações.
    """
    if request.user.has_perm('estoque.view_solicitacao'):
        qs = Solicitacao.objects.select_related('item', 'solicitante')
    else:
        qs = Solicitacao.objects.filter(solicitante=request.user).select_related('item', 'solicitante')

    status_filtro = request.GET.get('status', '').strip()
    if status_filtro:
        qs = qs.filter(status=status_filtro)

    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    solicitacoes_page = paginator.get_page(page_number)

    return render(
        request,
        'estoque/solicitacao_list.html',
        {'solicitacoes': solicitacoes_page, 'status_filtro': status_filtro},
    )


@login_required
def solicitacao_create(request):
    """
    Cria uma nova solicitação de material.
    """
    if request.method == 'POST':
        form = SolicitacaoForm(request.POST)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.solicitante = request.user
            solicitacao.status = 'PENDENTE'
            solicitacao.save()
            messages.success(request, 'Solicitação registrada com sucesso.')
            return redirect('solicitacao_list')
    else:
        form = SolicitacaoForm()
    return render(request, 'estoque/solicitacao_form.html', {'form': form})


@login_required
def solicitacao_detail(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    # Usuário comum só pode ver a própria solicitação
    if not request.user.has_perm('estoque.view_solicitacao') and solicitacao.solicitante != request.user:
        messages.error(request, 'Você não tem permissão para visualizar esta solicitação.')
        return redirect('solicitacao_list')

    return render(
        request,
        'estoque/solicitacao_detail.html',
        {'solicitacao': solicitacao},
    )


# ----------------------------------------------------------------------
# APIs de alertas de estoque
# ----------------------------------------------------------------------
@login_required
@permission_required('estoque.view_item', raise_exception=True)
@require_http_methods(["GET"])
def api_alertas_estoque(request):
    """
    Retorna todos os alertas de estoque com resumo.
    """
    itens = Item.objects.all()
    alertas = []

    resumo = {
        'total_alertas': 0,
        'criticos': 0,
        'baixos': 0,
        'altos': 0,
    }

    for item in itens:
        manager = item.estoque_manager
        status_info = manager.get_status_estoque()
        if status_info['requer_acao']:
            alertas.append(status_info)
            resumo['total_alertas'] += 1
            if status_info['status'] == manager.STATUS_CRITICO:
                resumo['criticos'] += 1
            elif status_info['status'] == manager.STATUS_BAIXO:
                resumo['baixos'] += 1
            elif status_info['status'] == manager.STATUS_ALTO:
                resumo['altos'] += 1

    return JsonResponse({'resumo': resumo, 'alertas': alertas}, safe=False)


@login_required
@permission_required('estoque.view_item', raise_exception=True)
@require_http_methods(["GET"])
def api_status_item(request, item_id):
    """
    Retorna o status de estoque de um item específico.
    """
    item = get_object_or_404(Item, pk=item_id)
    status_info = item.estoque_manager.get_status_estoque()
    return JsonResponse(status_info, safe=False)


@login_required
@permission_required('estoque.view_item', raise_exception=True)
@require_http_methods(["GET"])
def api_itens_criticos(request):
    """
    Lista itens em situação crítica.
    """
    itens = Item.objects.all()
    criticos = []

    for item in itens:
        manager = item.estoque_manager
        if manager.verifica_estoque_critico():
            criticos.append(manager.get_status_estoque())

    return JsonResponse({'total': len(criticos), 'itens': criticos}, safe=False)


@login_required
@permission_required('estoque.view_item', raise_exception=True)
@require_http_methods(["GET"])
def api_itens_reposicao(request):
    """
    Lista itens que precisam de reposição (baixo ou crítico).
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

    itens_reposicao.sort(key=lambda x: x['nivel_urgencia'], reverse=True)

    return JsonResponse({'total': len(itens_reposicao), 'itens': itens_reposicao}, safe=False)
