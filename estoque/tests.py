"""
Testes unitários para o sistema de gerenciamento de estoque.

Execução dos testes:
    python manage.py test estoque
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from decimal import Decimal
from .models import Item, Fornecedor, EstoqueManager


class EstoqueManagerTestCase(TestCase):
    """Testes para a classe EstoqueManager"""
    
    def setUp(self):
        """Configura dados de teste"""
        self.fornecedor = Fornecedor.objects.create(
            nome="Fornecedor Teste",
            cnpj="12.345.678/0001-90"
        )
        
        # Item com estoque crítico (abaixo de 50% do mínimo)
        self.item_critico = Item.objects.create(
            codigo="CRIT001",
            descricao="Item Crítico",
            unidade_medida="UN",
            valor_unitario=Decimal("10.00"),
            fornecedor=self.fornecedor,
            estoque_minimo=300,
            estoque_maximo=1000,
            quantidade_atual=100  # Menos de 50% do mínimo (150)
        )
        
        # Item com estoque baixo (abaixo do mínimo)
        self.item_baixo = Item.objects.create(
            codigo="BAIX001",
            descricao="Item Baixo",
            unidade_medida="UN",
            valor_unitario=Decimal("15.00"),
            fornecedor=self.fornecedor,
            estoque_minimo=300,
            estoque_maximo=1000,
            quantidade_atual=250  # Abaixo do mínimo mas acima de 50%
        )
        
        # Item com estoque OK
        self.item_ok = Item.objects.create(
            codigo="OK001",
            descricao="Item OK",
            unidade_medida="UN",
            valor_unitario=Decimal("20.00"),
            fornecedor=self.fornecedor,
            estoque_minimo=300,
            estoque_maximo=1000,
            quantidade_atual=500  # Entre mínimo e máximo
        )
        
        # Item com estoque alto (acima do máximo)
        self.item_alto = Item.objects.create(
            codigo="ALTO001",
            descricao="Item Alto",
            unidade_medida="UN",
            valor_unitario=Decimal("25.00"),
            fornecedor=self.fornecedor,
            estoque_minimo=300,
            estoque_maximo=1000,
            quantidade_atual=1500  # Acima do máximo
        )
    
    def test_verifica_estoque_critico(self):
        """Testa verificação de estoque crítico"""
        self.assertTrue(self.item_critico.estoque_manager.verifica_estoque_critico())
        self.assertFalse(self.item_baixo.estoque_manager.verifica_estoque_critico())
        self.assertFalse(self.item_ok.estoque_manager.verifica_estoque_critico())
        self.assertFalse(self.item_alto.estoque_manager.verifica_estoque_critico())
    
    def test_verifica_estoque_baixo(self):
        """Testa verificação de estoque baixo"""
        self.assertTrue(self.item_critico.estoque_manager.verifica_estoque_baixo())
        self.assertTrue(self.item_baixo.estoque_manager.verifica_estoque_baixo())
        self.assertFalse(self.item_ok.estoque_manager.verifica_estoque_baixo())
        self.assertFalse(self.item_alto.estoque_manager.verifica_estoque_baixo())
    
    def test_verifica_estoque_alto(self):
        """Testa verificação de estoque alto"""
        self.assertFalse(self.item_critico.estoque_manager.verifica_estoque_alto())
        self.assertFalse(self.item_baixo.estoque_manager.verifica_estoque_alto())
        self.assertFalse(self.item_ok.estoque_manager.verifica_estoque_alto())
        self.assertTrue(self.item_alto.estoque_manager.verifica_estoque_alto())
    
    def test_get_percentual_estoque(self):
        """Testa cálculo de percentual do estoque"""
        # Item crítico: 100/300 = 33.33%
        self.assertAlmostEqual(
            self.item_critico.estoque_manager.get_percentual_estoque(), 
            33.33, 
            places=1
        )
        
        # Item baixo: 250/300 = 83.33%
        self.assertAlmostEqual(
            self.item_baixo.estoque_manager.get_percentual_estoque(), 
            83.33, 
            places=1
        )
        
        # Item OK: 500/300 = 166.67%
        self.assertAlmostEqual(
            self.item_ok.estoque_manager.get_percentual_estoque(), 
            166.67, 
            places=1
        )
    
    def test_get_status_estoque(self):
        """Testa obtenção do status completo do estoque"""
        # Status crítico
        status_critico = self.item_critico.estoque_manager.get_status_estoque()
        self.assertEqual(status_critico['status'], 'CRITICO')
        self.assertTrue(status_critico['requer_acao'])
        self.assertEqual(status_critico['quantidade_atual'], 100)
        
        # Status baixo
        status_baixo = self.item_baixo.estoque_manager.get_status_estoque()
        self.assertEqual(status_baixo['status'], 'BAIXO')
        self.assertTrue(status_baixo['requer_acao'])
        
        # Status OK
        status_ok = self.item_ok.estoque_manager.get_status_estoque()
        self.assertEqual(status_ok['status'], 'OK')
        self.assertFalse(status_ok['requer_acao'])
        
        # Status alto
        status_alto = self.item_alto.estoque_manager.get_status_estoque()
        self.assertEqual(status_alto['status'], 'ALTO')
        self.assertTrue(status_alto['requer_acao'])
    
    def test_requer_reposicao(self):
        """Testa verificação de necessidade de reposição"""
        self.assertTrue(self.item_critico.estoque_manager.requer_reposicao())
        self.assertTrue(self.item_baixo.estoque_manager.requer_reposicao())
        self.assertFalse(self.item_ok.estoque_manager.requer_reposicao())
        self.assertFalse(self.item_alto.estoque_manager.requer_reposicao())
    
    def test_calcular_quantidade_reposicao(self):
        """Testa cálculo da quantidade sugerida para reposição"""
        # Item crítico precisa de 900 unidades (1000 - 100)
        self.assertEqual(
            self.item_critico.estoque_manager.calcular_quantidade_reposicao(), 
            900
        )
        
        # Item baixo precisa de 750 unidades (1000 - 250)
        self.assertEqual(
            self.item_baixo.estoque_manager.calcular_quantidade_reposicao(), 
            750
        )
        
        # Item OK não precisa de reposição
        self.assertEqual(
            self.item_ok.estoque_manager.calcular_quantidade_reposicao(), 
            0
        )
        
        # Item alto não precisa de reposição
        self.assertEqual(
            self.item_alto.estoque_manager.calcular_quantidade_reposicao(), 
            0
        )
    
    def test_get_nivel_urgencia(self):
        """Testa obtenção do nível de urgência"""
        self.assertEqual(self.item_critico.estoque_manager.get_nivel_urgencia(), 3)
        self.assertEqual(self.item_baixo.estoque_manager.get_nivel_urgencia(), 2)
        self.assertEqual(self.item_ok.estoque_manager.get_nivel_urgencia(), 0)
        self.assertEqual(self.item_alto.estoque_manager.get_nivel_urgencia(), 1)
    
    def test_estoque_manager_property(self):
        """Testa a property estoque_manager do modelo Item"""
        manager = self.item_critico.estoque_manager
        self.assertIsInstance(manager, EstoqueManager)
        self.assertEqual(manager.item, self.item_critico)


class APIAlertasTestCase(TestCase):
    """Testes para as APIs de alertas de estoque"""
    
    def setUp(self):
        """Configura dados de teste e autenticação"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Adiciona permissões necessárias
        view_permission = Permission.objects.get(codename='view_item')
        self.user.user_permissions.add(view_permission)
        
        self.client.login(username='testuser', password='testpass123')
        
        self.fornecedor = Fornecedor.objects.create(
            nome="Fornecedor API",
            cnpj="98.765.432/0001-10"
        )
        
        # Cria itens de teste
        self.item_critico = Item.objects.create(
            codigo="API001",
            descricao="Item Teste Crítico",
            unidade_medida="UN",
            valor_unitario=Decimal("10.00"),
            fornecedor=self.fornecedor,
            estoque_minimo=300,
            estoque_maximo=1000,
            quantidade_atual=100
        )
        
        self.item_ok = Item.objects.create(
            codigo="API002",
            descricao="Item Teste OK",
            unidade_medida="UN",
            valor_unitario=Decimal("15.00"),
            fornecedor=self.fornecedor,
            estoque_minimo=300,
            estoque_maximo=1000,
            quantidade_atual=500
        )
    
    def test_api_alertas_estoque(self):
        """Testa endpoint de alertas gerais"""
        response = self.client.get(reverse('api_alertas_estoque'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('resumo', data)
        self.assertIn('alertas', data)
        self.assertIn('total_alertas', data['resumo'])
        self.assertGreater(data['resumo']['total_alertas'], 0)
    
    def test_api_status_item(self):
        """Testa endpoint de status de item específico"""
        response = self.client.get(
            reverse('api_status_item', kwargs={'item_id': self.item_critico.id})
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'CRITICO')
        self.assertEqual(data['item_id'], self.item_critico.id)
        self.assertTrue(data['requer_acao'])
    
    def test_api_itens_criticos(self):
        """Testa endpoint de itens críticos"""
        response = self.client.get(reverse('api_itens_criticos'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('total', data)
        self.assertIn('itens_criticos', data)
        self.assertGreater(data['total'], 0)
    
    def test_api_itens_reposicao(self):
        """Testa endpoint de itens que necessitam reposição"""
        response = self.client.get(reverse('api_itens_reposicao'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('total', data)
        self.assertIn('itens', data)
        self.assertGreater(data['total'], 0)
    
    def test_api_sem_autenticacao(self):
        """Testa que APIs requerem autenticação"""
        self.client.logout()
        response = self.client.get(reverse('api_alertas_estoque'))
        # Deve redirecionar para login (302) ou retornar 401/403
        self.assertIn(response.status_code, [302, 401, 403])
