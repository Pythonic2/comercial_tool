# 🚀 Guia de Implementação - Novo Fluxo de Orçamentos

## Status Atual ✅

- ✅ Models atualizados (CompanyEmployee, Orcamento)
- ✅ Migrations 0002 e 0003 aplicadas
- ✅ Documentação criada
- ✅ Templates de exemplo criados
- ✅ Views de exemplo criadas

## Próximos Passos

### FASE 1: Integrar Views (30 min)

#### 1.1 Copiar imports nas views
Adicionar ao `comercial/views.py`:

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import secrets
from decimal import Decimal
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.db import transaction
```

#### 1.2 Copiar funções auxiliares
Copiar do `views_orcamento_novo.py` para `views.py`:
- `criar_orcamento_completo()`
- `orcamento_enviar_ao_cliente()`
- `usuario_pode_criar_orcamento()`
- `usuario_pode_acessar_orcamento()`

#### 1.3 Copiar as views principais
Copiar as funções:
- `orcamento_novo_etapa1()`
- `orcamento_novo_etapa2()`
- `orcamento_novo_etapa3()`
- `orcamento_publico()`
- `orcamento_salvar_rascunho()`
- `orcamento_enviar()`
- `orcamento_gerar_pdf()`
- `orcamento_produtos_autocomplete()`

---

### FASE 2: Atualizar URLs (15 min)

Adicionar ao `comercial/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    # ... URLs existentes ...
    
    # Novo fluxo de orçamentos
    path('orcamentos/novo/', views.orcamento_novo_etapa1, name='orcamento_novo_etapa1'),
    path('orcamentos/novo/etapa2/', views.orcamento_novo_etapa2, name='orcamento_novo_etapa2'),
    path('orcamentos/novo/etapa3/', views.orcamento_novo_etapa3, name='orcamento_novo_etapa3'),
    
    # Ações de orçamento
    path('orcamentos/<int:pk>/enviar/', views.orcamento_enviar, name='orcamento_enviar'),
    path('orcamentos/<int:pk>/rascunho/', views.orcamento_salvar_rascunho, name='orcamento_salvar_rascunho'),
    path('orcamentos/<int:pk>/pdf/', views.orcamento_gerar_pdf, name='orcamento_gerar_pdf'),
    
    # Público
    path('orcamento/<str:token>/', views.orcamento_publico, name='orcamento_publico'),
    
    # AJAX
    path('api/produtos/autocomplete/', views.orcamento_produtos_autocomplete, name='orcamento_produtos_autocomplete'),
]
```

---

### FASE 3: Criar Decorator para Acesso (10 min)

Criar arquivo `comercial/decorators.py`:

```python
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import CompanyProfile

