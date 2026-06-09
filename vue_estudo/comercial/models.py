from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class TimeStampedModel(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CompanyProfile(TimeStampedModel):
    """Perfil de empresa multi-tenant. Cada empresa registrada no sistema tem um proprietário (usuário)."""
    
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="company_profile"
    )
    nome_empresa = models.CharField(max_length=120, blank=True)
    cnpj = models.CharField(max_length=20, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    
    class Meta:
        ordering = ["nome_empresa"]
    
    def __str__(self):
        return self.nome_empresa


class Subscription(TimeStampedModel):
    """Modelo para gerenciar assinaturas e pagamentos de cada empresa."""
    
    company = models.OneToOneField(
        CompanyProfile, 
        on_delete=models.CASCADE, 
        related_name="subscription"
    )
    pago = models.BooleanField(default=True)
    data_pagamento = models.DateTimeField(default=timezone.now)
    proximo_pagamento = models.DateTimeField(blank=True, null=True)
    meio_pagamento = models.CharField(max_length=40, blank=True)
    valor_mensalidade = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    # Campos para futuro: meio de pagamento, cartão, etc.
    
    class Meta:
        ordering = ["-data_pagamento"]
    
    def save(self, *args, **kwargs):
        # Auto-preencher próximo pagamento se não estiver definido
        if not self.proximo_pagamento:
            self.proximo_pagamento = self.data_pagamento + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "Pago" if self.pago else "Pendente"
        return f"{self.company} - {status}"


class CompanyEmployee(TimeStampedModel):
    """
    Funcionários/Colaboradores de uma empresa.
    Permite que múltiplos usuários acessem e gerenciem a empresa.
    """
    ROLES = [
        ('owner', 'Proprietário'),
        ('manager', 'Gerente'),
        ('employee', 'Funcionário'),
    ]
    
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='employees'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_employees'
    )
    role = models.CharField(max_length=20, choices=ROLES, default='employee')
    ativo = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['company', 'user']
        ordering = ['-criado_em']
    
    def is_owner(self):
        return self.role == 'owner'
    
    def is_manager(self):
        return self.role in ['owner', 'manager']
    
    def can_create_orcamento(self):
        return self.ativo
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.nome_empresa} ({self.get_role_display()})"


class Cliente(TimeStampedModel):
    company = models.ForeignKey(
        CompanyProfile, 
        on_delete=models.CASCADE, 
        related_name="clientes",
        null=True,
        blank=True
    )
    nome_completo = models.CharField(max_length=120)
    cpf = models.CharField(max_length=14, blank=True)
    email = models.EmailField(max_length=120, blank=True)
    endereco_residencial = models.CharField(max_length=255, blank=True)
    celular = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["nome_completo"]
        unique_together = ["company", "cpf"]  # CPF único por empresa
    
    def __str__(self):
        return self.nome_completo


class Marca(TimeStampedModel):
    company = models.ForeignKey(
        CompanyProfile, 
        on_delete=models.CASCADE, 
        related_name="marcas",
        null=True,
        blank=True
    )
    nome = models.CharField(max_length=80)

    class Meta:
        ordering = ["nome"]
        unique_together = ["company", "nome"]  # Nome único por empresa

    def __str__(self):
        return self.nome


class Produto(TimeStampedModel):
    TIPOS = [
        ("produto", "Produto"),
        ("servico", "Serviço"),
    ]
    UNIDADES = [
        ("un", "Unidade"),
        ("lt", "Litros"),
        ("m", "Metro"),
        ("m2", "Metro quadrado"),
        ("kg", "Quilo"),
        ("h", "Hora"),
        ("diaria", "Diária"),
    ]

    company = models.ForeignKey(
        CompanyProfile, 
        on_delete=models.CASCADE, 
        related_name="produtos",
        null=True,
        blank=True
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default="produto")
    nome = models.CharField(max_length=120)
    marca = models.ForeignKey(
        Marca, 
        on_delete=models.PROTECT, 
        related_name="produtos",
        null=True,
        blank=True
    )
    disponivel = models.BooleanField(default=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    estoque_quantidade = models.PositiveIntegerField(default=0, blank=True)
    unidade_medida = models.CharField(max_length=10, choices=UNIDADES, default="un")
    medida = models.CharField(max_length=80, blank=True)
    litros = models.PositiveIntegerField(blank=True, null=True)
    quantidade_profissionais = models.PositiveIntegerField(blank=True, null=True)
    duracao_horas = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        detalhe = f" - {self.litros}L" if self.litros else ""
        if self.tipo == "servico" and self.quantidade_profissionais and self.duracao_horas:
            detalhe = f" - {self.quantidade_profissionais} prof. por {self.duracao_horas}h"
        return f"{self.nome}{detalhe} - R$ {self.valor}"
    
    @property
    def imagens(self):
        """Retorna todas as imagens do produto, ordenadas."""
        return self.product_images.all().order_by("ordem")
    
    @property
    def imagem_principal(self):
        """Retorna a primeira imagem do produto."""
        return self.product_images.first()


class ProductImage(TimeStampedModel):
    """Modelo para armazenar múltiplas imagens de produtos."""
    
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.CASCADE, 
        related_name="product_images"
    )
    imagem = models.ImageField(upload_to="produtos/")
    ordem = models.PositiveIntegerField(default=0)
    descricao = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["ordem", "criado_em"]

    def __str__(self):
        return f"{self.produto} - Imagem {self.ordem}"


