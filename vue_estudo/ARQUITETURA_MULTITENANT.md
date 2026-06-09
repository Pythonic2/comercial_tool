# Arquitetura Multi-Tenant Modular

## Visão Geral

O sistema foi refatorado para ser **multi-tenant**, permitindo que múltiplas empresas usem a plataforma de forma isolada. Cada empresa registra um perfil, seus clientes, produtos/serviços, e gerencia sua assinatura.

---

## Modelos Criados

### 1. **CompanyProfile** (Empresa)
- **Proprietário**: `owner` (OneToOneField para User)
- **Dados da Empresa**:
  - `nome_empresa`: Nome da empresa
  - `cnpj`: CNPJ (opcional)
  - `telefone`: Telefone de contato
  - `email`: Email da empresa
  - `endereco`: Endereço completo
  - `logo`: Imagem da logo (opcional, pode deixar em branco)

**Uso**: Cada usuário que se registra no sistema tem uma `CompanyProfile` associada. Todos os dados comerciais (clientes, produtos, orçamentos, etc.) são vinculados a uma empresa específica.

```python
# Exemplo
empresa = CompanyProfile.objects.create(
    owner=usuario,
    nome_empresa="Dona do Chopp Ltda",
    cnpj="44919343000120",
    telefone="85981423909",
    email="donadochopp@gmail.com",
    endereco="Rua Goiás - Panamericano, 60441-005 - Fortaleza/CE"
)
```

---

### 2. **Subscription** (Assinatura/Pagamento)
- **Empresa**: `company` (OneToOneField)
- **Status**:
  - `pago`: Boolean (padrão = True)
  - `data_pagamento`: Data do último pagamento (auto_now_add)
  - `proximo_pagamento`: Data do próximo pagamento (calculado automaticamente)
  - `valor_mensalidade`: Valor da mensalidade

**Uso**: Gerencia a assinatura de cada empresa. No momento, todos têm `pago=True` com data preenchida automaticamente.

**Futuro**: Será expandido para:
- Suporte a diferentes planos (básico, premium, etc.)
- Integração com gateway de pagamento
- Suporte a múltiplos meios de pagamento (PIX, cartão, boleto, etc.)

```python
# Exemplo - Criado automaticamente quando uma CompanyProfile é criada
subscription = Subscription.objects.create(
    company=empresa,
    pago=True,
    valor_mensalidade=Decimal("99.90")
)
```

---

### 3. **Cliente** (Agora Multi-Tenant)
- **Empresa**: `company` (ForeignKey para CompanyProfile)
- **Campos** (agora todos opcionais):
  - `nome_completo`: Nome do cliente
  - `cpf`: CPF (opcional, blank=True)
  - `email`: Email (opcional)
  - `endereco_residencial`: Endereço (opcional)
  - `celular`: Telefone (opcional)

**Mudanças**:
- Adicionado campo `company` para isolar clientes por empresa
- Todos os campos agora podem ser deixados em branco
- `cpf` não é mais globalmente único, mas sim único por empresa

```python
# Exemplo
cliente = Cliente.objects.create(
    company=empresa,
    nome_completo="E-Brasil Mkt",
    cpf="15.235.934/0001-80",  # Opcional
    email="contato@ebrasil.com",  # Opcional
    endereco_residencial="Rua Luís Braille - Monte Castelo, 79010-080",  # Opcional
    celular="67987654321"  # Opcional
)
```

---

### 4. **Marca** (Agora Multi-Tenant)
- **Empresa**: `company` (ForeignKey)
- **Campo único**: Nome único por empresa (não globalmente)

---

### 5. **Produto** (Agora Multi-Tenant + Imagens)
- **Empresa**: `company` (ForeignKey)
- **Campos principais**:
  - `nome`, `valor`, `unidade_medida`, `descricao`, etc.
  - `marca`: Agora opcional (blank=True)

**Nova Funcionalidade**: Produtos agora suportam **múltiplas imagens**

```python
# Exemplo
produto = Produto.objects.create(
    company=empresa,
    nome="300 litros Brahma ou Heineken",
    valor=Decimal("5194.00"),
    unidade_medida="lt",
    descricao="Chopp premium importado"
)

# Adicionar imagens
ProductImage.objects.create(
    produto=produto,
    imagem="path/to/image1.jpg",
    ordem=1,
    descricao="Foto frontal"
)
ProductImage.objects.create(
    produto=produto,
    imagem="path/to/image2.jpg",
    ordem=2,
    descricao="Detalhe do produto"
)
```

---

### 6. **ProductImage** (Novo)
- **Produto**: `produto` (ForeignKey)
- **Campos**:
  - `imagem`: ImageField
  - `ordem`: Posição na galeria
  - `descricao`: Descrição opcional

