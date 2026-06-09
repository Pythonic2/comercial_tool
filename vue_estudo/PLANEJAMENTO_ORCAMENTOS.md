"""
PLANEJAMENTO DETALHADO - NOVA ARQUITETURA DE ORÇAMENTOS

== ESTRUTURA DE USUÁRIOS ==

1. PROPRIETÁRIO (Owner)
   - Usuário que criou a empresa
   - Acesso total: clientes, produtos, funcionários, orçamentos
   - Gerencia assinatura

2. FUNCIONÁRIO (Employee)
   - Cadastrado pelo proprietário
   - Pode: criar orçamentos, ver clientes, ver produtos
   - Não pode: deletar, editar empresa, gerenciar funcionários
   - Permissões personalizáveis (futuro)

== FLUXO DE ACESSO ==

┌─────────────────────────────────────────────────────────┐
│ NOVO USUÁRIO                                            │
└─────────────────────────────────────────────────────────┘
                    ↓
        [Registrar conta ou Login?]
                ↙           ↘
    [Registrar]          [Login]
        ↓                   ↓
  [Criar empresa]    [Funcionário?]
        ↓                 ↙    ↘
  [Dashboard]    [Sim]      [Não - novo]
        ↓         ↓           ↓
  [Gerenciar]  [Acessar]  [Criar empresa]
   funcionários dashboard    ↓
                            [Dashboard]

== MODELOS ==

User (Django)
  ├─ CompanyProfile (1:1)
  │   ├─ CompanyEmployee (M:1) - múltiplos funcionários
  │   ├─ Cliente (M:1)
  │   ├─ Produto (M:1)
  │   ├─ Serviço (M:1)
  │   ├─ Subscription (1:1)
  │   └─ Orcamento (M:1)
  │
  └─ CompanyEmployee (M:1) - se for funcionário

== NOVO MODELO: CompanyEmployee ==

CompanyEmployee:
  - company (FK CompanyProfile)
  - user (FK User)
  - role (choices: 'owner', 'employee', 'manager')
  - permissions (JSONField) - futuro
  - date_joined
  - ativo

== FLUXO DE CRIAÇÃO DE ORÇAMENTO ==

[Dashboard]
    ↓
[Novo Orçamento]
    ↓
┌─────────────────────────────────────────────┐
│ ETAPA 1: SELEÇÃO DE CLIENTE                 │
├─────────────────────────────────────────────┤
│ • Dropdown de clientes existentes OR         │
│ • Botão "Novo cliente" (formulário rápido)  │
│ • Pré-preencher dados se existir             │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ ETAPA 2: ADICIONAR PRODUTOS/SERVIÇOS        │
├─────────────────────────────────────────────┤
│ • Tabela com linhas vazias para preenchimento
│ • Campo de produto (autocomplete)            │
│ • Campo de quantidade                        │
│ • Campo de valor unitário (auto-popula)     │
│ • Botão "+ Adicionar linha"                 │
│ • Botão "- Remover linha"                   │
│ • Preview de total em tempo real             │
│ • Histórico de itens recentes (rápido acesso)
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ ETAPA 3: OBSERVAÇÕES E VALIDADE             │
├─────────────────────────────────────────────┤
│ • Campo de observações (textarea)            │
│ • Data de validade                          │
│ • Desconto (opcional)                       │
│ • Logo a usar (padrão da empresa)           │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ ETAPA 4: REVISÃO E AÇÕES                    │
├─────────────────────────────────────────────┤
│ Resumo:                                     │
│ • Dados do cliente                          │
│ • Itens (produtos/serviços)                 │
│ • Total                                     │
│ • Validade                                  │
│                                              │
│ Botões:                                     │
│ • [Salvar como rascunho] - volta lista      │
│ • [Gerar PDF] - download                    │
│ • [Enviar cliente] - email + link           │
│ • [Editar] - volta pra etapa anterior       │
└─────────────────────────────────────────────┘

== MUDANÇAS NO MODELO ==

Orcamento:
  ✓ Remove: status (sempre "rascunho" inicialmente)
  ✓ Add: criado_por (FK CompanyEmployee) - quem criou
  ✓ Add: enviado_em (DateTimeField)
  ✓ Add: link_pubico (CharField unique) - para compartilhar
  ✓ Keep: tudo que tem já

== INTERFACE MELHORADA ==

ANTES:
┌─────────────────────────────────┐
│ Cliente: [dropdown]              │
│ Status: [dropdown]               │
│ Validade: [data]                 │
│ Forma pagamento: [dropdown]      │
│ Desconto: [input]                │
│ Logo: [file upload]              │
│ Observações: [textarea]          │
└─────────────────────────────────┘

Produtos (adicionar 1 por vez):
┌─────────────────────────────────┐
│ Produto: [dropdown]              │
│ Quantidade: [input]              │
│ Valor unitário: [input]          │
│                                  │
│ [+ Adicionar]                    │
└─────────────────────────────────┘

DEPOIS:
┌──────────────────────────────────────────────┐
│ 1. CLIENTE (cards com opções)                │
├──────────────────────────────────────────────┤
│ [Novo Cliente] [Cliente Existente...]        │
│                                              │
│ Se existente: dropdown com busca             │
│ Se novo: formulário rápido inline            │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 2. ITEMS (tabela dinâmica)                   │
├──────────────────────────────────────────────┤
│ Produto │ Qtd │ V.Unit │ Total │ Ações      │
├──────────────────────────────────────────────┤
│ [input] │ [n] │ [auto] │ [auto]│ [X]        │
│ [input] │ [n] │ [auto] │ [auto]│ [X]        │
│ [input] │ [n] │ [auto] │ [auto]│ [X]        │
│         │     │        │       │            │
├──────────────────────────────────────────────┤
│                        SUBTOTAL: R$ 0,00     │
│                        DESCONTO: [input]     │
│                        TOTAL:    R$ 0,00     │
├──────────────────────────────────────────────┤
│ [+ Adicionar linha]  [Importar últimos]      │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 3. DETALHES                                  │
├──────────────────────────────────────────────┤
│ Validade: [date]                             │
│ Observações: [textarea]                      │
│ Desconto: [input] (já acima, remover daqui) │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 4. AÇÕES (buttons)                           │
├──────────────────────────────────────────────┤
│ [← Voltar] [Salvar Rascunho] [Enviar +] [PDF]
└──────────────────────────────────────────────┘

== MELHORIAS IMPLEMENTAR ==

1. ✅ Remover "Status" da criação
2. ✅ Multi-linha para produtos
3. ✅ Autocomplete de produtos
4. ✅ Cálculo de total em tempo real (JavaScript)
5. ✅ Cliente: novo ou existente
6. ✅ Histórico de últimos itens
7. ✅ Importar itens de último orçamento
8. ✅ Gerar PDF direto
9. ✅ Enviar por email
10. ✅ Link público para cliente visualizar

== AUTENTICAÇÃO ==

Novo fluxo:
1. /register/ - Criar conta (usuário novo)
2. /login/ - Entrar (existente)
3. /dashboard/ - Painel (logado)

Se usuário é proprietário → ver gerenciar funcionários
Se funcionário → ver lista de empresas que tem acesso

== PERMISSÕES ==

Proprietário pode:
- Tudo

Funcionário pode:
- Ver clientes
- Ver produtos
- Criar orçamentos
- Editar seus orçamentos
- Não pode: deletar, editar empresa, gerenciar funcionários

== PRÓXIMAS ETAPAS ==

1. ✅ Criar modelo CompanyEmployee
2. ✅ Atualizar autenticação (register/login)
3. ✅ Criar painel de gerenciamento de funcionários
4. ✅ Reformular formulário de orçamento
5. ✅ Adicionar JavaScript para interatividade
6. ✅ Implementar funcionalidade de envio por email
7. ✅ Gerar link público para orçamento

"""
