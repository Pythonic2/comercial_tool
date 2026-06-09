# Nova Arquitetura de Orçamentos - Implementação

## ✅ Mudanças Implementadas

### 1. Modelo CompanyEmployee
✅ Novo modelo para gerenciar funcionários por empresa
- `company` (FK) - empresa que o funcionário trabalha
- `user` (FK) - usuário Django
- `role` - Proprietário, Gerente, Funcionário
- `ativo` - pode acessar sistema ou não
- Métodos: `is_owner()`, `is_manager()`, `can_create_orcamento()`

### 2. Modelo Orcamento Atualizado
✅ Adicionados campos novos:
- `criado_por` (FK CompanyEmployee) - quem criou o orçamento
- `link_pubico` - Link público para cliente visualizar
- `enviado_em` - Quando foi enviado ao cliente
- Status mantém valores, mas NÃO aparece no formulário de criação

### 3. Migration 0003_companyemployee
✅ Aplicada com sucesso

---

## 📋 Novo Fluxo de Acesso (User Story)

### USUÁRIO 1: João (Proprietário)
```
1. Registra conta em /register/
2. Cria empresa "Dona do Chopp"
3. Acessa dashboard
4. Menu: "Gerenciar Funcionários"
5. Cadastra funcionários:
   - Maria (Gerente)
   - Pedro (Funcionário)
   - Ana (Funcionário)
```

### USUÁRIO 2: Maria (Gerente, funcionária)
```
1. Já tem conta (João criou)
2. Acessa /login/
3. Vê: "Você tem acesso a 1 empresa"
4. Clica em "Dona do Chopp"
5. Acessa dashboard da empresa
6. Pode criar orçamentos
```

### USUÁRIO 3: Cliente (sem acesso sistema, recebe orçamento)
```
1. Recebe email com link do orçamento
2. Clica em link público
3. Vê orçamento formatado em HTML
4. Não precisa login
```

---

## 🏗️ Fluxo de Criação de Orçamento (Reformulado)

### ANTES (Problemático)
```
┌────────────────────────────────────┐
│ Cliente: [dropdown]                │
│ Status: [rascunho/enviado/etc]     │  ← Confuso!
│ Validade: [data]                   │
│ Forma pagamento: [dropdown]        │
│ Desconto: [input]                  │
│ Observações: [textarea]            │
│                                    │
│ Produtos (1 por vez):              │
│ Produto: [dropdown]                │
│ Quantidade: [input]                │
│ Valor unitário: [input]            │
│ [+ Adicionar]                      │  ← Tedioso!
└────────────────────────────────────┘
```

### DEPOIS (Intuitivo)

#### **ETAPA 1: Cliente**
```
┌──────────────────────────────────────────┐
│ SELECAR CLIENTE                          │
├──────────────────────────────────────────┤
│                                          │
│ Ou use cliente existente:                │
│ ┌────────────────────────────────────┐  │
│ │ Procurar: [search input]           │  │
│ │ • E-Brasil Mkt  (CNPJ: 123...)     │  │
│ │ • João Silva    (CPF: 123...)      │  │
│ │ • Maria Santos  (CPF: 456...)      │  │
│ └────────────────────────────────────┘  │
│                                          │
│ Ou criar novo cliente:                   │
│ ┌────────────────────────────────────┐  │
│ │ [+ Novo Cliente - Formulário Rápido]  │
│ │ Nome: [input]                      │  │
│ │ Email: [input]                     │  │
│ │ Telefone: [input]                  │  │
│ │ [Salvar] [Cancelar]                │  │
│ └────────────────────────────────────┘  │
│                                          │
│ [← Voltar] [Próximo →]                   │
└──────────────────────────────────────────┘
```

#### **ETAPA 2: Itens (Produtos/Serviços)**
```
┌──────────────────────────────────────────────┐
│ ADICIONAR PRODUTOS/SERVIÇOS                  │
├──────────────────────────────────────────────┤
│                                              │
│ Cliente: E-Brasil Mkt [Mudar]                │
│                                              │
│ ┌──────────────────────────────────────────┐│
│ │ Produto│Qtd│V.Unitário│Total│Ações      ││
│ ├──────────────────────────────────────────┤│
│ │ [🔍]   │[1]│  [auto]   │[auto]│ [✕]     ││
│ │ [🔍]   │[1]│  [auto]   │[auto]│ [✕]     ││
│ │ [🔍]   │[1]│  [auto]   │[auto]│ [✕]     ││
│ │                                          ││
│ ├──────────────────────────────────────────┤│
│ │                  SUBTOTAL: R$ 5.454,00    ││
│ │                  DESCONTO: R$ [input]    ││
│ │                  TOTAL:    R$ 5.454,00    ││
│ └──────────────────────────────────────────┘│
│                                              │
│ Ações:                                       │
│ [+ Adicionar linha] [↻ Últimos itens]      │
│                                              │
│ [← Voltar] [Próximo →]                       │
└──────────────────────────────────────────────┘
```

