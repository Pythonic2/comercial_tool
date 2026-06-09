"""
comercial/views_orcamento_novo.py

Views reformuladas para o novo fluxo de criação de orçamento.
Use este código como referência para atualizar comercial/views.py
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_http_methods
import secrets
from decimal import Decimal
from datetime import timedelta

from .models import (
    Cliente, Orcamento, OrcamentoProduto, OrcamentoServico,
    Produto, Serviço, CompanyProfile, CompanyEmployee
)
from .forms import ClienteForm
from .decorators import require_company_access


# ============================================================================
# ETAPA 1: SELEÇÃO/CRIAÇÃO DE CLIENTE
# ============================================================================

@login_required
@require_company_access
def orcamento_novo_etapa1(request, company_id=None):
    """
    Etapa 1: Selecionar cliente existente ou criar novo
    Armazena dados em session para próximas etapas
    """
    
    # Obter empresa
    if company_id:
        company = get_object_or_404(CompanyProfile, id=company_id)
    else:
        company = request.user.company_profile
    
    # Verificar acesso
    if not usuario_pode_criar_orcamento(request.user, company):
        messages.error(request, "Você não tem permissão para criar orçamentos")
        return redirect('home')
    
    if request.method == 'POST':
        opcao = request.POST.get('opcao_cliente')
        
        if opcao == 'existente':
            cliente_id = request.POST.get('cliente_id')
            try:
                cliente = Cliente.objects.get(id=cliente_id, company=company)
                # Salvar em session
                request.session['orcamento_data'] = {
                    'etapa_atual': 1,
                    'cliente_id': cliente.id,
                    'cliente_nome': cliente.nome_completo,
                }
                return redirect('orcamento_novo_etapa2')
            except Cliente.DoesNotExist:
                messages.error(request, "Cliente não encontrado")
        
        elif opcao == 'novo':
            nome = request.POST.get('novo_cliente_nome')
            email = request.POST.get('novo_cliente_email', '')
            telefone = request.POST.get('novo_cliente_telefone', '')
            
            if not nome:
                messages.error(request, "Nome do cliente é obrigatório")
            else:
                # Criar novo cliente
                cliente = Cliente.objects.create(
                    company=company,
                    nome_completo=nome,
                    email=email,
                    celular=telefone
                )
                request.session['orcamento_data'] = {
                    'etapa_atual': 1,
                    'cliente_id': cliente.id,
                    'cliente_nome': cliente.nome_completo,
                }
                messages.success(request, f"Cliente '{nome}' criado com sucesso!")
                return redirect('orcamento_novo_etapa2')
    
    # GET - mostrar formulário
    clientes = Cliente.objects.filter(company=company).order_by('nome_completo')
    
    context = {
        'company': company,
        'clientes': clientes,
        'etapa': 1,
    }
    
    return render(request, 'comercial/orcamentos/wizard.html', context)


# ============================================================================
# ETAPA 2: SELEÇÃO DE ITENS (PRODUTOS/SERVIÇOS)
# ============================================================================

@login_required
@require_company_access
def orcamento_novo_etapa2(request, company_id=None):
    """
    Etapa 2: Adicionar múltiplos produtos/serviços
    
    AJAX endpoints:
    - GET ?action=list_produtos -> JSON com todos os produtos
    - POST com items -> Valida e salva em session
    """
    
    # Validar que veio da etapa 1
    orcamento_data = request.session.get('orcamento_data')
    if not orcamento_data or orcamento_data.get('etapa_atual') != 1:
        messages.error(request, "Você deve começar pela Etapa 1")
        return redirect('orcamento_novo_etapa1')
    
    company = get_object_or_404(CompanyProfile, id=company_id) if company_id else request.user.company_profile
    
    if request.method == 'POST':
        # Validar itens enviados
        items = request.POST.getlist('item_id')  # Lista de IDs
        quantities = request.POST.getlist('quantidade')
        values = request.POST.getlist('valor_unitario')
        
        if not items:
            messages.error(request, "Você deve adicionar pelo menos um item")
        else:
            # Processar e validar itens
            orcamento_data['itens'] = []
            
            for item_id, qtd, valor in zip(items, quantities, values):
                try:
                    produto = Produto.objects.get(id=item_id, company=company)
                    orcamento_data['itens'].append({
                        'tipo': 'produto',
                        'id': produto.id,
                        'nome': produto.nome,
                        'quantidade': Decimal(qtd),
                        'valor_unitario': Decimal(valor or produto.valor),
                        'subtotal': Decimal(qtd) * Decimal(valor or produto.valor),
                    })
                except (Produto.DoesNotExist, ValueError):
                    continue
            
            if orcamento_data['itens']:
                orcamento_data['etapa_atual'] = 2
                request.session['orcamento_data'] = orcamento_data
                return redirect('orcamento_novo_etapa3')
            else:
                messages.error(request, "Nenhum item válido foi adicionado")
    
    # GET - AJAX para listar produtos
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        produtos = Produto.objects.filter(company=company, disponivel=True)
        data = [
            {
                'id': p.id,
                'nome': p.nome,
                'valor': float(p.valor),
                'unidade': p.get_unidade_medida_display(),
            }
            for p in produtos
        ]
        return JsonResponse({'produtos': data})
    
    # GET - Mostrar formulário
    cliente_id = orcamento_data.get('cliente_id')
    cliente = Cliente.objects.get(id=cliente_id)
    produtos = Produto.objects.filter(company=company, disponivel=True)
    
    context = {
        'company': company,
        'cliente': cliente,
        'produtos': produtos,
        'etapa': 2,
        'orcamento_cliente': cliente,
    }
    
    return render(request, 'comercial/orcamentos/wizard.html', context)


# ============================================================================
# ETAPA 3: DETALHES E CONFIRMAÇÃO
# ============================================================================

@login_required
@require_company_access
def orcamento_novo_etapa3(request, company_id=None):
    """
    Etapa 3: Definir detalhes (validade, observações, forma de pagamento)
    e confirmação final
    """
    
    # Validar que veio das etapas anteriores
    orcamento_data = request.session.get('orcamento_data')
    if not orcamento_data or orcamento_data.get('etapa_atual') != 2:
        messages.error(request, "Você deve completar as etapas anteriores")
        return redirect('orcamento_novo_etapa1')
    
    company = get_object_or_404(CompanyProfile, id=company_id) if company_id else request.user.company_profile
    
    if request.method == 'POST':
        validade = request.POST.get('validade')
        forma_pagamento = request.POST.get('forma_pagamento')
        observacoes = request.POST.get('observacoes', '')
        usar_logo = request.POST.get('usar_logo') == 'on'
        action = request.POST.get('action', 'draft')  # 'draft' ou 'send'
        
        if not validade or not forma_pagamento:
            messages.error(request, "Validade e forma de pagamento são obrigatórios")
        else:
            # CRIAR ORÇAMENTO
            orcamento = criar_orcamento_completo(
                company=company,
                usuario=request.user,
                cliente_id=orcamento_data['cliente_id'],
                itens=orcamento_data['itens'],
                validade=validade,
                forma_pagamento=forma_pagamento,
                observacoes=observacoes,
                usar_logo=usar_logo,
            )
            
            # Limpar session
            del request.session['orcamento_data']
            
            if action == 'send':
                # Enviar ao cliente
                orcamento_enviar_ao_cliente(orcamento, request)
                messages.success(request, "Orçamento criado e enviado ao cliente!")
            else:
                # Apenas salvar como rascunho
                messages.success(request, "Orçamento salvo como rascunho!")
            
            return redirect('orcamento_detail', pk=orcamento.id)
    
    # GET - Mostrar resumo
    cliente = Cliente.objects.get(id=orcamento_data['cliente_id'])
    itens = orcamento_data.get('itens', [])
    
    total = sum(Decimal(item['subtotal']) for item in itens)
    
    context = {
        'company': company,
        'cliente': cliente,
        'orcamento_itens': itens,
        'total': total,
        'etapa': 3,
    }
    
    return render(request, 'comercial/orcamentos/wizard.html', context)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

@transaction.atomic
def criar_orcamento_completo(company, usuario, cliente_id, itens, validade, 
                             forma_pagamento, observacoes='', usar_logo=True):
    """
    Criar orçamento com todos os itens em uma transação
    """
    
    cliente = Cliente.objects.get(id=cliente_id, company=company)
    
    # Obter ou criar CompanyEmployee
    try:
        criado_por = CompanyEmployee.objects.get(user=usuario, company=company)
    except CompanyEmployee.DoesNotExist:
        # Criar como proprietário se não existir
        criado_por = CompanyEmployee.objects.create(
            user=usuario,
            company=company,
            role='owner'
        )
    
    # Criar orçamento
    orcamento = Orcamento.objects.create(
        company=company,
        cliente=cliente,
        usuario=usuario,
        criado_por=criado_por,
        validade=validade,
        forma_pagamento=forma_pagamento,
        observacoes=observacoes,
        status='rascunho',  # Sempre começa como rascunho
        desconto=Decimal('0'),
        logo=company.logo if usar_logo else None,
    )
    
    # Adicionar itens
    for item in itens:
        if item['tipo'] == 'produto':
            produto = Produto.objects.get(id=item['id'], company=company)
            OrcamentoProduto.objects.create(
                orcamento=orcamento,
                produto=produto,
                quantidade=item['quantidade'],
                valor_unitario=item['valor_unitario'],
            )
    
    return orcamento


def orcamento_enviar_ao_cliente(orcamento, request):
    """
    Enviar orçamento por email e gerar link público
    """
    
    # Gerar link público
    orcamento.link_publico = secrets.token_urlsafe(20)
    orcamento.enviado_em = timezone.now()
    orcamento.status = 'enviado'
    orcamento.save()
    
    # Construir URL pública
    link_publico = request.build_absolute_uri(
        reverse('orcamento_publico', kwargs={'token': orcamento.link_publico})
    )
    
    # Renderizar HTML do email
    html_email = render_to_string(
        'comercial/orcamentos/email_orcamento.html',
        {
            'orcamento': orcamento,
            'link_publico': link_publico,
            'dias_validade': (orcamento.validade - timezone.now().date()).days,
        }
    )
    
    # Enviar email
    try:
        send_mail(
            subject=f"Orçamento #{orcamento.id} - {orcamento.company.nome_empresa}",
            message="Use um cliente de email que suporte HTML para visualizar este orçamento.",
            from_email='noreply@seusistema.com',
            recipient_list=[orcamento.cliente.email],
            html_message=html_email,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Erro ao enviar email: {e}")


def usuario_pode_criar_orcamento(user, company):
    """
    Verificar se usuário tem permissão para criar orçamentos
    """
    
    if user.is_superuser:
        return True
    
    try:
        funcionario = CompanyEmployee.objects.get(user=user, company=company)
        return funcionario.can_create_orcamento()
    except CompanyEmployee.DoesNotExist:
        return False


# ============================================================================
# VISUALIZAÇÃO PÚBLICA DO ORÇAMENTO
# ============================================================================

@require_http_methods(['GET'])
def orcamento_publico(request, token):
    """
    Visualizar orçamento via link público (sem autenticação)
    """
    
    orcamento = get_object_or_404(Orcamento, link_publico=token)
    
    # Verificar se link ainda é válido
    if orcamento.validade < timezone.now().date():
        return render(request, 'comercial/orcamentos/publico_expirado.html', {
            'orcamento': orcamento,
        }, status=410)
    
    context = {
        'orcamento': orcamento,
        'itens_produtos': orcamento.orcamento_produtos.all(),
        'itens_servicos': orcamento.orcamento_servicos.all(),
    }
    
    return render(request, 'comercial/orcamentos/publico_detail.html', context)


# ============================================================================
# AÇÕES RÁPIDAS (DRAFT, SEND, DOWNLOAD)
# ============================================================================

@login_required
def orcamento_salvar_rascunho(request, pk):
    """
    Manter orçamento como rascunho (não enviar)
    """
    
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    if not usuario_pode_acessar_orcamento(request.user, orcamento):
        messages.error(request, "Você não tem permissão para acessar este orçamento")
        return redirect('home')
    
    orcamento.status = 'rascunho'
    orcamento.save()
    
    messages.success(request, "Orçamento salvo como rascunho")
    return redirect('orcamento_detail', pk=pk)


@login_required
def orcamento_enviar(request, pk):
    """
    Enviar orçamento ao cliente
    """
    
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    if not usuario_pode_acessar_orcamento(request.user, orcamento):
        messages.error(request, "Você não tem permissão para acessar este orçamento")
        return redirect('home')
    
    if not orcamento.cliente.email:
        messages.error(request, "Cliente não tem email cadastrado")
        return redirect('orcamento_detail', pk=pk)
    
    orcamento_enviar_ao_cliente(orcamento, request)
    messages.success(request, "Orçamento enviado ao cliente com sucesso!")
    
    return redirect('orcamento_detail', pk=pk)


@login_required
def orcamento_gerar_pdf(request, pk):
    """
    Gerar e baixar orçamento em PDF
    """
    
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    if not usuario_pode_acessar_orcamento(request.user, orcamento):
        messages.error(request, "Você não tem permissão para acessar este orçamento")
        return redirect('home')
    
    # TODO: Implementar geração de PDF usando reportlab ou weasyprint
    # Por enquanto, redirecionar para visualização
    return redirect('orcamento_detail', pk=pk)


def usuario_pode_acessar_orcamento(user, orcamento):
    """
    Verificar se usuário pode acessar um orçamento específico
    """
    
    if user.is_superuser:
        return True
    
    try:
        funcionario = CompanyEmployee.objects.get(
            user=user,
            company=orcamento.company,
            ativo=True
        )
        return True
    except CompanyEmployee.DoesNotExist:
        return False


# ============================================================================
# AUTOCOMPLETE PARA SELEÇÃO DE PRODUTOS (AJAX)
# ============================================================================

def orcamento_produtos_autocomplete(request):
    """
    API AJAX para autocomplete de produtos
    Query params: ?q=termo&company_id=id
    """
    
    termo = request.GET.get('q', '')
    
    try:
        company = request.user.company_profile
    except:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    produtos = Produto.objects.filter(
        company=company,
        disponivel=True,
        nome__icontains=termo
    )[:10]
    
    data = [
        {
            'id': p.id,
            'nome': f"{p.nome} - R$ {p.valor:.2f}",
            'valor': float(p.valor),
        }
        for p in produtos
    ]
    
    return JsonResponse({'results': data})
