from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comercial", "0002_commercial_redesign"),
    ]

    operations = [
        migrations.AddField(
            model_name="produto",
            name="imagem",
            field=models.ImageField(blank=True, null=True, upload_to="produtos/"),
        ),
        migrations.AddField(
            model_name="servico",
            name="imagem",
            field=models.ImageField(blank=True, null=True, upload_to="servicos/"),
        ),
    ]
