from django.db import migrations, models


def normalize_documents(apps, schema_editor):
    Cliente = apps.get_model("comercial", "Cliente")
    for cliente in Cliente.objects.all().iterator():
        digits = "".join(character for character in cliente.documento if character.isdigit())
        cliente.documento = digits
        cliente.tipo_documento = "cnpj" if len(digits) == 14 else "cpf"
        cliente.save(update_fields=["documento", "tipo_documento"])


class Migration(migrations.Migration):

    dependencies = [
        ("comercial", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="cliente",
            old_name="cpf",
            new_name="documento",
        ),
        migrations.AddField(
            model_name="cliente",
            name="tipo_documento",
            field=models.CharField(
                choices=[("cpf", "CPF"), ("cnpj", "CNPJ")],
                default="cpf",
                max_length=4,
                verbose_name="Tipo de pessoa",
            ),
        ),
        migrations.RunPython(normalize_documents, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="cliente",
            name="documento",
            field=models.CharField(max_length=18, unique=True, verbose_name="CPF ou CNPJ"),
        ),
        migrations.RemoveField(
            model_name="produto",
            name="marca",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="medida",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="unidade_medida",
        ),
        migrations.AlterField(
            model_name="produto",
            name="litros",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Litros (opcional)"),
        ),
        migrations.DeleteModel(
            name="Marca",
        ),
        migrations.RemoveField(
            model_name="orcamento",
            name="status",
        ),
        migrations.AddField(
            model_name="contrato",
            name="data_evento",
            field=models.DateField(blank=True, null=True, verbose_name="Data do contrato/evento"),
        ),        migrations.AlterField(
            model_name="contrato",
            name="status",
            field=models.CharField(
                choices=[
                    ("rascunho", "Rascunho"),
                    ("aguardando_assinatura", "Aguardando assinatura"),
                    ("assinado", "Assinado / aguardando data"),
                    ("executado", "Executado"),
                    ("cancelado", "Cancelado"),
                ],
                default="rascunho",
                max_length=30,
            ),
        ),
        migrations.AlterModelOptions(
            name="contrato",
            options={"ordering": ["-data_evento", "-criado_em"]},
        ),
    ]
