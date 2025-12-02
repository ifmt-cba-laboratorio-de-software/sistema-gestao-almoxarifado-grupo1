# estoque/models.py

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class EstoqueManager:
    """
    Classe responsável por gerenciar alertas e status de estoque de itens.
    
    Valores de referência:
    - ESTOQUE_MAXIMO_PADRAO: 1000 unidades
    - ESTOQUE_MINIMO_PADRAO: 300 unidades
    - PERCENTUAL_CRITICO: 50% do estoque mínimo (150 unidades)
    
    Status possíveis:
    - CRITICO: Quantidade < 50% do estoque mínimo
    - BAIXO: Quantidade < estoque mínimo
    - OK: Quantidade entre mínimo e máximo
    - ALTO: Quantidade > estoque máximo
    """
    
    ESTOQUE_MAXIMO_PADRAO = 1000
    ESTOQUE_MINIMO_PADRAO = 300
    PERCENTUAL_CRITICO = 0.5  # 50% do estoque mínimo
    
    STATUS_CRITICO = 'CRITICO'
    STATUS_BAIXO = 'BAIXO'
    STATUS_OK = 'OK'
    STATUS_ALTO = 'ALTO'
    
    def __init__(self, item):
        """
        Inicializa o gerenciador com uma instância de Item.
        
        Args:
            item (Item): Instância do modelo Item
        """
        self.item = item
        self.estoque_minimo = item.estoque_minimo if item.estoque_minimo > 0 else self.ESTOQUE_MINIMO_PADRAO
        self.estoque_maximo = item.estoque_maximo if item.estoque_maximo > 0 else self.ESTOQUE_MAXIMO_PADRAO
        self.quantidade_atual = item.quantidade_atual
    
    def verifica_estoque_critico(self):
        """
        Verifica se o estoque está em nível crítico (abaixo de 50% do mínimo).
        
        Returns:
            bool: True se crítico, False caso contrário
        """
        limite_critico = self.estoque_minimo * self.PERCENTUAL_CRITICO
        return self.quantidade_atual < limite_critico
    
    def verifica_estoque_baixo(self):
        """
        Verifica se o estoque está abaixo do nível mínimo.
        
        Returns:
            bool: True se baixo, False caso contrário
        """
        return self.quantidade_atual < self.estoque_minimo
    
    def verifica_estoque_alto(self):
        """
        Verifica se o estoque está acima do nível máximo.
        
        Returns:
            bool: True se alto, False caso contrário
        """
        return self.quantidade_atual > self.estoque_maximo
    
    def get_percentual_estoque(self):
        """
        Calcula o percentual do estoque atual em relação ao mínimo.
        
        Returns:
            float: Percentual (0-100+) do estoque em relação ao mínimo
        """
        if self.estoque_minimo == 0:
            return 0.0
        return (self.quantidade_atual / self.estoque_minimo) * 100
    
    def get_status_estoque(self):
        """
        Retorna o status atual do estoque com informações detalhadas.
        
        Returns:
            dict: Dicionário contendo:
                - status (str): STATUS_CRITICO, STATUS_BAIXO, STATUS_OK ou STATUS_ALTO
                - quantidade_atual (int): Quantidade em estoque
                - estoque_minimo (int): Limite mínimo
                - estoque_maximo (int): Limite máximo
                - percentual (float): Percentual em relação ao mínimo
                - requer_acao (bool): Se requer ação imediata
                - mensagem (str): Descrição do status
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
            'item_descricao': self.item.descricao
        }
    
    def requer_reposicao(self):
        """
        Verifica se o item requer reposição imediata.
        
        Returns:
            bool: True se requer reposição (crítico ou baixo), False caso contrário
        """
        return self.verifica_estoque_critico() or self.verifica_estoque_baixo()
    
    def calcular_quantidade_reposicao(self):
        """
        Calcula a quantidade sugerida para reposição até atingir o estoque máximo.
        
        Returns:
            int: Quantidade sugerida para reposição (0 se não necessário)
        """
        if not self.requer_reposicao():
            return 0
        return max(0, self.estoque_maximo - self.quantidade_atual)
    
    def get_nivel_urgencia(self):
        """
        Retorna o nível de urgência para ação no estoque.
        
        Returns:
            int: 0 (OK), 1 (ALTO), 2 (BAIXO), 3 (CRÍTICO)
        """
        if self.verifica_estoque_critico():
            return 3
        elif self.verifica_estoque_baixo():
            return 2
        elif self.verifica_estoque_alto():
            return 1
        return 0

class Fornecedor(models.Model):
    nome = models.CharField(max_length=100) # Nome/Razão Social
    cnpj = models.CharField("CNPJ", max_length=18, blank=True, null=True)
    contato = models.CharField("Pessoa de Contato", max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nome

class Item(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=150)
    unidade_medida = models.CharField(max_length=20)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.SET_NULL, null=True, blank=True)
    estoque_minimo = models.IntegerField(default=0)
    estoque_maximo = models.IntegerField(default=0)
    quantidade_atual = models.IntegerField(default=0)

    # NOVO: Calcula o valor total deste item em estoque
    @property
    def valor_total_estoque(self):
        # O cálculo deve ser feito com o custo (valor_unitario)
        return self.quantidade_atual * self.valor_unitario
    
    @property
    def estoque_manager(self):
        """
        Retorna uma instância do EstoqueManager para este item.
        
        Uso:
            item = Item.objects.get(pk=1)
            status = item.estoque_manager.get_status_estoque()
            if item.estoque_manager.requer_reposicao():
                print("Necessário repor estoque!")
        
        Returns:
            EstoqueManager: Instância do gerenciador de estoque
        """
        return EstoqueManager(self)

    def __str__(self):
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

    def save(self, *args, **kwargs):
        # Salva movimentação e atualiza estoque do item
        super().save(*args, **kwargs)
        if self.tipo == 'ENTRADA' or self.tipo == 'DEVOLUÇÃO':
            self.item.quantidade_atual += self.quantidade
        elif self.tipo in ('SAIDA', 'RETIRADA'):
            self.item.quantidade_atual -= self.quantidade
            if self.item.quantidade_atual < 0:
                self.item.quantidade_atual = 0
        self.item.save()

    def __str__(self):
        return f"{self.tipo} - {self.item.descricao} ({self.quantidade})"