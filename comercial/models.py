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
    TIPOS_DOCUMENTO = [
        ("cpf", "CPF"),
        ("cnpj", "CNPJ"),
    ]

    nome_completo = models.CharField(max_length=120)
    tipo_documento = models.CharField(
        max_length=4,
        choices=TIPOS_DOCUMENTO,
        default="cpf",
        verbose_name="Tipo de pessoa",
    )
    documento = models.CharField(max_length=18, unique=True, verbose_name="CPF ou CNPJ")
    email = models.EmailField(max_length=120)
    endereco_residencial = models.CharField(max_length=255)
    celular = models.CharField(max_length=20)

    class Meta:
        ordering = ["nome_completo"]

    @property
    def documento_formatado(self):
        value = "".join(filter(str.isdigit, self.documento))
        if self.tipo_documento == "cpf" and len(value) == 11:
            return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"
        if self.tipo_documento == "cnpj" and len(value) == 14:
            return f"{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}"
        return self.documento

    def __str__(self):
        return self.nome_completo


class Produto(TimeStampedModel):
    nome = models.CharField(max_length=120)
    imagem = models.ImageField(upload_to="produtos/", blank=True, null=True)
    disponivel = models.BooleanField(default=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    estoque_quantidade = models.PositiveIntegerField(default=0)
    litros = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Litros (opcional)",
    )
    descricao = models.TextField(blank=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        detalhe = f" - {self.litros}L" if self.litros else ""
        return f"{self.nome}{detalhe} - R$ {self.valor}"


class Servico(TimeStampedModel):
    nome = models.CharField(max_length=120)
    imagem = models.ImageField(upload_to="servicos/", blank=True, null=True)
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
    FORMAS_PAGAMENTO = [
        ("dinheiro", "Dinheiro"),
        ("cartao", "Cartão"),
        ("pix", "PIX"),
        ("boleto", "Boleto"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="orcamentos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
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

    @property
    def responsavel(self):
        return self.usuario.get_full_name() or self.usuario.get_username()

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
    TIPOS_MODELO = [
        ("chopeira_eletrica", "Chopeira elétrica"),
        ("servico_comodato", "Prestação de serviços e comodato"),
        ("personalizado", "Documento personalizado"),
    ]

    STATUS = [
        ("rascunho", "Rascunho"),
        ("aguardando_assinatura", "Aguardando assinatura"),
        ("assinado", "Assinado / aguardando data"),
        ("executado", "Executado"),
        ("cancelado", "Cancelado"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="contratos")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    orcamento = models.ForeignKey(Orcamento, on_delete=models.SET_NULL, blank=True, null=True)
    titulo = models.CharField(max_length=140)
    status = models.CharField(max_length=30, choices=STATUS, default="rascunho")
    tipo_modelo = models.CharField(max_length=30, choices=TIPOS_MODELO, default="chopeira_eletrica")
    data_evento = models.DateField(blank=True, null=True, verbose_name="Data do contrato/evento")
    endereco_evento = models.CharField(max_length=255, blank=True)
    horario_inicio = models.TimeField(blank=True, null=True)
    horario_fim = models.TimeField(blank=True, null=True)
    com_profissional = models.BooleanField(default=False)
    quantidade_profissionais = models.PositiveSmallIntegerField(default=0)
    valor_hora_extra = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("50.00"))
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    data_pagamento = models.DateField(blank=True, null=True)
    data_vencimento_saldo = models.DateField(blank=True, null=True)
    prazo_chopeira_horas = models.PositiveSmallIntegerField(default=24)
    taxa_nova_instalacao = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("250.00"))
    cidade_assinatura = models.CharField(max_length=80, default="Fortaleza/CE")
    documento_modelo = models.FileField(upload_to="documentos/modelos/", blank=True, null=True)
    documento_final = models.FileField(upload_to="documentos/finais/", blank=True, null=True)
    placeholders = models.JSONField(default=list, blank=True)
    valores_preenchidos = models.JSONField(default=dict, blank=True)
    data_assinatura_cliente = models.DateField(blank=True, null=True)
    data_assinatura_usuario = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ["-data_evento", "-criado_em"]

    @property
    def valor_total(self):
        return self.orcamento.valor_total if self.orcamento else Decimal("0.00")

    @property
    def saldo_pendente(self):
        return max(self.valor_total - self.valor_pago, Decimal("0.00"))

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
