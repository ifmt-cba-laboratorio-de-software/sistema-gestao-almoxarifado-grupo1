from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User


class EstoqueManager:
    """
    Classe responsável por gerenciar alertas e status de estoque de um Item.
    Usada em views e APIs para identificar itens críticos, baixos, altos,
    bem como sugerir quantidade de reposição.
    """

    ESTOQUE_MAXIMO_PADRAO = 1000
    ESTOQUE_MINIMO_PADRAO = 300
    PERCENTUAL_CRITICO = Decimal('0.50')

    STATUS_CRITICO = 'CRITICO'
    STATUS_BAIXO = 'BAIXO'
    STATUS_OK = 'OK'
    STATUS_ALTO = 'ALTO'

    def __init__(self, item: "Item"):
        self.item = item

    # Atalhos para propriedades
    @property
    def quantidade_atual(self) -> int:
        return self.item.quantidade_atual or 0

    @property
    def estoque_minimo(self) -> int:
        if self.item.estoque_minimo and self.item.estoque_minimo > 0:
            return self.item.estoque_minimo
        return self.ESTOQUE_MINIMO_PADRAO

    @property
    def estoque_maximo(self) -> int:
        if self.item.estoque_maximo and self.item.estoque_maximo > 0:
            return self.item.estoque_maximo
        return self.ESTOQUE_MAXIMO_PADRAO

    # Regras de negócio de estoque

    def verifica_estoque_critico(self) -> bool:
        """
        Verdadeiro se a quantidade atual estiver abaixo de 50% do estoque mínimo.
        """
        limite_critico = int(self.estoque_minimo * self.PERCENTUAL_CRITICO)
        return self.quantidade_atual < limite_critico

    def verifica_estoque_baixo(self) -> bool:
        """
        Verdadeiro se a quantidade atual for menor que o estoque mínimo.
        """
        return self.quantidade_atual < self.estoque_minimo

    def verifica_estoque_alto(self) -> bool:
        """
        Verdadeiro se a quantidade atual for maior que o estoque máximo.
        """
        return self.quantidade_atual > self.estoque_maximo

    def get_percentual_estoque(self) -> float:
        """
        Percentual da quantidade atual em relação ao estoque mínimo.
        """
        if self.estoque_minimo == 0:
            return 0.0
        return float((Decimal(self.quantidade_atual) / Decimal(self.estoque_minimo)) * 100)

    def get_status_estoque(self) -> dict:
        """
        Retorna um dicionário com o status do item.
        """
        percentual = self.get_percentual_estoque()

        if self.verifica_estoque_critico():
            status = self.STATUS_CRITICO
            requer_acao = True
            mensagem = f"CRÍTICO: Estoque abaixo de 50% do mínimo ({self.quantidade_atual}/{self.estoque_minimo})"
        elif self.verifica_estoque_baixo():
            status = self.STATUS_BAIXO
            requer_acao = True
            mensagem = f"BAIXO: Estoque abaixo do mínimo ({self.quantidade_atual}/{self.estoque_minimo})"
        elif self.verifica_estoque_alto():
            status = self.STATUS_ALTO
            requer_acao = True
            mensagem = f"ALTO: Estoque acima do máximo ({self.quantidade_atual}/{self.estoque_maximo})"
        else:
            status = self.STATUS_OK
            requer_acao = False
            mensagem = f"OK: Estoque dentro dos limites ({self.quantidade_atual})"

        return {
            'status': status,
            'quantidade_atual': self.quantidade_atual,
            'estoque_minimo': self.estoque_minimo,
            'estoque_maximo': self.estoque_maximo,
            'percentual': round(percentual, 2),
            'requer_acao': requer_acao,
            'mensagem': mensagem,
            'item_id': self.item.id,
            'item_codigo': self.item.codigo,
            'item_descricao': self.item.descricao,
            'categoria': self.item.categoria,
        }

    def requer_reposicao(self) -> bool:
        """
        Verdadeiro se o item estiver crítico ou baixo.
        """
        return self.verifica_estoque_critico() or self.verifica_estoque_baixo()

    def get_nivel_urgencia(self) -> int:
        """
        Nível numérico de urgência (para ordenação).
        3 = crítico, 2 = baixo, 1 = alto, 0 = ok.
        """
        if self.verifica_estoque_critico():
            return 3
        if self.verifica_estoque_baixo():
            return 2
        if self.verifica_estoque_alto():
            return 1
        return 0

    def calcular_quantidade_reposicao(self) -> int:
        """
        Sugestão de quantidade de reposição para atingir o estoque máximo.
        """
        if self.quantidade_atual >= self.estoque_maximo:
            return 0
        return max(self.estoque_maximo - self.quantidade_atual, 0)