**Detalhes da coluna Produto [🔍]**:
- Campo com autocomplete
- Mostra: "300 litros Brahma - R$ 5.194,00"
- Ao selecionar: preenche automaticamente "V.Unitário"
- Permite digitação livre (não selecionado)

#### **ETAPA 3: Detalhes**
```
┌──────────────────────────────────────────┐
│ DETALHES DO ORÇAMENTO                    │
├──────────────────────────────────────────┤
│                                          │
│ Validade:                                │
│ [data picker]                            │
│                                          │
│ Observações:                             │
│ [textarea - múltiplas linhas]            │
│                                          │
│ Forma de Pagamento:                      │
│ ○ Dinheiro  ○ PIX  ○ Cartão ○ Boleto   │
│                                          │
│ Usar Logo da Empresa:                    │
│ ○ Sim ● Não                              │
│                                          │
│ [← Voltar] [Próximo →]                    │
└──────────────────────────────────────────┘
```

#### **ETAPA 4: Revisão & Ações**
```
┌──────────────────────────────────────────┐
│ REVISÃO & ENVIO                          │
├──────────────────────────────────────────┤
│                                          │
│ CLIENTE:                                 │
│ E-Brasil Mkt                             │
│ contato@ebrasil.com                      │
│                                          │
│ ITENS:                                   │
│ • 300L Brahma x1 ........... R$ 5.194,00 │
│ • 2 Profissionais 4h x1 ... R$ 260,00    │
│ • 2 Balcões x1 ............. R$ 0,00     │
│                                          │
│ SUBTOTAL .................. R$ 5.454,00  │
│ DESCONTO ................... R$ 0,00     │
│ ───────────────────────────────────────  │
│ TOTAL ..................... R$ 5.454,00  │
│                                          │
│ Validade: 10/07/2026                     │
│ Forma pagamento: PIX                     │
│                                          │
│ Botões de ação:                          │
│ ┌────────────────────────────────────┐  │
│ │ [Editar] [Salvar Rascunho]        │  │
│ │ [✉ Enviar ao Cliente]             │  │
│ │ [⬇ Baixar PDF]                    │  │
│ └────────────────────────────────────┘  │
│                                          │
│ [← Voltar]                               │
└──────────────────────────────────────────┘
```

---

## 💻 Implementação (Forms)

### OrcamentoClienteForm - ETAPA 1
```python
class OrcamentoClienteForm(BootstrapFormMixin, forms.Form):
    """Selecionar ou criar cliente"""
    
    cliente_existente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        required=False,
        label="Cliente Existente",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    novo_cliente_nome = forms.CharField(
        max_length=120,
        required=False,
        label="Nome (novo cliente)"
    )
    novo_cliente_email = forms.EmailField(
        required=False,
        label="Email (novo cliente)"
    )
    novo_cliente_telefone = forms.CharField(
        max_length=20,
        required=False,
        label="Telefone (novo cliente)"
    )
    
    def clean(self):
        cleaned = super().clean()
        cliente = cleaned.get('cliente_existente')
        novo_nome = cleaned.get('novo_cliente_nome')
        
        # Validar: um dos dois deve estar preenchido
        if not cliente and not novo_nome:
            raise forms.ValidationError(
                "Selecione um cliente existente ou crie um novo"
            )
        
        return cleaned
```

### OrcamentoItensForm - ETAPA 2
```python
class OrcamentoItemForm(forms.Form):
    """Adicionar múltiplos itens em uma tabela"""
    
    TIPO_CHOICES = [
        ('produto', 'Produto'),
        ('servico', 'Serviço'),
    ]
    
    tipo = forms.ChoiceField(choices=TIPO_CHOICES)
    item_id = forms.IntegerField()
    quantidade = forms.DecimalField(
        min_value=Decimal('0.01'),
        decimal_places=2
    )
    valor_unitario = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        required=False  # Auto-preenchido
    )
    
    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')
        item_id = cleaned.get('item_id')
        
        # Validar que item existe
        if tipo == 'produto':
            try:
                Produto.objects.get(id=item_id)
            except Produto.DoesNotExist:
                raise forms.ValidationError("Produto não encontrado")
        
        return cleaned
```

### OrcamentoDetalhesForm - ETAPA 3
```python
class OrcamentoDetalhesForm(BootstrapFormMixin, forms.Form):
    """Detalhes finais do orçamento"""
    
    validade = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        required=False
    )
    
    forma_pagamento = forms.ChoiceField(
        choices=Orcamento.FORMAS_PAGAMENTO,
        widget=forms.RadioSelect()
    )
    
    usar_logo = forms.BooleanField(
        required=False,
        label="Usar logo da empresa"
    )
```

---

## 🔄 Views Reformuladas

