# Exemplo de Atualização de Views para Multi-Tenant

## Padrão Geral

### Antes (Single Tenant):
```python
@login_required
def cliente_list(request):
    clientes = Cliente.objects.all()
    return render(request, "comercial/clientes/list.html", {"clientes": clientes})
```

### Depois (Multi-Tenant):
```python
@login_required
def cliente_list(request):
    # Filtrar apenas clientes da empresa do usuário
    clientes = Cliente.objects.filter(
        company=request.user.company_profile
    )
    return render(request, "comercial/clientes/list.html", {"clientes": clientes})
```

---

## Exemplos de Atualização Necessária

### 1. Cliente Views

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

@login_required
def cliente_list(request):
    """Listar clientes da empresa"""
    clientes = Cliente.objects.filter(
        company=request.user.company_profile
    )
    return render(request, "comercial/clientes/list.html", {"clientes": clientes})


@login_required
def cliente_create(request):
    """Criar novo cliente"""
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.company = request.user.company_profile  # Auto-preencher company
            cliente.save()
            messages.success(request, "Cliente criado com sucesso.")
            return redirect("cliente_list")
    else:
        form = ClienteForm()
    return render(request, "comercial/clientes/form.html", {"form": form})


@login_required
def cliente_detail(request, pk):
    """Ver detalhes de um cliente"""
    cliente = get_object_or_404(
        Cliente, 
        pk=pk, 
        company=request.user.company_profile  # Garantir acesso apenas à sua empresa
    )
    return render(request, "comercial/clientes/detail.html", {"cliente": cliente})


@login_required
def cliente_update(request, pk):
    """Editar cliente"""
    cliente = get_object_or_404(
        Cliente, 
        pk=pk, 
        company=request.user.company_profile
    )
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente atualizado com sucesso.")
            return redirect("cliente_list")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "comercial/clientes/form.html", {"form": form, "cliente": cliente})


@login_required
def cliente_delete(request, pk):
    """Deletar cliente"""
    cliente = get_object_or_404(
        Cliente, 
        pk=pk, 
        company=request.user.company_profile
    )
    if request.method == "POST":
        cliente.delete()
        messages.success(request, "Cliente deletado com sucesso.")
        return redirect("cliente_list")
    return render(request, "comercial/clientes/confirm_delete.html", {"cliente": cliente})
```

---

### 2. Produto Views

```python
@login_required
def produto_list(request):
    """Listar produtos da empresa"""
    produtos = Produto.objects.filter(
        company=request.user.company_profile
    ).prefetch_related("product_images")
    return render(request, "comercial/produtos/list.html", {"produtos": produtos})


@login_required
def produto_create(request):
    """Criar novo produto com imagens"""
    if request.method == "POST":
        form = ProdutoForm(request.POST, request.FILES)
        formset = ProductImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            produto = form.save(commit=False)
            produto.company = request.user.company_profile
            produto.save()
            
            # Salvar imagens
            formset.instance = produto
            formset.save()
            
            messages.success(request, "Produto criado com sucesso com suas imagens.")
            return redirect("produto_list")
    else:
        form = ProdutoForm()
        formset = ProductImageFormSet()
    
    return render(request, "comercial/produtos/form.html", {
        "form": form,
        "formset": formset
    })


@login_required
def produto_update(request, pk):
    """Editar produto e suas imagens"""
    produto = get_object_or_404(
        Produto, 
        pk=pk, 
        company=request.user.company_profile
    )
    
    if request.method == "POST":
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        formset = ProductImageFormSet(request.POST, request.FILES, instance=produto)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Produto atualizado com sucesso.")
            return redirect("produto_list")
    else:
        form = ProdutoForm(instance=produto)
        formset = ProductImageFormSet(instance=produto)
    
    return render(request, "comercial/produtos/form.html", {
        "form": form,
        "formset": formset,
        "produto": produto
    })
