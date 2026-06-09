# Generated migration for CompanyEmployee and Orcamento updates

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comercial', '0002_multi_tenant'),
    ]

    operations = [
        # Create CompanyEmployee
        migrations.CreateModel(
            name='CompanyEmployee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('role', models.CharField(choices=[('owner', 'Proprietário'), ('manager', 'Gerente'), ('employee', 'Funcionário')], default='employee', max_length=20)),
                ('ativo', models.BooleanField(default=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='comercial.companyprofile')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company_employees', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-criado_em'],
            },
        ),
        
        # Add unique_together to CompanyEmployee
        migrations.AlterUniqueTogether(
            name='companyemployee',
            unique_together={('company', 'user')},
        ),
        
        # Add fields to Orcamento
        migrations.AddField(
            model_name='orcamento',
            name='criado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orcamentos_criados', to='comercial.companyemployee'),
        ),
        
        migrations.AddField(
            model_name='orcamento',
            name='link_pubico',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        
        migrations.AddField(
            model_name='orcamento',
            name='enviado_em',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
