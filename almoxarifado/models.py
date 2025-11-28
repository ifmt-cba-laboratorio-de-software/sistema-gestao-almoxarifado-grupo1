from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Fornecedor(models.Model):
    nome = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fornecedor'
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = 'categoria'
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nome


class Item(models.Model):
    UNIDADE_CHOICES = [
        ('UN', 'Unidade'),
        ('CX', 'Caixa'),
        ('KG', 'Quilograma'),
        ('LT', 'Litro'),
        ('MT', 'Metro'),
        ('PC', 'Peça'),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    descricao = models.CharField(max_length=255)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='itens')
    unidade_medida = models.CharField(max_length=2, choices=UNIDADE_CHOICES)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, related_name='itens')
    
    # Controle de estoque
    quantidade_atual = models.IntegerField(default=0)
    estoque_minimo = models.IntegerField(default=0)
    estoque_maximo = models.IntegerField(default=0)
    
    localizacao = models.CharField(max_length=100, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'item'
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['descricao']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

    @property
    def esta_abaixo_minimo(self):
        return self.quantidade_atual < self.estoque_minimo

    @property
    def esta_acima_maximo(self):
        return self.quantidade_atual > self.estoque_maximo

    @property
    def valor_total_estoque(self):
        return self.quantidade_atual * self.valor_unitario


class Movimentacao(models.Model):
    TIPO_CHOICES = [
        ('E', 'Entrada'),
        ('S', 'Saída'),
        ('A', 'Ajuste'),
        ('T', 'Transferência'),
    ]

    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='movimentacoes')
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    quantidade = models.IntegerField(validators=[MinValueValidator(1)])
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='movimentacoes')
    
    data_movimentacao = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True)
    
    # Campos para controle
    numero_documento = models.CharField(max_length=50, blank=True)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Estoque antes e depois
    estoque_anterior = models.IntegerField()
    estoque_posterior = models.IntegerField()

    class Meta:
        db_table = 'movimentacao'
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'
        ordering = ['-data_movimentacao']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.item.descricao} - {self.quantidade}"

    @property
    def valor_total(self):
        if self.valor_unitario:
            return self.quantidade * self.valor_unitario
        return self.item.valor_unitario * self.quantidade

    def save(self, *args, **kwargs):
        # Registra estoque anterior
        self.estoque_anterior = self.item.quantidade_atual
        
        # Atualiza estoque do item
        if self.tipo == 'E':  # Entrada
            self.item.quantidade_atual += self.quantidade
        elif self.tipo == 'S':  # Saída
            if self.item.quantidade_atual < self.quantidade:
                raise ValueError(f"Estoque insuficiente. Disponível: {self.item.quantidade_atual}")
            self.item.quantidade_atual -= self.quantidade
        elif self.tipo == 'A':  # Ajuste
            self.item.quantidade_atual = self.quantidade
        
        # Registra estoque posterior
        self.estoque_posterior = self.item.quantidade_atual
        
        self.item.save()
        super().save(*args, **kwargs)


class RetiradaTemporaria(models.Model):
    STATUS_CHOICES = [
        ('A', 'Ativa'),
        ('D', 'Devolvida'),
        ('P', 'Parcialmente Devolvida'),
    ]

    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='retiradas')
    usuario_retirada = models.ForeignKey(User, on_delete=models.PROTECT, related_name='retiradas')
    quantidade_retirada = models.IntegerField(validators=[MinValueValidator(1)])
    quantidade_devolvida = models.IntegerField(default=0)
    
    data_retirada = models.DateTimeField(auto_now_add=True)
    data_prevista_devolucao = models.DateTimeField()
    data_devolucao = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    observacao = models.TextField(blank=True)
    setor_destino = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'retirada_temporaria'
        verbose_name = 'Retirada Temporária'
        verbose_name_plural = 'Retiradas Temporárias'
        ordering = ['-data_retirada']

    def __str__(self):
        return f"{self.item.descricao} - {self.usuario_retirada.username} - {self.quantidade_retirada}"

    @property
    def quantidade_pendente(self):
        return self.quantidade_retirada - self.quantidade_devolvida

    @property
    def esta_atrasada(self):
        from django.utils import timezone
        if self.status == 'A' and self.data_prevista_devolucao < timezone.now():
            return True
        return False