```

---

### 3. Orçamento Views

```python
@login_required
def orcamento_list(request):
    """Listar orçamentos da empresa"""
    orcamentos = Orcamento.objects.filter(
        company=request.user.company_profile
    ).select_related("cliente")
    return render(request, "comercial/orcamentos/list.html", {"orcamentos": orcamentos})


@login_required
def orcamento_create(request):
    """Criar novo orçamento"""
    if request.method == "POST":
        form = OrcamentoForm(request.POST, request.FILES)
        produto_formset = OrcamentoProdutoFormSet(request.POST)
        servico_formset = OrcamentoServicoFormSet(request.POST)
        
        if form.is_valid() and produto_formset.is_valid() and servico_formset.is_valid():
            orcamento = form.save(commit=False)
            orcamento.company = request.user.company_profile
            orcamento.usuario = request.user
            orcamento.save()
            
            # Salvar itens
            produto_formset.instance = orcamento
            produto_formset.save()
            servico_formset.instance = orcamento
            servico_formset.save()
            
            messages.success(request, "Orçamento criado com sucesso.")
            return redirect("orcamento_detail", pk=orcamento.pk)
    else:
        form = OrcamentoForm()
        # Filtrar apenas clientes da empresa
        form.fields['cliente'].queryset = Cliente.objects.filter(
            company=request.user.company_profile
        )
        produto_formset = OrcamentoProdutoFormSet()
        servico_formset = OrcamentoServicoFormSet()
    
    return render(request, "comercial/orcamentos/form.html", {
        "form": form,
        "produto_formset": produto_formset,
        "servico_formset": servico_formset
    })
```

---

## Recomendações

1. **Use select_related/prefetch_related** para evitar N+1 queries
   ```python
   orcamentos = Orcamento.objects.filter(
       company=request.user.company_profile
   ).select_related("cliente", "usuario")
   ```

2. **Sempre validar company do usuário** em get_object_or_404
   ```python
   get_object_or_404(Modelo, pk=pk, company=request.user.company_profile)
   ```

3. **Auto-preencher company em create/update**
   ```python
   instance.company = request.user.company_profile
   ```

4. **Filtrar QuerySets em form.fields**
   ```python
   form.fields['cliente'].queryset = Cliente.objects.filter(
       company=request.user.company_profile
   )
   ```

5. **Decorator para verificar Company**
   ```python
   from functools import wraps
   
   def company_required(view_func):
       @wraps(view_func)
       def wrapper(request, *args, **kwargs):
           if not hasattr(request.user, 'company_profile'):
               messages.error(request, "Você precisa configurar sua empresa primeiro.")
               return redirect('company_setup')
           return view_func(request, *args, **kwargs)
       return wrapper
   ```

---

## Padrão de Filtro Reutilizável

```python
# utils.py
def get_user_company(request):
    """Helper para obter a empresa do usuário"""
    if hasattr(request.user, 'company_profile'):
        return request.user.company_profile
    return None

def get_company_or_404(request):
    """Helper que redireciona se usuário não tem empresa"""
    company = get_user_company(request)
    if not company:
        messages.error(request, "Você precisa configurar sua empresa primeiro.")
        raise Redirect('company_setup')
    return company
```

Uso:
```python
@login_required
def cliente_list(request):
    company = get_company_or_404(request)
    clientes = Cliente.objects.filter(company=company)
    return render(request, "comercial/clientes/list.html", {"clientes": clientes})
```

---

## Checklist de Atualização

- [ ] Views de Cliente (list, create, update, delete)
- [ ] Views de Marca (list, create, update, delete)
- [ ] Views de Produto (list, create com imagens, update, delete)
- [ ] Views de Serviço (list, create, update, delete)
- [ ] Views de Orçamento (list, create, update, delete)
- [ ] Views de Contrato (list, create, update, delete)
- [ ] Views de Evento (list, create, update, delete)
- [ ] Views de Configuração da Empresa (setup, update)
- [ ] Dashboard (filtrado por empresa)
- [ ] Admin Django (filtrado por empresa)
- [ ] Testes de isolamento de dados

