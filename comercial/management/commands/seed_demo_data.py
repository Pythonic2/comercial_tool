from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from comercial.models import (
    Cliente,
    ConfiguracaoEmpresa,
    Contrato,
    Orcamento,
    OrcamentoProduto,
    OrcamentoServico,
    Produto,
    Servico,
)


class Command(BaseCommand):
    help = "Cria uma massa de demonstração para o fluxo comercial e dashboard."

    def handle(self, *args, **options):
        today = date.today()
        user = self._get_demo_user()
        ConfiguracaoEmpresa.objects.update_or_create(
            pk=1,
            defaults={
                "nome_empresa": "Dona do Chopp",
                "cnpj": "12345678000190",
                "telefone": "(11) 99999-2026",
                "email": "comercial@donadochopp.example",
                "endereco": "Rua das Festas, 120",
            },
        )

        produtos = self._create_produtos()
        servicos = self._create_servicos()
        clientes = self._create_clientes()
        orcamentos = self._create_orcamentos(today, user, clientes, produtos, servicos)
        self._create_contratos(today, user, clientes, orcamentos)

        self.stdout.write(self.style.SUCCESS("Massa de demonstração criada com sucesso."))

    def _get_demo_user(self):
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()
        if user:
            return user
        user, _ = User.objects.get_or_create(
            username="demo",
            defaults={
                "email": "demo@donadochopp.example",
                "first_name": "Funcionário",
                "last_name": "Demo",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.set_password("demo1234")
        user.save()
        return user

    def _create_produtos(self):
        dados = [
            ("Barril Chopp Pilsen 30L", 30, "360.00", 14),
            ("Barril Chopp Pilsen 50L", 50, "540.00", 9),
            ("Barril Chopp IPA 30L", 30, "480.00", 6),
            ("Chopeira elétrica", None, "180.00", 12),
            ("Copo descartável", None, "38.00", 32),
        ]
        produtos = {}
        for nome, litros, valor, estoque in dados:
            produto, _ = Produto.objects.update_or_create(
                nome=nome,
                defaults={
                    "litros": litros,
                    "valor": Decimal(valor),
                    "estoque_quantidade": estoque,
                    "disponivel": estoque > 0,
                    "descricao": "Item demonstrativo.",
                },
            )
            produtos[nome] = produto
        return produtos

    def _create_servicos(self):
        dados = [
            ("Entrega e retirada", "90.00"),
            ("Instalação da chopeira", "130.00"),
            ("Operador de chopp", "280.00"),
        ]
        servicos = {}
        for nome, valor in dados:
            servico, _ = Servico.objects.update_or_create(
                nome=nome,
                defaults={
                    "valor": Decimal(valor),
                    "descricao": "Serviço demonstrativo.",
                    "ativo": True,
                },
            )
            servicos[nome] = servico
        return servicos

    def _create_clientes(self):
        dados = [
            ("Mariana Alves", "cpf", "11122233301"),
            ("Empresa Exemplo Ltda", "cnpj", "12345678000190"),
            ("Bruno Martins", "cpf", "11122233302"),
        ]
        clientes = []
        for index, (nome, tipo, documento) in enumerate(dados, start=1):
            cliente, _ = Cliente.objects.update_or_create(
                documento=documento,
                defaults={
                    "nome_completo": nome,
                    "tipo_documento": tipo,
                    "email": f"cliente{index}@example.com",
                    "endereco_residencial": f"Rua Exemplo, {index * 10}",
                    "celular": f"(11) 98888-100{index}",
                },
            )
            clientes.append(cliente)
        return clientes

    def _create_orcamentos(self, today, user, clientes, produtos, servicos):
        specs = [
            (clientes[0], "pix", produtos["Barril Chopp Pilsen 50L"], "2", servicos["Entrega e retirada"]),
            (clientes[1], "cartao", produtos["Barril Chopp IPA 30L"], "3", servicos["Operador de chopp"]),
            (clientes[2], "pix", produtos["Barril Chopp Pilsen 30L"], "1", servicos["Instalação da chopeira"]),
        ]
        orcamentos = []
        for index, (cliente, pagamento, produto, quantidade, servico) in enumerate(specs, start=1):
            orcamento, _ = Orcamento.objects.update_or_create(
                cliente=cliente,
                observacoes=f"Orçamento demonstrativo #{index}",
                defaults={
                    "usuario": user,
                    "validade": today + timedelta(days=10),
                    "forma_pagamento": pagamento,
                    "desconto": Decimal("0"),
                },
            )
            OrcamentoProduto.objects.filter(orcamento=orcamento).delete()
            OrcamentoServico.objects.filter(orcamento=orcamento).delete()
            OrcamentoProduto.objects.create(
                orcamento=orcamento,
                produto=produto,
                quantidade=Decimal(quantidade),
                valor_unitario=produto.valor,
            )
            OrcamentoServico.objects.create(
                orcamento=orcamento,
                servico=servico,
                quantidade=Decimal("1"),
                valor_unitario=servico.valor,
            )
            orcamentos.append(orcamento)
        return orcamentos

    def _create_contratos(self, today, user, clientes, orcamentos):
        modelo_path = self._ensure_modelo_contrato()
        specs = [
            ("Contrato executado", clientes[0], orcamentos[0], "executado", today - timedelta(days=5)),
            ("Contrato futuro", clientes[1], orcamentos[1], "assinado", today + timedelta(days=12)),
            ("Contrato cancelado", clientes[2], orcamentos[2], "cancelado", today + timedelta(days=20)),
        ]
        for titulo, cliente, orcamento, status, data_evento in specs:
            Contrato.objects.update_or_create(
                titulo=titulo,
                defaults={
                    "cliente": cliente,
                    "usuario": user,
                    "orcamento": orcamento,
                    "status": status,
                    "data_evento": data_evento,
                    "documento_modelo": str(modelo_path.relative_to(settings.MEDIA_ROOT)),
                    "placeholders": ["nome_cliente", "documento", "valor_total"],
                    "valores_preenchidos": {
                        "nome_cliente": cliente.nome_completo,
                        "documento": cliente.documento_formatado,
                        "valor_total": f"{orcamento.valor_total:.2f}",
                    },
                },
            )

    def _ensure_modelo_contrato(self):
        modelo_dir = Path(settings.MEDIA_ROOT) / "documentos" / "modelos"
        modelo_dir.mkdir(parents=True, exist_ok=True)
        modelo_path = modelo_dir / "contrato_modelo_demo.txt"
        if not modelo_path.exists():
            modelo_path.write_text(
                "Contrato para {{nome_cliente}}, documento {{documento}}, "
                "no valor de R$ {{valor_total}}.",
                encoding="utf-8",
            )
        return modelo_path