**Uso**: Permite que cada produto tenha múltiplas fotos, como no orçamento PDF que mostra fotos dos serviços.

---

### 7. **Serviço** (Agora Multi-Tenant)
- **Empresa**: `company` (ForeignKey)
- **Exemplo**: "2 Profissionais durante 4h" é um serviço, não um produto

```python
servico = Servico.objects.create(
    company=empresa,
    nome="2 Profissionais durante 4h",
    valor=Decimal("260.00"),
    descricao="Instalação e suporte de 4 horas",
    ativo=True
)
```

---

### 8. **Orçamento** (Agora Multi-Tenant)
- **Empresa**: `company` (ForeignKey)
- **Cliente**: Referência ao Cliente específico da empresa
- Mantém todos os itens (OrcamentoProduto, OrcamentoServico)

---

### 9. **Contrato** e **Evento** (Agora Multi-Tenant)
- Ambos agora incluem `company` (ForeignKey)
- Isolados por empresa

---

## Fluxo de Cadastro (Novo Usuário/Empresa)

1. **Usuário cria conta** → Django User criado
2. **CompanyProfile criada** → Automaticamente vinculada ao User
3. **Subscription criada** → Com `pago=True` por padrão
4. **Usuário preenche dados da empresa** → Deixa campos em branco se desejar
5. **Usuário cadastra clientes** → Vinculados à sua empresa
6. **Usuário cadastra produtos/serviços** → Com suporte a múltiplas imagens
7. **Usuário cria orçamentos** → Com produtos/serviços de sua empresa

---

## Exemplo de Uso Prático

```python
# 1. Criar usuário
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.create_user(
    username='empresa1',
    email='empresa1@example.com',
    password='senha123'
)

# 2. CompanyProfile criada automaticamente pelo signal (se implementado)
# Ou criar manualmente:
empresa = CompanyProfile.objects.create(
    owner=user,
    nome_empresa="Minha Empresa",
    cnpj="12345678901234",
    logo=None  # Deixar em branco
)

# 3. Subscription criada automaticamente
# Ou criar manualmente:
subscription, created = Subscription.objects.get_or_create(
    company=empresa,
    defaults={'pago': True}
)

# 4. Cadastrar cliente
cliente = Cliente.objects.create(
    company=empresa,
    nome_completo="Cliente ABC"
    # Deixar outros campos em branco se quiser
)

# 5. Cadastrar produto com imagens
produto = Produto.objects.create(
    company=empresa,
    nome="Produto A",
    valor=100.00
)
imagem = ProductImage.objects.create(
    produto=produto,
    imagem="path/to/image.jpg"
)

# 6. Criar orçamento
orcamento = Orcamento.objects.create(
    company=empresa,
    cliente=cliente,
    usuario=user
)
```

---

## Isolamento de Dados (Multi-Tenant)

Cada empresa vê apenas:
- Seus próprios clientes
- Seus próprios produtos/serviços
- Seus próprios orçamentos, contratos e eventos
- Sua própria assinatura

**Implementação nas Views**: As views precisam filtrar por `company` do usuário logado:

```python
@login_required
def cliente_list(request):
    clientes = Cliente.objects.filter(
        company=request.user.company_profile
    )
    return render(request, "comercial/clientes/list.html", {"clientes": clientes})
```

---

## Próximos Passos

1. **Atualizar Views e Forms** para referenciar `company` automaticamente
2. **Adicionar Signals** para criar CompanyProfile/Subscription automaticamente
3. **Criar Página de Configuração** para empresa preencher dados
4. **Implementar Upload de Logo** com validação
5. **Expandir Subscription** para suportar múltiplos planos e meios de pagamento
6. **Dashboard** para visualizar dados por empresa
7. **Testes** para garantir isolamento de dados

---

## Campos Agora Opcionais

Para permitir que empresas deixem campos em branco:
- `Cliente.cpf` → blank=True, null=False (string vazia)
- `Cliente.email` → blank=True
- `Cliente.endereco_residencial` → blank=True
- `Cliente.celular` → blank=True
- `Marca.nome` → Ainda deve ter nome, mas agora é único por empresa
- `Produto.marca` → blank=True, null=True
- `Produto.estoque_quantidade` → blank=True (padrão 0)
- `CompanyProfile.logo` → blank=True, null=True
- Todos os campos de `CompanyProfile` exceto `nome_empresa` → blank=True

---

## Notas Importantes

- **Backward Compatibility**: Os dados antigos ainda existem com `company=NULL`. Você pode migrar dados existentes para uma empresa "padrão" se necessário.
- **Campos Vazios**: Use `blank=True` nas forms para permitir campos vazios
- **Logo**: Pode ser deixada em branco, imagem padrão será usada no template
- **Teste**: Crie uma empresa de teste para validar o fluxo completo

