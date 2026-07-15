from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comercial', '0005_alter_contrato_tipo_modelo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='email',
            field=models.EmailField(blank=True, max_length=120),
        ),
    ]