def require_company_access(view_func):
    """
    Verificar que usuário tem acesso à empresa especificada
    Pode ser passada como parâmetro ou usar company_profile padrão
    """
    @wraps(view_func)
    def wrapper(request, company_id=None, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if company_id:
            try:
                company = CompanyProfile.objects.get(id=company_id)
                # Verificar acesso
                if not (request.user == company.owner or 
                        request.user.company_employees.filter(
                            company=company,
                            ativo=True
                        ).exists()):
                    messages.error(request, "Você não tem acesso a esta empresa")
                    return redirect('home')
            except CompanyProfile.DoesNotExist:
                messages.error(request, "Empresa não encontrada")
                return redirect('home')
        
        return view_func(request, company_id=company_id, *args, **kwargs)
    
    return wrapper
```

---

### FASE 4: Copiar/Atualizar Templates (20 min)

#### 4.1 Copiar template principal

O arquivo `templates/comercial/orcamentos/wizard_example.html` deve ser copiado para:
- `templates/comercial/orcamentos/wizard.html`

#### 4.2 Criar template de visualização pública

Criar `templates/comercial/orcamentos/publico_detail.html`:

```django
{% extends "base.html" %}

{% block title %}Orçamento #{{ orcamento.id }}{% endblock %}

{% block content %}
<div class="container mt-5 mb-5">
    <div class="card">
        <div class="card-header bg-primary text-white">
            <h3>Orçamento #{{ orcamento.id }}</h3>
            <p class="mb-0 small">{{ orcamento.company.nome_empresa }}</p>
        </div>
        
        <div class="card-body">
            <!-- Cabeçalho -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <h5>Empresa</h5>
                    <p>
                        <strong>{{ orcamento.company.nome_empresa }}</strong><br>
                        CNPJ: {{ orcamento.company.cnpj }}<br>
                        Telefone: {{ orcamento.company.telefone }}<br>
                        Email: {{ orcamento.company.email }}
                    </p>
                </div>
                <div class="col-md-6">
                    <h5>Cliente</h5>
                    <p>
                        <strong>{{ orcamento.cliente.nome_completo }}</strong><br>
                        {% if orcamento.cliente.email %}
                            Email: {{ orcamento.cliente.email }}<br>
                        {% endif %}
                        {% if orcamento.cliente.celular %}
                            Telefone: {{ orcamento.cliente.celular }}<br>
                        {% endif %}
                    </p>
                </div>
            </div>
            
            <!-- Logo se existir -->
            {% if orcamento.logo %}
                <div class="text-center mb-4">
                    <img src="{{ orcamento.logo.url }}" style="max-height: 100px;">
                </div>
            {% endif %}
            
            <!-- Itens -->
            <table class="table">
                <thead class="table-light">
                    <tr>
                        <th>Item</th>
                        <th class="text-end">Quantidade</th>
                        <th class="text-end">V. Unitário</th>
                        <th class="text-end">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in itens_produtos %}
                        <tr>
                            <td>{{ item.produto.nome }}</td>
                            <td class="text-end">{{ item.quantidade }}</td>
                            <td class="text-end">R$ {{ item.valor_unitario|floatformat:2 }}</td>
                            <td class="text-end">R$ {{ item.get_total|floatformat:2 }}</td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <!-- Resumo financeiro -->
            <div class="row">
                <div class="col-md-6 ms-auto">
                    <table class="table table-sm border">
                        <tr>
                            <td><strong>Subtotal:</strong></td>
                            <td class="text-end">R$ {{ orcamento.get_subtotal|floatformat:2 }}</td>
                        </tr>
                        <tr>
                            <td><strong>Desconto:</strong></td>
                            <td class="text-end">R$ {{ orcamento.desconto|floatformat:2 }}</td>
                        </tr>
                        <tr class="table-primary">
                            <td><strong>TOTAL:</strong></td>
                            <td class="text-end"><strong>R$ {{ orcamento.get_total|floatformat:2 }}</strong></td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <!-- Detalhes -->
            <hr>
            <div class="row mb-3">
                <div class="col-md-6">
                    <p><strong>Validade:</strong> {{ orcamento.validade|date:"d/m/Y" }}</p>
                    <p><strong>Forma de Pagamento:</strong> {{ orcamento.get_forma_pagamento_display }}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Criado em:</strong> {{ orcamento.criado_em|date:"d/m/Y H:i" }}</p>
                    <p><strong>Enviado em:</strong> 
                        {% if orcamento.enviado_em %}
                            {{ orcamento.enviado_em|date:"d/m/Y H:i" }}
                        {% else %}
                            Não enviado
                        {% endif %}
                    </p>
                </div>
            </div>
            
            {% if orcamento.observacoes %}
                <div class="alert alert-info">
                    <strong>Observações:</strong>
                    <p>{{ orcamento.observacoes|linebreaks }}</p>
                </div>
            {% endif %}
        </div>
        
        <div class="card-footer">
            <p class="text-muted small mb-0">
                Orçamento válido até {{ orcamento.validade|date:"d/m/Y" }}
            </p>
        </div>
    </div>
</div>
{% endblock %}
```

#### 4.3 Template de orçamento expirado

Criar `templates/comercial/orcamentos/publico_expirado.html`:

```django
{% extends "base.html" %}

