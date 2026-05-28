from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse


class TimeStampedModel(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Cliente(TimeStampedModel):
    nome_completo = models.CharField(max_length=120)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(max_length=120)
    endereco_residencial = models.CharField(max_length=255)
    celular = models.CharField(max_length=20)

    class Meta:
        ordering = ["nome_completo"]

    def __str__(self):
        return self.nome_completo


class Marca(TimeStampedModel):
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Produto(TimeStampedModel):
    UNIDADES = [
        ("un", "Unidade"),
        ("lt", "Litros"),
        ("m", "Metro"),
        ("m2", "Metro quadrado"),
        ("kg", "Quilo"),
    ]

    nome = models.CharField(max_length=120)
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name="produtos")
    disponivel = models.BooleanField(default=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    estoque_quantidade = models.PositiveIntegerField(default=0)
    unidade_medida = models.CharField(max_length=10, choices=UNIDADES, default="un")
    medida = models.CharField(max_length=80, blank=True)
    litros = models.PositiveIntegerField(blank=True, null=True)
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        detalhe = f" - {self.litros}L" if self.litros else ""
        return f"{self.nome}{detalhe} - R$ {self.valor}"


class Servico(TimeStampedModel):
    nome = models.CharField(max_length=120)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField()
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} - R$ {self.valor}"


class ConfiguracaoEmpresa(models.Model):
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

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="orcamentos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS, default="rascunho")
    validade = models.DateField(blank=True, null=True)
    forma_pagamento = models.CharField(max_length=20, choices=FORMAS_PAGAMENTO, default="pix")
    observacoes = models.TextField(blank=True)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    arquivo_pdf = models.FileField(upload_to="orcamentos/", blank=True, null=True)

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
