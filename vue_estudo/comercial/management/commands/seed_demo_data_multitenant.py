"""
Exemplo de dados para testes e demonstração.

Este comando popula o banco com uma empresa de exemplo, clientes, produtos e serviços.

Uso:
    python manage.py seed_demo_data_multitenant

Ou importar as funções diretamente:
    from comercial.management.commands.seed_demo_data_multitenant import create_demo_company
    create_demo_company()
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from comercial.models import (
    CompanyProfile, Subscription, Cliente, Marca, Produto, 
    ProductImage, Servico, Orcamento, OrcamentoProduto, OrcamentoServico
)
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Popula banco com dados de demonstração multi-tenant'

    def handle(self, *args, **options):
        self.stdout.write("Criando dados de demonstração...")
        
        # Criar usuário de teste
        user, created = User.objects.get_or_create(
            username='donadochopp',
            defaults={
                'email': 'donadochopp@gmail.com',
                'first_name': 'Dona',
                'last_name': 'do Chopp',
            }
        )
        
        if created:
            user.set_password('senha123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f"✓ Usuário criado: {user.username}"))
        else:
            self.stdout.write(f"ℹ Usuário já existe: {user.username}")
        
        # Criar/atualizar CompanyProfile
        empresa, created = CompanyProfile.objects.get_or_create(
            owner=user,
            defaults={
                'nome_empresa': 'Dona do Chopp Ltda',
                'cnpj': '44919343000120',
                'telefone': '85981423909',
                'email': 'donadochopp@gmail.com',
                'endereco': 'Rua Goiás - Panamericano, 60441-005 - Fortaleza/CE',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Empresa criada: {empresa.nome_empresa}"))
        else:
            self.stdout.write(f"ℹ Empresa já existe: {empresa.nome_empresa}")
        
        # Criar Subscription (deve ser automático pelo signal)
        subscription, created = Subscription.objects.get_or_create(
            company=empresa,
            defaults={
                'pago': True,
                'valor_mensalidade': Decimal('99.90'),
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS("✓ Assinatura criada (pago=True)"))
        
        # Criar Marca
        marca, created = Marca.objects.get_or_create(
            company=empresa,
            nome='Brahma',
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Marca criada: {marca.nome}"))
        
        # Criar Produtos
        produtos_data = [
            {
                'nome': '300 litros Brahma ou Heineken',
                'valor': Decimal('5194.00'),
                'unidade_medida': 'lt',
                'descricao': 'Item principal do orçamento demonstrativo do PDF.',
                'estoque_quantidade': 10,
            },
            {
                'nome': '2 Balcões',
                'valor': Decimal('0.00'),
                'unidade_medida': 'un',
                'descricao': 'Balcões de brinde para evento.',
                'estoque_quantidade': 5,
            },
        ]
        
        for prod_data in produtos_data:
            produto, created = Produto.objects.get_or_create(
                company=empresa,
                nome=prod_data['nome'],
                defaults={
                    'marca': marca,
                    'valor': prod_data['valor'],
                    'unidade_medida': prod_data['unidade_medida'],
                    'descricao': prod_data['descricao'],
                    'estoque_quantidade': prod_data['estoque_quantidade'],
                    'disponivel': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Produto: {produto.nome}"))
        
        # Criar Serviços
        servicos_data = [
            {
                'nome': '2 Profissionais durante 4h',
                'valor': Decimal('260.00'),
                'descricao': 'Linha de serviço exibida no orçamento do PDF.',
            },
            {
                'nome': 'Frete e instalação',
                'valor': Decimal('150.00'),
                'descricao': 'Serviço complementar para logística e montagem.',
            },
            {
                'nome': 'Copos descartáveis',
                'valor': Decimal('50.00'),
                'descricao': 'Item de apoio citado nas observações do PDF.',
            },
        ]
        
        for serv_data in servicos_data:
            servico, created = Servico.objects.get_or_create(
                company=empresa,
                nome=serv_data['nome'],
                defaults={
                    'valor': serv_data['valor'],
                    'descricao': serv_data['descricao'],
                    'ativo': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Serviço: {servico.nome}"))
        
        # Criar Clientes
        clientes_data = [
            {
                'nome_completo': 'E-Brasil Mkt',
                'cpf': '15.235.934/0001-80',
                'email': 'contato@ebrasil.com',
                'endereco_residencial': 'Rua Luís Braille - Monte Castelo, 79010-080 - Campo Grande/MS',
                'celular': '67987654321',
            },
            {
                'nome_completo': 'João Silva',
                'cpf': '12345678901',
                'email': 'joao@example.com',
                'endereco_residencial': 'Rua das Flores, 123',
                'celular': '85988881111',
            },
            {
                'nome_completo': 'Maria Santos',
                'cpf': '98765432109',
                'email': 'maria@example.com',
                'endereco_residencial': 'Avenida Principal, 456',
                'celular': '85999992222',
            },
        ]
        
        clientes_criados = []
        for cli_data in clientes_data:
            cliente, created = Cliente.objects.get_or_create(
                company=empresa,
                cpf=cli_data['cpf'],
                defaults={
                    'nome_completo': cli_data['nome_completo'],
                    'email': cli_data['email'],
                    'endereco_residencial': cli_data['endereco_residencial'],
                    'celular': cli_data['celular'],
                }
            )
            clientes_criados.append(cliente)
            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Cliente: {cliente.nome_completo}"))
        
        # Criar Orçamento de exemplo
        if clientes_criados:
            cliente = clientes_criados[0]
            orcamento, created = Orcamento.objects.get_or_create(
                company=empresa,
                cliente=cliente,
                usuario=user,
                status='rascunho',
                defaults={
                    'validade': date.today() + timedelta(days=30),
                    'forma_pagamento': 'pix',
                    'observacoes': 'Orçamento de exemplo para demonstração',
                    'desconto': Decimal('0.00'),
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ Orçamento criado: #{orcamento.pk}"))
                
                # Adicionar itens ao orçamento
                produtos = Produto.objects.filter(company=empresa)[:2]
                for idx, produto in enumerate(produtos, 1):
                    OrcamentoProduto.objects.get_or_create(
                        orcamento=orcamento,
                        produto=produto,
                        defaults={
                            'quantidade': Decimal('1'),
                            'valor_unitario': produto.valor,
                        }
                    )
                    self.stdout.write(f"    ✓ Item adicionado: {produto.nome}")
                
                # Adicionar serviço
                servicos = Servico.objects.filter(company=empresa)[:1]
                for servico in servicos:
                    OrcamentoServico.objects.get_or_create(
                        orcamento=orcamento,
                        servico=servico,
                        defaults={
                            'quantidade': Decimal('1'),
                            'valor_unitario': servico.valor,
                        }
                    )
                    self.stdout.write(f"    ✓ Serviço adicionado: {servico.nome}")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Dados de demonstração criados com sucesso!"))
        self.stdout.write(f"\nCredenciais de acesso:")
        self.stdout.write(f"  Usuário: donadochopp")
        self.stdout.write(f"  Senha: senha123")
        self.stdout.write(f"  Empresa: {empresa.nome_empresa}")
        self.stdout.write(f"  Email: {empresa.email}")


def create_demo_company(user=None):
    """Helper para criar empresa de demo programaticamente"""
    if not user:
        user, _ = User.objects.get_or_create(
            username='demo',
            defaults={'email': 'demo@example.com'}
        )
        if not user.has_usable_password():
            user.set_password('demo123')
            user.save()
    
    empresa = CompanyProfile.objects.create(
        owner=user,
        nome_empresa='Demo Company',
    )
    
    return empresa
