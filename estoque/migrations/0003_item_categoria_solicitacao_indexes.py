from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0002_fornecedor_email_fornecedor_telefone_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Campo categoria em Item
        migrations.AddField(
            model_name='item',
            name='categoria',
            field=models.CharField(
                max_length=50,
                blank=True,
                null=True,
                help_text='Categoria ou tipo de material (ex.: Limpeza, Escritório, Equipamento).',
            ),
        ),

        # Modelo Solicitacao
        migrations.CreateModel(
            name='Solicitacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.IntegerField()),
                ('tipo', models.CharField(choices=[('CONSUMO', 'Consumo'), ('TEMPORARIA', 'Retirada Temporária')], max_length=20)),
                ('status', models.CharField(choices=[('PENDENTE', 'Pendente'), ('APROVADA', 'Aprovada'), ('ATENDIDA', 'Atendida'), ('CANCELADA', 'Cancelada')], default='PENDENTE', max_length=20)),
                ('data_solicitacao', models.DateTimeField(auto_now_add=True)),
                ('data_atendimento', models.DateTimeField(blank=True, null=True)),
                ('data_devolucao_prevista', models.DateField(blank=True, null=True)),
                ('observacao', models.TextField(blank=True, null=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='estoque.item')),
                ('solicitante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitacoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-data_solicitacao'],
            },
        ),

        # Indexes em Item
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['codigo'], name='estoque_ite_codigo_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['descricao'], name='estoque_ite_descric_idx'),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(fields=['categoria'], name='estoque_ite_categor_idx'),
        ),

        # Indexes em Movimentacao
        migrations.AddIndex(
            model_name='movimentacao',
            index=models.Index(fields=['item', 'data'], name='estoque_mov_item_data_idx'),
        ),
        migrations.AddIndex(
            model_name='movimentacao',
            index=models.Index(fields=['tipo', 'data'], name='estoque_mov_tipo_data_idx'),
        ),

        # Indexes em Solicitacao
        migrations.AddIndex(
            model_name='solicitacao',
            index=models.Index(fields=['item', 'status'], name='estoque_sol_item_status_idx'),
        ),
        migrations.AddIndex(
            model_name='solicitacao',
            index=models.Index(fields=['solicitante', 'status'], name='estoque_sol_solicit_status_idx'),
        ),
    ]