### Vista de Múltiplas Etapas
```python
@login_required
def orcamento_create_wizard(request):
    """
    Assistente de criação de orçamento em múltiplas etapas
    Armazena dados em session até confirmação final
    """
    
    etapa = request.GET.get('etapa', '1')
    
    if request.method == 'POST':
        if etapa == '1':
            # Processar cliente
            form = OrcamentoClienteForm(request.POST)
            if form.is_valid():
                # Salvar em session
                request.session['orcamento_cliente'] = form.cleaned_data
                return redirect('orcamento_create_wizard?etapa=2')
        
        elif etapa == '2':
            # Processar itens (múltiplos)
            itens = request.POST.getlist('items')
            request.session['orcamento_itens'] = itens
            return redirect('orcamento_create_wizard?etapa=3')
        
        elif etapa == '3':
            # Salvar orçamento completo
            orcamento = criar_orcamento_from_session(request)
            messages.success(request, "Orçamento criado!")
            return redirect('orcamento_detail', pk=orcamento.pk)
    
    # GET - mostrar etapa apropriada
    if etapa == '1':
        form = OrcamentoClienteForm()
    elif etapa == '2':
        form = OrcamentoItensForm()
    elif etapa == '3':
        form = OrcamentoDetalhesForm()
    
    context = {
        'form': form,
        'etapa': etapa,
        'progresso': f'{etapa}/3',
    }
    
    return render(request, 'comercial/orcamentos/wizard.html', context)
```

---

## 🎯 Recursos Principais

### Autocomplete de Produtos
```javascript
// Em template JavaScript
document.querySelectorAll('.produto-autocomplete').forEach(el => {
    new Autocomplete(el, {
        onSelectItem: ({item}) => {
            // item = {id, nome, valor}
            el.parentElement.next().value = item.valor; // Preencher valor
        }
    });
});
```

### Cálculo de Total em Tempo Real
```javascript
function atualizarTotal() {
    let subtotal = 0;
    document.querySelectorAll('tr.item-linha').forEach(tr => {
        let qtd = tr.querySelector('[name="quantidade"]').value || 0;
        let valor = tr.querySelector('[name="valor_unitario"]').value || 0;
        subtotal += qtd * valor;
    });
    
    let desconto = document.querySelector('[name="desconto"]').value || 0;
    let total = subtotal - desconto;
    
    document.querySelector('.total-display').textContent = 
        formatarMoeda(total);
}

// Atualizar ao mudar qualquer campo
document.querySelectorAll('[name="quantidade"], [name="valor_unitario"], [name="desconto"]')
    .forEach(el => el.addEventListener('change', atualizarTotal));
```

### Salvar Rascunho
```python
@login_required
def orcamento_save_draft(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    # Validar permissão
    if orcamento.criado_por.user != request.user:
        raise PermissionDenied
    
    # Manter como rascunho
    orcamento.status = 'rascunho'
    orcamento.save()
    
    messages.success(request, "Orçamento salvo como rascunho")
    return redirect('orcamento_list')
```

### Enviar Ao Cliente
```python
@login_required
def orcamento_send(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    # Gerar link público
    orcamento.link_pubico = secrets.token_urlsafe(20)
    orcamento.enviado_em = timezone.now()
    orcamento.save()
    
    # Enviar email
    enviar_email_orcamento(
        orcamento.cliente.email,
        orcamento,
        request.build_absolute_uri(f'/orcamento/{orcamento.link_pubico}/')
    )
    
    messages.success(request, "Orçamento enviado ao cliente!")
    return redirect('orcamento_detail', pk=pk)
```

---

## 🛡️ Segurança

### Verificar Permissões
```python
def verificar_acesso_orcamento(user, orcamento):
    """
    Usuário pode acessar orçamento se:
    - É o proprietário da empresa, OU
    - É funcionário ativo da empresa que criou, OU
    - É o cliente (via link público)
    """
    
    # Funcionário da empresa
    if hasattr(user, 'company_employees'):
        empresas = user.company_employees.filter(
            company=orcamento.company,
            ativo=True
        )
        if empresas.exists():
            return True
    
    # Cliente (via link público)
    # Aceitar sem autenticação
    return False
```

---

## 📊 Status do Orçamento

Nunca muda automaticamente. Muda apenas por ações do usuário:

| Status | Ação | Feito por |
|--------|------|-----------|
| rascunho → enviado | "Enviar ao Cliente" | Funcionário |
| rascunho → cancelado | "Cancelar" | Funcionário |
| enviado → aprovado | (futuro) | Cliente via link |
| enviado → executado | (futuro) | Proprietário |

---

## ✅ Checklist de Implementação

- [ ] Criar template wizard.html (4 etapas)
- [ ] Implementar views de wizard
- [ ] Adicionar JavaScript para autocomplete
- [ ] Adicionar cálculo de total em tempo real
- [ ] Implementar send_email_orcamento
- [ ] Criar view pública de visualização
- [ ] Testar fluxo completo
- [ ] Adicionar permissões de acesso