{% block title %}Orçamento Expirado{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="alert alert-warning" role="alert">
        <h4>⚠️ Orçamento Expirado</h4>
        <p>
            O orçamento #{{ orcamento.id }} expirou em {{ orcamento.validade|date:"d/m/Y" }}.
        </p>
        <p>
            Para obter um novo orçamento, entre em contato com:
            <strong>{{ orcamento.company.nome_empresa }}</strong><br>
            Telefone: {{ orcamento.company.telefone }}<br>
            Email: {{ orcamento.company.email }}
        </p>
    </div>
</div>
{% endblock %}
```

#### 4.4 Email template

Criar `templates/comercial/orcamentos/email_orcamento.html`:

```django
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        th { background: #f8f9fa; }
        .total-row { background: #f8f9fa; font-weight: bold; }
        .footer { font-size: 12px; color: #666; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0; }
        .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ orcamento.company.nome_empresa }}</h1>
        <p>Orçamento #{{ orcamento.id }}</p>
    </div>
    
    <div class="content">
        <p>Prezado(a) {{ orcamento.cliente.nome_completo }},</p>
        
        <p>Segue em anexo o orçamento solicitado.</p>
        
        <table>
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Quantidade</th>
                    <th>Valor Unitário</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                {% for item in orcamento.orcamento_produtos.all %}
                <tr>
                    <td>{{ item.produto.nome }}</td>
                    <td>{{ item.quantidade }}</td>
                    <td>R$ {{ item.valor_unitario|floatformat:2 }}</td>
                    <td>R$ {{ item.get_total|floatformat:2 }}</td>
                </tr>
                {% endfor %}
                <tr class="total-row">
                    <td colspan="3">TOTAL</td>
                    <td>R$ {{ orcamento.get_total|floatformat:2 }}</td>
                </tr>
            </tbody>
        </table>
        
        <p><strong>Validade:</strong> {{ orcamento.validade|date:"d/m/Y" }} ({{ dias_validade }} dias)</p>
        <p><strong>Forma de Pagamento:</strong> {{ orcamento.get_forma_pagamento_display }}</p>
        
        {% if orcamento.observacoes %}
        <div style="background: #f0f8ff; padding: 10px; margin: 10px 0;">
            <strong>Observações:</strong><br>
            {{ orcamento.observacoes|linebreaks }}
        </div>
        {% endif %}
        
        <p style="text-align: center; margin-top: 30px;">
            <a href="{{ link_publico }}" class="btn">Ver Orçamento Completo</a>
        </p>
        
        <p>Em caso de dúvidas, nos contate:</p>
        <p>
            {{ orcamento.company.nome_empresa }}<br>
            Telefone: {{ orcamento.company.telefone }}<br>
            Email: {{ orcamento.company.email }}
        </p>
    </div>
    
    <div class="footer">
        <p>Este é um email automático. Por favor, não responda direto para este endereço.</p>
    </div>
</body>
</html>
```

---

### FASE 5: Adicionar Métodos aos Models (10 min)

Adicionar ao modelo `Orcamento` em `comercial/models.py`:

```python
class Orcamento(TimeStampedModel):
    # ... campos existentes ...
    
    def get_subtotal(self):
        """Calcular subtotal de todos os itens"""
        total_produtos = sum(
            item.get_total() for item in self.orcamento_produtos.all()
        ) if self.orcamento_produtos.exists() else 0
        
        total_servicos = sum(
            item.get_total() for item in self.orcamento_servicos.all()
        ) if self.orcamento_servicos.exists() else 0
        
        return total_produtos + total_servicos
    
    def get_total(self):
        """Calcular total com desconto"""
        return self.get_subtotal() - self.desconto
    
    def is_valido(self):
        """Verificar se orçamento ainda é válido"""
        from django.utils import timezone
        return self.validade >= timezone.now().date()
    
    def pode_ser_enviado(self):
        """Verificar se orçamento pode ser enviado"""
        return self.status == 'rascunho' and self.cliente.email
```

Adicionar aos modelos `OrcamentoProduto` e `OrcamentoServico`:

```python
class OrcamentoProduto(TimeStampedModel):
    # ... campos existentes ...
    
    def get_total(self):
        return self.quantidade * self.valor_unitario


class OrcamentoServico(TimeStampedModel):
    # ... campos existentes ...
    
    def get_total(self):
        return self.quantidade * self.valor_unitario
```

---

### FASE 6: Testar Sistema Completo (20 min)

#### 6.1 Teste no banco de dados
```bash
wsl -d Ubuntu bash -c "cd ~/vue_estudo && . venv/bin/activate && python manage.py check"
```

#### 6.2 Criar superuser para teste
```bash
wsl -d Ubuntu bash -c "cd ~/vue_estudo && . venv/bin/activate && python manage.py createsuperuser"
```

#### 6.3 Testar fluxo de orçamento
1. Acessar `/orcamentos/novo/`
2. Criar cliente novo
3. Adicionar 2-3 produtos
4. Definir detalhes
5. Enviar ao cliente
6. Acessar link público com token

#### 6.4 Verificar email (modo test)
Temporariamente, em `core/settings.py`:

```python
# Modo de teste - imprimir emails no console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

---

### FASE 7: Admin - Registrar CompanyEmployee (5 min)

Adicionar ao `comercial/admin.py`:

```python
from .models import CompanyEmployee

@admin.register(CompanyEmployee)
class CompanyEmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'ativo', 'criado_em')
    list_filter = ('company', 'role', 'ativo')
    search_fields = ('user__username', 'user__email', 'company__nome_empresa')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    def get_queryset(self, request):
        """Filtrar por empresa se não for superuser"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(company=request.user.company_profile)
        return qs
```

---

## 📋 Checklist Final

- [ ] Fase 1: Views copiadas para comercial/views.py
- [ ] Fase 2: URLs adicionadas em comercial/urls.py
- [ ] Fase 3: Decorator criado em comercial/decorators.py
- [ ] Fase 4: Templates criados/copiados
- [ ] Fase 5: Métodos adicionados aos models
- [ ] Fase 6: Sistema testado
- [ ] Fase 7: CompanyEmployee registrado no admin
- [ ] ✅ Teste de fluxo completo
- [ ] ✅ Teste de email de envio
- [ ] ✅ Teste de link público
- [ ] ✅ Produção

---

## 🎯 Próximas Features (Futuro)

1. **PDF Generation** - Usar ReportLab ou WeasyPrint para gerar PDF
2. **Approval Flow** - Cliente aprovar orçamento via link público
3. **Invoice Generation** - Converter orçamento aprovado em nota fiscal
4. **Recurring Quotes** - Duplicar orçamentos anteriores
5. **Analytics** - Dashboard com estatísticas de orçamentos
6. **Integration** - Integrar com WhatsApp, Telegram, etc.