class Servico(TimeStampedModel):
    company = models.ForeignKey(
        CompanyProfile, 
        on_delete=models.CASCADE, 
        related_name="servicos",
        null=True,
        blank=True
    )
    nome = models.CharField(max_length=120)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} - R$ {self.valor}"



class ConfiguracaoEmpresa(models.Model):
    """
    Modelo legado mantido por compatibilidade. 
    Use CompanyProfile para novas implementações.
    """
    nome_empresa = models.CharField(max_length=120, default="Dona do Chopp")
    cnpj = models.CharField(max_length=20, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    texto_padrao_orcamento = models.TextField(
        default=(
            "Segue orçamento solicitado para {{nome_cliente}}. "
            "Produtos: {{produtos}}. Serviços: {{servicos}}."
        )
    )

    def __str__(self):
        return self.nome_empresa


class Orcamento(TimeStampedModel):
    STATUS = [
        ("rascunho", "Rascunho"),
        ("enviado", "Enviado"),
        ("aprovado", "Aprovado"),
        ("executado", "Executado"),
        ("cancelado", "Cancelado"),
    ]
    FORMAS_PAGAMENTO = [
        ("dinheiro", "Dinheiro"),
        ("cartao", "Cartão"),
        ("pix", "PIX"),
        ("boleto", "Boleto"),
    ]

    company = models.ForeignKey(
        CompanyProfile, 
        on_delete=models.CASCADE, 
        related_name="orcamentos",
        null=True,
        blank=True
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="orcamentos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    criado_por = models.ForeignKey(
        CompanyEmployee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orcamentos_criados"
    )
    status = models.CharField(max_length=20, choices=STATUS, default="rascunho")
    validade = models.DateField(blank=True, null=True)
    forma_pagamento = models.CharField(max_length=20, choices=FORMAS_PAGAMENTO, default="pix")
    observacoes = models.TextField(blank=True)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    arquivo_pdf = models.FileField(upload_to="orcamentos/", blank=True, null=True)
    link_pubico = models.CharField(max_length=100, unique=True, blank=True, null=True)
    enviado_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-criado_em"]

    @property
    def subtotal_produtos(self):
        return sum((item.total for item in self.itens_produto.all()), Decimal("0.00"))

    @property
    def subtotal_servicos(self):
        return sum((item.total for item in self.itens_servico.all()), Decimal("0.00"))

    @property
    def valor_total(self):
        return self.subtotal_produtos + self.subtotal_servicos - self.desconto

    def get_absolute_url(self):
        return reverse("orcamento_detail", args=[self.pk])

    def __str__(self):
        return f"Orçamento #{self.pk} - {self.cliente}"


class OrcamentoProduto(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name="itens_produto")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self):
        return self.quantidade * self.valor_unitario

    def __str__(self):
        return f"{self.produto} x {self.quantidade}"


class OrcamentoServico(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name="itens_servico")
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self):
        return self.quantidade * self.valor_unitario

    def __str__(self):
        return f"{self.servico} x {self.quantidade}"


class Contrato(TimeStampedModel):
    STATUS = [
        ("rascunho", "Rascunho"),
        ("aguardando_assinatura", "Aguardando assinatura"),
        ("assinado", "Assinado"),
        ("executado", "Executado"),
        ("cancelado", "Cancelado"),
    ]

    company = models.ForeignKey(
        CompanyProfile, 
        on_delete=models.CASCADE, 
        related_name="contratos",
        null=True,
        blank=True
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="contratos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    orcamento = models.ForeignKey(Orcamento, on_delete=models.SET_NULL, blank=True, null=True)
    titulo = models.CharField(max_length=140)
    status = models.CharField(max_length=30, choices=STATUS, default="rascunho")
    documento_modelo = models.FileField(upload_to="documentos/modelos/")
    documento_final = models.FileField(upload_to="documentos/finais/", blank=True, null=True)
    placeholders = models.JSONField(default=list, blank=True)
    valores_preenchidos = models.JSONField(default=dict, blank=True)
    data_assinatura_cliente = models.DateField(blank=True, null=True)
    data_assinatura_usuario = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.titulo} - {self.cliente}"


class Evento(TimeStampedModel):
    STATUS = [
        ("pendente", "Pendente"),
        ("completo", "Completo"),
        ("cancelado", "Cancelado"),
    ]
    BOMBA_OPCOES = [
        ("choppeira_eletrica", "Choppeira Elétrica"),
        ("choppeira_bomba", "Choppeira Bomba"),
    ]

    company = models.ForeignKey(
        CompanyProfile, 
        on_delete=models.CASCADE, 
        related_name="eventos",
        null=True,
        blank=True
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="eventos")
    contrato = models.ForeignKey(Contrato, on_delete=models.SET_NULL, blank=True, null=True, related_name="eventos")
    endereco_evento = models.CharField(max_length=255)
    tipo_evento = models.CharField(max_length=80)
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")
    bomba_opcao = models.CharField(max_length=30, choices=BOMBA_OPCOES, null=True, blank=True)
    profissional = models.BooleanField(default=False)
    data = models.DateField()
    hora = models.TimeField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    forma_pagamento = models.CharField(max_length=20, choices=Orcamento.FORMAS_PAGAMENTO, default="pix")
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["data", "hora"]

    def __str__(self):
        return f"{self.tipo_evento} - {self.data} {self.hora}"



class EventoProduto(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="itens_produto")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.evento} - {self.produto} ({self.quantidade})"


class EventoServico(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="itens_servico")
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.evento} - {self.servico} ({self.quantidade})"
