# Guia de Implementação Passo a Passo

## ✅ Já Completo

- [x] Modelos criados e migrações aplicadas
  - CompanyProfile, ProductImage, Subscription
  - Todos os modelos existentes atualizados com campo `company`
- [x] Forms criados para os novos modelos
- [x] Signals preparados (comercial/signals.py)
- [x] Admin multi-tenant exemplo (comercial/admin_multitenant.py)
- [x] Documentação completa
- [x] Exemplos de views

---

## 📋 Próximos Passos (Implementação)

### Passo 1: Registrar Signals
**Arquivo**: `comercial/apps.py` ✅ (já feito)

O `ready()` foi adicionado para importar os signals automaticamente.

---

### Passo 2: Atualizar Django Admin
**Arquivo**: `comercial/admin.py`

```python
# ADICIONAR ao admin.py existente

from django.contrib import admin
from .models import (
    CompanyProfile, Subscription, Cliente, Marca, Produto, 
    ProductImage, Servico, Orcamento, Contrato, Evento
)

# Importar os admins do arquivo de exemplo
from .admin_multitenant import (
    CompanyProfileAdmin, SubscriptionAdmin, ClienteAdmin, 
    MarcaAdmin, ProdutoAdmin, ServicoAdmin, OrcamentoAdmin, 
    ContratoAdmin, EventoAdmin
)

# Registrar
admin.site.register(CompanyProfile, CompanyProfileAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Marca, MarcaAdmin)
admin.site.register(Produto, ProdutoAdmin)
admin.site.register(Servico, ServicoAdmin)
admin.site.register(Orcamento, OrcamentoAdmin)
admin.site.register(Contrato, ContratoAdmin)
admin.site.register(Evento, EventoAdmin)
```

---

### Passo 3: Criar Página de Registro de Empresa
**Arquivo**: `comercial/views.py` - Adicionar

```python
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse

def register_company(request):
    """Página de registro: usuário + empresa"""
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        nome_empresa = request.POST.get('nome_empresa')
        cnpj = request.POST.get('cnpj', '')
        
        # Criar usuário
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # CompanyProfile criada automaticamente pelo signal
        # Atualizar dados
        empresa = user.company_profile
        empresa.nome_empresa = nome_empresa
        empresa.cnpj = cnpj
        empresa.save()
        
        # Login automático
        user = authenticate(username=username, password=password)
        login(request, user)
        
        messages.success(request, "Empresa registrada com sucesso!")
        return redirect('home')
    
    return render(request, "comercial/register_company.html")


@login_required
def company_setup(request):
    """Página de configuração da empresa (após registro)"""
    empresa = request.user.company_profile
    
    if request.method == "POST":
        form = CompanyProfileForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "Empresa configurada com sucesso!")
            return redirect('home')
    else:
        form = CompanyProfileForm(instance=empresa)
    
    return render(request, "comercial/company_setup.html", {"form": form})
```

---

### Passo 4: Atualizar Views Existentes
**Arquivo**: `comercial/views.py` - Modificar

Aplique o padrão de cada view (veja `EXEMPLO_ATUALIZACAO_VIEWS.md`):

```python
# ANTES
def cliente_list(request):
    clientes = Cliente.objects.all()
    ...

# DEPOIS
@login_required
def cliente_list(request):
    clientes = Cliente.objects.filter(
        company=request.user.company_profile
    )
    ...
```

**Checklist de Views a Atualizar**:
- [ ] home() - Mostrar dados da empresa
- [ ] dashboard() - Filtrar por empresa
- [ ] cliente_list(), create(), update(), delete()
- [ ] marca_list(), create(), update(), delete()
- [ ] produto_list(), create(), update(), delete()
- [ ] servico_list(), create(), update(), delete()
- [ ] orcamento_list(), create(), update(), delete(), detail()
- [ ] contrato_list(), create(), update(), delete()
- [ ] evento_list(), create(), update(), delete()

---

### Passo 5: Atualizar Forms
**Arquivo**: `comercial/forms.py` - Adicionar método

```python
# Adicionar após cada formulário de modelo

class ClienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nome_completo", "cpf", "email", "endereco_residencial", "celular"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos agora opcionais
        self.fields['cpf'].required = False
        self.fields['email'].required = False
        self.fields['endereco_residencial'].required = False
        self.fields['celular'].required = False
```

---

### Passo 6: Criar Templates

**`templates/comercial/register_company.html`**
```html
{% extends "base.html" %}

{% block title %}Registrar Empresa{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <h2>Criar Empresa</h2>
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label>Usuário</label>
                    <input type="text" name="username" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>Email</label>
                    <input type="email" name="email" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>Senha</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>Nome da Empresa</label>
                    <input type="text" name="nome_empresa" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>CNPJ (opcional)</label>
                    <input type="text" name="cnpj" class="form-control">
                </div>
                <button type="submit" class="btn btn-primary">Registrar</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

**`templates/comercial/company_setup.html`**
```html
{% extends "base.html" %}

