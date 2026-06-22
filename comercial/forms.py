import re

from django import forms
from django.forms import inlineformset_factory

from .models import (
    Cliente,
    ConfiguracaoEmpresa,
    Contrato,
    Evento,
    EventoProduto,
    EventoServico,
    Orcamento,
    OrcamentoProduto,
    OrcamentoServico,
    Produto,
    Servico,
)


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault("class", "form-control")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class ClienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome_completo",
            "tipo_documento",
            "documento",
            "email",
            "endereco_residencial",
            "celular",
        ]

    def clean_documento(self):
        documento = "".join(character for character in self.cleaned_data["documento"] if character.isdigit())
        tipo = self.cleaned_data.get("tipo_documento")
        tamanho = 11 if tipo == "cpf" else 14
        if len(documento) != tamanho:
            nome = "CPF" if tipo == "cpf" else "CNPJ"
            raise forms.ValidationError(f"{nome} deve conter {tamanho} dígitos.")
        return documento


class ProdutoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "nome",
            "imagem",
            "disponivel",
            "valor",
            "estoque_quantidade",
            "litros",
            "descricao",
        ]
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}


class ServicoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Servico
        fields = ["nome", "imagem", "valor", "descricao", "ativo"]
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}


class OrcamentoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Orcamento
        fields = ["cliente", "validade", "forma_pagamento", "desconto", "logo", "observacoes"]
        widgets = {
            "validade": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class OrcamentoProdutoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = OrcamentoProduto
        fields = ["produto", "quantidade", "valor_unitario"]


class OrcamentoServicoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = OrcamentoServico
        fields = ["servico", "quantidade", "valor_unitario"]


OrcamentoProdutoFormSet = inlineformset_factory(
    Orcamento,
    OrcamentoProduto,
    form=OrcamentoProdutoForm,
    extra=1,
    can_delete=True,
)

OrcamentoServicoFormSet = inlineformset_factory(
    Orcamento,
    OrcamentoServico,
    form=OrcamentoServicoForm,
    extra=1,
    can_delete=True,
)


class ContratoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Contrato
        fields = [
            "tipo_modelo",
            "cliente",
            "orcamento",
            "titulo",
            "status",
            "data_evento",
            "endereco_evento",
            "horario_inicio",
            "horario_fim",
            "com_profissional",
            "quantidade_profissionais",
            "valor_hora_extra",
            "valor_pago",
            "data_pagamento",
            "data_vencimento_saldo",
            "prazo_chopeira_horas",
            "taxa_nova_instalacao",
            "cidade_assinatura",
            "documento_modelo",
            "data_assinatura_cliente",
            "data_assinatura_usuario",
            "observacoes",
        ]
        widgets = {
            "data_evento": forms.DateInput(attrs={"type": "date"}),
            "horario_inicio": forms.TimeInput(attrs={"type": "time"}),
            "horario_fim": forms.TimeInput(attrs={"type": "time"}),
            "data_pagamento": forms.DateInput(attrs={"type": "date"}),
            "data_vencimento_saldo": forms.DateInput(attrs={"type": "date"}),
            "data_assinatura_cliente": forms.DateInput(attrs={"type": "date"}),
            "data_assinatura_usuario": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "documento_modelo": "Preencha somente para o tipo Documento personalizado.",
            "orcamento": "Fornece automaticamente produtos, serviços e valor total.",
            "prazo_chopeira_horas": "Prazo permitido no mesmo endereço após o evento.",
        }

    def clean(self):
        cleaned = super().clean()
        modelo = cleaned.get("tipo_modelo")
        documento = cleaned.get("documento_modelo")
        orcamento = cleaned.get("orcamento")
        cliente = cleaned.get("cliente")
        if modelo == "personalizado" and not documento:
            self.add_error("documento_modelo", "Envie o arquivo DOCX do modelo personalizado.")
        if orcamento and cliente and orcamento.cliente_id != cliente.pk:
            self.add_error("orcamento", "O orçamento selecionado pertence a outro cliente.")
        if cleaned.get("com_profissional") and not cleaned.get("quantidade_profissionais"):
            self.add_error("quantidade_profissionais", "Informe ao menos um profissional.")
        return cleaned


class PlaceholderValuesForm(BootstrapFormMixin, forms.Form):
    def __init__(self, placeholders, *args, **kwargs):
        initial_values = kwargs.get("initial") or {}
        super().__init__(*args, **kwargs)
        for placeholder in placeholders:
            field_name = re.sub(r"[^0-9a-zA-Z_]", "_", placeholder)
            self.fields[field_name] = forms.CharField(
                label=f"{{{{{placeholder}}}}}",
                required=False,
                max_length=255,
            )
            self.fields[field_name].placeholder_key = placeholder
            if placeholder in initial_values:
                self.initial[field_name] = initial_values[placeholder]

    def cleaned_placeholder_values(self):
        return {
            field.placeholder_key: self.cleaned_data.get(name, "")
            for name, field in self.fields.items()
        }


class EventoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            "cliente",
            "contrato",
            "endereco_evento",
            "tipo_evento",
            "status",
            "bomba_opcao",
            "profissional",
            "data",
            "hora",
            "valor_total",
            "forma_pagamento",
            "observacoes",
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "hora": forms.TimeInput(attrs={"type": "time"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class EventoProdutoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EventoProduto
        fields = ["produto", "quantidade"]


class EventoServicoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EventoServico
        fields = ["servico", "quantidade"]


EventoProdutoFormSet = inlineformset_factory(
    Evento,
    EventoProduto,
    form=EventoProdutoForm,
    extra=1,
    can_delete=True,
)

EventoServicoFormSet = inlineformset_factory(
    Evento,
    EventoServico,
    form=EventoServicoForm,
    extra=1,
    can_delete=True,
)


class ConfiguracaoEmpresaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ConfiguracaoEmpresa
        fields = [
            "nome_empresa",
            "cnpj",
            "telefone",
            "email",
            "endereco",
            "logo",
            "texto_padrao_orcamento",
        ]
        widgets = {"texto_padrao_orcamento": forms.Textarea(attrs={"rows": 4})}
