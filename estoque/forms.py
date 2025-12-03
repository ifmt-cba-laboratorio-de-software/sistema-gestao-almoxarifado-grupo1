from django import forms
from django.core.exceptions import ValidationError

from .models import Fornecedor, Item, Movimentacao, Solicitacao


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'


class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['item', 'tipo', 'quantidade', 'data_devolucao_prevista']

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        data_dev = cleaned_data.get('data_devolucao_prevista')

        if tipo == 'RETIRADA' and not data_dev:
            raise ValidationError(
                "Para retiradas temporárias é obrigatório informar a data prevista de devolução."
            )

        return cleaned_data


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'contato', 'telefone', 'email']


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = [
            'item',
            'quantidade',
            'tipo',
            'data_devolucao_prevista',
            'observacao',
        ]

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        data_dev = cleaned_data.get('data_devolucao_prevista')

        if tipo == 'TEMPORARIA' and not data_dev:
            raise ValidationError(
                "Para solicitações temporárias é obrigatório informar a data prevista de devolução."
            )

        return cleaned_data