{% block title %}Configurar Empresa{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <h2>Configurar Empresa</h2>
            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}
                {{ form.as_p }}
                <button type="submit" class="btn btn-primary">Salvar</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

---

### Passo 7: Adicionar URLs
**Arquivo**: `comercial/urls.py`

```python
path('register/', register_company, name='register_company'),
path('company/setup/', company_setup, name='company_setup'),
```

---

### Passo 8: Atualizar Templates Base
**`templates/base.html`**

Adicionar logo e nome da empresa no header:

```html
{% if user.is_authenticated %}
    {% if user.company_profile %}
        <div class="navbar-brand">
            {% if user.company_profile.logo %}
                <img src="{{ user.company_profile.logo.url }}" height="40" alt="Logo">
            {% endif %}
            <span>{{ user.company_profile.nome_empresa }}</span>
        </div>
    {% endif %}
{% endif %}
```

---

### Passo 9: Testes
**Arquivo**: `comercial/tests.py`

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import CompanyProfile, Cliente

class MultiTenantTests(TestCase):
    def setUp(self):
        # Criar dois usuários com empresas diferentes
        self.user1 = User.objects.create_user('empresa1', 'emp1@test.com', 'pass')
        self.user2 = User.objects.create_user('empresa2', 'emp2@test.com', 'pass')
        
        # Verificar que CompanyProfiles foram criados
        self.assertEqual(CompanyProfile.objects.count(), 2)
    
    def test_isolamento_de_dados(self):
        """Verificar que cada usuário só vê seus dados"""
        empresa1 = self.user1.company_profile
        empresa2 = self.user2.company_profile
        
        # Criar clientes em empresas diferentes
        cliente1 = Cliente.objects.create(
            company=empresa1,
            nome_completo="Cliente 1"
        )
        cliente2 = Cliente.objects.create(
            company=empresa2,
            nome_completo="Cliente 2"
        )
        
        # Verificar isolamento
        self.assertEqual(Cliente.objects.filter(company=empresa1).count(), 1)
        self.assertEqual(Cliente.objects.filter(company=empresa2).count(), 1)
        self.assertEqual(cliente1.company, empresa1)
        self.assertEqual(cliente2.company, empresa2)
    
    def test_subscription_criada(self):
        """Verificar que Subscription é criada com pago=True"""
        empresa = self.user1.company_profile
        self.assertTrue(empresa.subscription.pago)
        self.assertIsNotNone(empresa.subscription.data_pagamento)
```

---

## 🚀 Resumo de Implementação

| Etapa | Status | Arquivo | Descrição |
|-------|--------|---------|-----------|
| 1. Signals | ⏳ Manual | `apps.py`, `signals.py` | Importar signals |
| 2. Admin | ⏳ Manual | `admin.py` | Registrar admin multi-tenant |
| 3. Registro | ⏳ Manual | `views.py` | Criar register_company() |
| 4. Views | ⏳ Manual | `views.py` | Filtrar por company |
| 5. Forms | ⏳ Manual | `forms.py` | Permitir campos vazios |
| 6. Templates | ⏳ Manual | `templates/` | Criar registro/setup |
| 7. URLs | ⏳ Manual | `urls.py` | Adicionar rotas |
| 8. Base | ⏳ Manual | `templates/base.html` | Adicionar logo/empresa |
| 9. Testes | ⏳ Manual | `tests.py` | Validar isolamento |

---

## 📚 Arquivos de Referência

- `ARQUITETURA_MULTITENANT.md` - Visão geral completa
- `EXEMPLO_ATUALIZACAO_VIEWS.md` - Exemplos de como atualizar views
- `comercial/admin_multitenant.py` - Admin pronto para copiar
- `comercial/signals.py` - Signals já criados
- `comercial/forms.py` - Forms atualizados

---

## ⚠️ Notas Importantes

1. **Dados Legados**: Registros antigos podem ter `company=NULL`. Migre ou deixe com `null=True`.
2. **Validação**: Sempre validar que `company=request.user.company_profile` nas views.
3. **Logo Vazia**: Templates devem ter fallback para logo padrão.
4. **CPF Único**: Agora é único por empresa, não globalmente.
5. **Campos Opcionais**: Permita campos vazios nos formulários.

---

## 🎯 Próximas Melhorias

- [ ] Painel de administração de assinatura/pagamento
- [ ] Integração com gateway de pagamento (PIX, Stripe, etc.)
- [ ] Suporte a múltiplos usuários por empresa
- [ ] Permissões/roles por usuário
- [ ] API para integração externa
- [ ] Webhooks para eventos
- [ ] Analytics por empresa
- [ ] Exportação de dados

