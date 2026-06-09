from datetime import date, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from comercial.models import (
    Cliente,
    ConfiguracaoEmpresa,
    Contrato,
    Evento,
    EventoProduto,
    EventoServico,
    Marca,
    Orcamento,
    OrcamentoProduto,
    OrcamentoServico,
    Produto,
    Servico,
)


class Command(BaseCommand):
    help = "Cria uma massa de dados ficticia para demonstracao do comercial e dashboard."

    def handle(self, *args, **options):
        today = date.today()
        user = self._get_demo_user()

        ConfiguracaoEmpresa.objects.update_or_create(
            pk=1,
            defaults={
                "nome_empresa": "Dona do Chopp",
                "cnpj": "12.345.678/0001-90",
                "telefone": "(11) 99999-2026",
                "email": "comercial@donadochopp.example",
                "endereco": "Rua das Festas, 120 - Sao Paulo/SP",
                "texto_padrao_orcamento": (
                    "Segue orcamento solicitado para {{nome_cliente}} com produtos "
                    "{{produtos}} e servicos {{servicos}}."
                ),
            },
        )

        marcas = self._create_marcas()
        produtos = self._create_produtos(marcas)
        servicos = self._create_servicos()
        clientes = self._create_clientes()
        orcamentos = self._create_orcamentos(today, user, clientes, produtos, servicos)
        contratos = self._create_contratos(today, user, clientes, orcamentos)
        self._create_eventos(today, clientes, contratos, produtos, servicos)

        self.stdout.write(self.style.SUCCESS("Massa ficticia criada/atualizada com sucesso."))
        self.stdout.write(
            f"Clientes: {Cliente.objects.count()} | Produtos: {Produto.objects.count()} | "
            f"Orcamentos: {Orcamento.objects.count()} | Eventos: {Evento.objects.count()}"
        )

    def _get_demo_user(self):
        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()
        if user:
            return user
        user, _ = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@donadochopp.example", "is_staff": True, "is_superuser": True},
        )
        user.set_password("demo1234")
        user.save()
        return user

    def _create_marcas(self):
        nomes = ["Dona do Chopp", "Brahma", "Heineken", "Stella Artois", "Colorado"]
        return {nome: Marca.objects.update_or_create(nome=nome)[0] for nome in nomes}

    def _create_produtos(self, marcas):
        dados = [
            ("300 litros Brahma ou Heineken", "Dona do Chopp", "lt", 300, "300 litros", "5194.00", 10),
            ("2 Balcões", "Dona do Chopp", "un", None, "Brinde para evento", "0.00", 5),
        ]
        produtos = {}
        for nome, marca, unidade, litros, medida, valor, estoque in dados:
            produto, _ = Produto.objects.update_or_create(
                nome=nome,
                defaults={
                    "marca": marcas[marca],
                    "unidade_medida": unidade,
                    "litros": litros,
                    "medida": medida,
                    "valor": Decimal(valor),
                    "estoque_quantidade": estoque,
                    "disponivel": estoque > 0,
                    "descricao": "Item ficticio para demonstracao comercial.",
                },
            )
            produtos[nome] = produto
        return produtos

    def _create_servicos(self):
        dados = [
            ("2 Profissionais durante 4h", "260.00", "Instalação e atendimento durante 4 horas com 2 profissionais."),
            ("Frete e instalação", "150.00", "Frete, montagem e suporte inicial."),
            ("Copos descartáveis", "50.00", "Copos descartáveis para apoio ao evento."),
        ]
        servicos = {}
        for nome, valor, descricao in dados:
            servico, _ = Servico.objects.update_or_create(
                nome=nome,
                defaults={"valor": Decimal(valor), "descricao": descricao, "ativo": True},
            )
            servicos[nome] = servico
        return servicos

    def _create_clientes(self):
        dados = [
            ("Mariana Alves", "111.222.333-01", "mariana.alves@example.com", "Rua das Acacias, 45", "(11) 98888-1001"),
            ("Bruno Martins", "111.222.333-02", "bruno.martins@example.com", "Av. Paulista, 900", "(11) 98888-1002"),
            ("Camila Rocha", "111.222.333-03", "camila.rocha@example.com", "Rua Augusta, 1450", "(11) 98888-1003"),
            ("Felipe Santos", "111.222.333-04", "felipe.santos@example.com", "Rua Vergueiro, 2020", "(11) 98888-1004"),
            ("Renata Lima", "111.222.333-05", "renata.lima@example.com", "Alameda Santos, 310", "(11) 98888-1005"),
            ("Thiago Costa", "111.222.333-06", "thiago.costa@example.com", "Rua Harmonia, 88", "(11) 98888-1006"),
            ("Juliana Nunes", "111.222.333-07", "juliana.nunes@example.com", "Rua Fidalga, 71", "(11) 98888-1007"),
            ("Rafael Pereira", "111.222.333-08", "rafael.pereira@example.com", "Av. Pompeia, 510", "(11) 98888-1008"),
        ]
        clientes = []
        for nome, cpf, email, endereco, celular in dados:
            cliente, _ = Cliente.objects.update_or_create(
                cpf=cpf,
                defaults={
                    "nome_completo": nome,
                    "email": email,
                    "endereco_residencial": endereco,
                    "celular": celular,
                },
            )
            clientes.append(cliente)
        return clientes

    def _create_orcamentos(self, today, user, clientes, produtos, servicos):
        specs = [
            (0, "executado", clientes[0], "pix", "0.00", [("Barril Chopp Pilsen 50L", "2"), ("Chopeira eletrica 1 torneira", "1")], [("Entrega e retirada", "1"), ("Instalacao da chopeira", "1")]),
            (-3, "aprovado", clientes[1], "cartao", "40.00", [("Barril Chopp Lager 50L", "1"), ("Copo descartavel 300ml pct 100", "3")], [("Entrega e retirada", "1")]),
            (-8, "enviado", clientes[2], "pix", "0.00", [("Barril Chopp IPA 30L", "2"), ("Chopeira bomba manual", "1")], [("Instalacao da chopeira", "1"), ("Kit gelo e conservacao", "1")]),
            (-16, "executado", clientes[3], "dinheiro", "75.00", [("Barril Stella 30L", "2")], [("Operador de chopp", "1"), ("Entrega e retirada", "1")]),
            (-34, "cancelado", clientes[4], "boleto", "0.00", [("Barril Chopp Pilsen 30L", "1")], [("Entrega e retirada", "1")]),
            (-62, "executado", clientes[5], "pix", "120.00", [("Barril Chopp Pilsen 50L", "3"), ("Chopeira eletrica 1 torneira", "1")], [("Operador de chopp", "1"), ("Limpeza pos-evento", "1")]),
            (-95, "rascunho", clientes[6], "pix", "0.00", [("Barril Chopp IPA 30L", "1")], [("Kit gelo e conservacao", "1")]),
            (-150, "executado", clientes[7], "cartao", "150.00", [("Barril Chopp Lager 50L", "2"), ("Copo descartavel 300ml pct 100", "2")], [("Entrega e retirada", "1"), ("Operador de chopp", "1")]),
            (-220, "executado", clientes[0], "pix", "80.00", [("Barril Chopp Pilsen 30L", "2")], [("Instalacao da chopeira", "1")]),
            (-330, "aprovado", clientes[2], "boleto", "0.00", [("Barril Stella 30L", "1"), ("Chopeira bomba manual", "1")], [("Entrega e retirada", "1")]),
        ]
        orcamentos = []
        for index, (offset, status, cliente, pagamento, desconto, itens_produto, itens_servico) in enumerate(specs, start=1):
            orcamento, _ = Orcamento.objects.update_or_create(
                cliente=cliente,
                observacoes=f"Orcamento demonstrativo #{index}",
                defaults={
                    "usuario": user,
                    "status": status,
                    "validade": today + timedelta(days=10),
                    "forma_pagamento": pagamento,
                    "desconto": Decimal(desconto),
                },
            )
            OrcamentoProduto.objects.filter(orcamento=orcamento).delete()
            OrcamentoServico.objects.filter(orcamento=orcamento).delete()
            for produto_nome, quantidade in itens_produto:
                produto = produtos[produto_nome]
                OrcamentoProduto.objects.create(
                    orcamento=orcamento,
                    produto=produto,
                    quantidade=Decimal(quantidade),
                    valor_unitario=produto.valor,
                )
            for servico_nome, quantidade in itens_servico:
                servico = servicos[servico_nome]
                OrcamentoServico.objects.create(
                    orcamento=orcamento,
                    servico=servico,
                    quantidade=Decimal(quantidade),
                    valor_unitario=servico.valor,
                )
            created_at = timezone.now() + timedelta(days=offset)
            Orcamento.objects.filter(pk=orcamento.pk).update(criado_em=created_at, atualizado_em=created_at)
            orcamentos.append(orcamento)
        return orcamentos

    def _create_contratos(self, today, user, clientes, orcamentos):
        modelo_path = self._ensure_modelo_contrato()
        specs = [
            (clientes[0], orcamentos[0], "Contrato festa Mariana", "executado", -1),
            (clientes[1], orcamentos[1], "Contrato confraternizacao Bruno", "assinado", None),
            (clientes[3], orcamentos[3], "Contrato aniversario Felipe", "executado", -14),
            (clientes[5], orcamentos[5], "Contrato evento corporativo Thiago", "aguardando_assinatura", None),
            (clientes[7], orcamentos[7], "Contrato casamento Rafael", "assinado", None),
        ]
        contratos = []
        for cliente, orcamento, titulo, status, assinatura_offset in specs:
            assinatura = today + timedelta(days=assinatura_offset) if assinatura_offset else None
            contrato, _ = Contrato.objects.update_or_create(
                titulo=titulo,
                defaults={
                    "cliente": cliente,
                    "usuario": user,
                    "orcamento": orcamento,
                    "status": status,
                    "documento_modelo": str(modelo_path.relative_to(settings.MEDIA_ROOT)),
                    "placeholders": ["nome_cliente", "cpf", "produto", "valor_total"],
                    "valores_preenchidos": {
                        "nome_cliente": cliente.nome_completo,
                        "cpf": cliente.cpf,
                        "produto": "Chopp para evento",
                        "valor_total": f"{orcamento.valor_total:.2f}",
                    },
                    "data_assinatura_cliente": assinatura,
                    "data_assinatura_usuario": assinatura,
                    "observacoes": "Contrato ficticio para demonstracao.",
                },
            )
            contratos.append(contrato)
        return contratos

    def _ensure_modelo_contrato(self):
        modelo_dir = Path(settings.MEDIA_ROOT) / "documentos" / "modelos"
        modelo_dir.mkdir(parents=True, exist_ok=True)
        modelo_path = modelo_dir / "contrato_modelo_demo.txt"
        if not modelo_path.exists():
            modelo_path.write_text(
                "Contrato de locacao para {{nome_cliente}}, CPF {{cpf}}, "
                "referente a {{produto}} no valor de R$ {{valor_total}}.",
                encoding="utf-8",
            )
        return modelo_path

    def _create_eventos(self, today, clientes, contratos, produtos, servicos):
        specs = [
            (-2, clientes[0], contratos[0], "Aniversario", "completo", "choppeira_eletrica", True, "19:00", "1440.00", [("Barril Chopp Pilsen 50L", 2)], [("Operador de chopp", 1)]),
            (2, clientes[1], contratos[1], "Confraternizacao", "pendente", "choppeira_eletrica", False, "18:30", "1284.00", [("Barril Chopp Lager 50L", 1)], [("Entrega e retirada", 1)]),
            (7, clientes[2], None, "Open house", "pendente", "choppeira_bomba", False, "17:00", "1155.00", [("Barril Chopp IPA 30L", 2)], [("Kit gelo e conservacao", 1)]),
            (-12, clientes[3], contratos[2], "Churrasco", "completo", "choppeira_eletrica", True, "13:00", "1315.00", [("Barril Stella 30L", 2)], [("Entrega e retirada", 1)]),
            (18, clientes[4], None, "Evento corporativo", "pendente", "choppeira_eletrica", True, "20:00", "980.00", [("Barril Chopp Pilsen 30L", 1)], [("Operador de chopp", 1)]),
            (-36, clientes[5], contratos[3], "Feira gastronomica", "completo", "choppeira_eletrica", True, "16:00", "2010.00", [("Barril Chopp Pilsen 50L", 3)], [("Limpeza pos-evento", 1)]),
            (45, clientes[6], None, "Casamento civil", "pendente", "choppeira_bomba", False, "19:30", "555.00", [("Barril Chopp IPA 30L", 1)], [("Kit gelo e conservacao", 1)]),
            (-84, clientes[7], contratos[4], "Casamento", "completo", "choppeira_eletrica", True, "21:00", "1896.00", [("Barril Chopp Lager 50L", 2)], [("Operador de chopp", 1)]),
            (-160, clientes[0], None, "Festa junina", "cancelado", "choppeira_bomba", False, "15:00", "640.00", [("Barril Chopp Pilsen 30L", 1)], [("Entrega e retirada", 1)]),
            (-250, clientes[2], None, "Inauguracao", "completo", "choppeira_eletrica", True, "18:00", "720.00", [("Barril Stella 30L", 1)], [("Instalacao da chopeira", 1)]),
        ]
        for offset, cliente, contrato, tipo, status, bomba, profissional, hora_texto, valor, itens_produto, itens_servico in specs:
            evento, _ = Evento.objects.update_or_create(
                cliente=cliente,
                tipo_evento=tipo,
                data=today + timedelta(days=offset),
                defaults={
                    "contrato": contrato,
                    "endereco_evento": cliente.endereco_residencial,
                    "status": status,
                    "bomba_opcao": bomba,
                    "profissional": profissional,
                    "hora": time.fromisoformat(hora_texto),
                    "valor_total": Decimal(valor),
                    "forma_pagamento": "pix",
                    "observacoes": "Evento ficticio para acompanhar no dashboard.",
                },
            )
            EventoProduto.objects.filter(evento=evento).delete()
            EventoServico.objects.filter(evento=evento).delete()
            for produto_nome, quantidade in itens_produto:
                EventoProduto.objects.create(evento=evento, produto=produtos[produto_nome], quantidade=quantidade)
            for servico_nome, quantidade in itens_servico:
                EventoServico.objects.create(evento=evento, servico=servicos[servico_nome], quantidade=quantidade)
