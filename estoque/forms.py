from django import forms
from .models import Fornecedor, Item, Movimentacao

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'

class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['item', 'tipo', 'quantidade', 'data_devolucao_prevista']


# NOVO FORMULÁRIO DE FORNECEDOR
class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'contato', 'telefone', 'email']