class Fornecedor(models.Model):
    nome = models.CharField(max_length=100)
    cnpj = models.CharField("CNPJ", max_length=18, blank=True, null=True)
    contato = models.CharField("Pessoa de Contato", max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)

    def __str__(self) -> str:
        return self.nome


class Item(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=150)
    categoria = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Categoria ou tipo de material (ex.: Limpeza, Escritório, Equipamento).",
    )
    unidade_medida = models.CharField(max_length=20)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    estoque_minimo = models.IntegerField(default=0)
    estoque_maximo = models.IntegerField(default=0)
    quantidade_atual = models.IntegerField(default=0)

    class Meta:
        ordering = ['descricao']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['descricao']),
            models.Index(fields=['categoria']),
        ]

    @property
    def valor_total_estoque(self) -> Decimal:
        """
        Valor total do estoque deste item (quantidade atual x valor unitário).
        """
        return (self.quantidade_atual or 0) * (self.valor_unitario or Decimal('0.00'))

    @property
    def estoque_manager(self) -> EstoqueManager:
        """
        Acesso ao gerenciador de estoque do item.
        Uso:
            status = item.estoque_manager.get_status_estoque()
        """
        return EstoqueManager(self)

    def __str__(self) -> str:
        return f"{self.codigo} - {self.descricao}"


class Movimentacao(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('RETIRADA', 'Retirada Temporária'),
        ('DEVOLUCAO', 'Devolução'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    quantidade = models.IntegerField()
    data = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_devolucao_prevista = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-data']
        indexes = [
            models.Index(fields=['item', 'data']),
            models.Index(fields=['tipo', 'data']),
        ]

    def _aplicar_efeito_no_estoque(self, fator: int) -> None:
        """
        Aplica ou reverte o efeito desta movimentação no estoque do item.
        fator = +1 para aplicar, -1 para reverter.
        """
        if self.tipo in ('ENTRADA', 'DEVOLUCAO'):
            self.item.quantidade_atual += fator * self.quantidade
        elif self.tipo in ('SAIDA', 'RETIRADA'):
            self.item.quantidade_atual -= fator * self.quantidade

        if self.item.quantidade_atual < 0:
            self.item.quantidade_atual = 0

        self.item.save(update_fields=['quantidade_atual'])

    def save(self, *args, **kwargs):
        """
        Garante que o estoque do item seja atualizado corretamente tanto
        para novas movimentações quanto para edições.
        """
        if self.pk:
            # Reverte efeito anterior antes de salvar nova versão
            antiga = Movimentacao.objects.get(pk=self.pk)
            antiga._aplicar_efeito_no_estoque(fator=-1)

        super().save(*args, **kwargs)
        self._aplicar_efeito_no_estoque(fator=1)

    def __str__(self) -> str:
        return f"{self.tipo} - {self.item.descricao} ({self.quantidade})"


class Solicitacao(models.Model):
    """
    Representa um pedido de material feito por um usuário,
    permitindo o acompanhamento do status da solicitação.
    """
    TIPO_CHOICES = [
        ('CONSUMO', 'Consumo'),
        ('TEMPORARIA', 'Retirada Temporária'),
    ]

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADA', 'Aprovada'),
        ('ATENDIDA', 'Atendida'),
        ('CANCELADA', 'Cancelada'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitacoes')
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_atendimento = models.DateTimeField(null=True, blank=True)
    data_devolucao_prevista = models.DateField(null=True, blank=True)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-data_solicitacao']
        indexes = [
            models.Index(fields=['item', 'status']),
            models.Index(fields=['solicitante', 'status']),
        ]

    def __str__(self) -> str:
        return f"Solicitação #{self.id} - {self.item.descricao} ({self.quantidade}) - {self.status}"
