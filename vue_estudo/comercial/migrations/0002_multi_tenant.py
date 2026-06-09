# Generated migration for multi-tenant setup

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comercial', '0001_initial'),
    ]

    operations = [
        # Create CompanyProfile
        migrations.CreateModel(
            name='CompanyProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('nome_empresa', models.CharField(max_length=120)),
                ('cnpj', models.CharField(blank=True, max_length=20)),
                ('telefone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('endereco', models.CharField(blank=True, max_length=255)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='logos/')),
                ('owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='company_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['nome_empresa'],
            },
        ),
        
        # Create ProductImage
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('imagem', models.ImageField(upload_to='produtos/')),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('descricao', models.CharField(blank=True, max_length=255)),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_images', to='comercial.produto')),
            ],
            options={
                'ordering': ['ordem', 'criado_em'],
            },
        ),
        
        # Create Subscription
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('pago', models.BooleanField(default=True)),
                ('data_pagamento', models.DateTimeField(auto_now_add=True)),
                ('proximo_pagamento', models.DateTimeField(blank=True, null=True)),
                ('valor_mensalidade', models.DecimalField(decimal_places=2, default='0.00', max_digits=10)),
                ('company', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='comercial.companyprofile')),
            ],
            options={
                'ordering': ['-data_pagamento'],
            },
        ),
        
        # Add company field to Marca
        migrations.AddField(
            model_name='marca',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='marcas', to='comercial.companyprofile'),
        ),
        
        # Add company field to Produto
        migrations.AddField(
            model_name='produto',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='produtos', to='comercial.companyprofile'),
        ),
        
        # Update Produto unique_together
        migrations.AlterUniqueTogether(
            name='marca',
            unique_together={('company', 'nome')},
        ),
        
        # Add company field to Servico
        migrations.AddField(
            model_name='servico',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='servicos', to='comercial.companyprofile'),
        ),
        
        # Add company field to Cliente
        migrations.AddField(
            model_name='cliente',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='clientes', to='comercial.companyprofile'),
        ),
        
        # Update Cliente constraints
        migrations.AlterUniqueTogether(
            name='cliente',
            unique_together={('company', 'cpf')},
        ),
        migrations.AlterField(
            model_name='cliente',
            name='cpf',
            field=models.CharField(blank=True, max_length=14),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='email',
            field=models.EmailField(blank=True, max_length=120),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='endereco_residencial',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='celular',
            field=models.CharField(blank=True, max_length=20),
        ),
        
        # Add company field to Orcamento
        migrations.AddField(
            model_name='orcamento',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orcamentos', to='comercial.companyprofile'),
        ),
        
        # Add company field to Contrato
        migrations.AddField(
            model_name='contrato',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contratos', to='comercial.companyprofile'),
        ),
        
        # Add company field to Evento
        migrations.AddField(
            model_name='evento',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='eventos', to='comercial.companyprofile'),
        ),
    ]
