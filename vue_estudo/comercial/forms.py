import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

from .models import (
    Cliente,
    CompanyEmployee,
    CompanyProfile,
    ConfiguracaoEmpresa,
    Contrato,
    Evento,
    EventoProduto,
    EventoServico,
    Marca,
    Orcamento,
    OrcamentoProduto,
    OrcamentoServico,
    Produto,
    ProductImage,
    Servico,
    Subscription,
)

User = get_user_model()


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


class CompanyProfileForm(BootstrapFormMixin, forms.ModelForm):
    """Formulário para cadastro e edição de perfil da empresa."""
    
    class Meta:
        model = CompanyProfile
        fields = ["nome_empresa", "cnpj", "telefone", "email", "endereco", "logo"]
        widgets = {
            "endereco": forms.Textarea(attrs={"rows": 2}),
        }


class SignupForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2"]


class CompanyEmployeeForm(BootstrapFormMixin, forms.ModelForm):
    username = forms.CharField(label="Usuário")
    email = forms.EmailField(required=False)
    first_name = forms.CharField(label="Nome", required=False)
    last_name = forms.CharField(label="Sobrenome", required=False)
    password = forms.CharField(label="Senha inicial", widget=forms.PasswordInput)

    class Meta:
        model = CompanyEmployee
        fields = ["username", "email", "first_name", "last_name", "password", "role", "ativo"]

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Já existe um usuário com esse login.")
        return username

    def save(self, company, commit=True):
        user = User(
            username=self.cleaned_data["username"],
            email=self.cleaned_data.get("email", ""),
            first_name=self.cleaned_data.get("first_name", ""),
            last_name=self.cleaned_data.get("last_name", ""),
        )
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            employee = super().save(commit=False)
            employee.company = company
            employee.user = user
            employee.save()
            return employee
        return user


class SubscriptionForm(BootstrapFormMixin, forms.ModelForm):
    """Formulário para gerenciar assinatura da empresa."""
    
    class Meta:
        model = Subscription
        fields = ["pago"]
        widgets = {
            "pago": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ClienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nome_completo", "cpf", "email", "endereco_residencial", "celular"]


class MarcaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nome"]


class ProdutoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "tipo",
            "nome",
            "marca",
            "disponivel",
            "valor",
            "estoque_quantidade",
            "unidade_medida",
            "medida",
            "litros",
            "quantidade_profissionais",
            "duracao_horas",
            "descricao",
        ]
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}


class ProductImageForm(BootstrapFormMixin, forms.ModelForm):
    """Formulário para adicionar imagens aos produtos."""
    
    class Meta:
        model = ProductImage
        fields = ["imagem", "ordem", "descricao"]


ProductImageFormSet = inlineformset_factory(
    Produto,
    ProductImage,
    form=ProductImageForm,
    extra=1,
    can_delete=True,
)


class ServicoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Servico
        fields = ["nome", "valor", "descricao", "ativo"]
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}


class OrcamentoForm(BootstrapFormMixin, forms.ModelForm):
    itens_catalogo = forms.MultipleChoiceField(
        label="Produtos e serviços",
        choices=(),
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 12}),
    )

    class Meta:
        model = Orcamento
        fields = ["cliente", "validade", "forma_pagamento", "desconto", "logo", "observacoes"]
        widgets = {
            "validade": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)
        self.company = company
        self.catalog_map = self._catalog_map()
        self.fields["itens_catalogo"].choices = [
            (key, label) for key, (_, label) in self.catalog_map.items()
        ]
        self.fields["itens_catalogo"].widget.attrs.update(
            {
                "data-item-selector": "true",
                "multiple": "multiple",
            }
        )
        self.fields["itens_catalogo"].help_text = "Selecione um ou mais produtos e serviços. Use Ctrl/Command para múltipla seleção."

        if self.instance and self.instance.pk:
            selected_ids = [f"produto:{pk}" for pk in self.instance.itens_produto.values_list("produto_id", flat=True)]
            selected_ids += [f"servico:{pk}" for pk in self.instance.itens_servico.values_list("servico_id", flat=True)]
            self.fields["itens_catalogo"].initial = selected_ids

    def _catalog_map(self):
        if not self.company:
            return {}
        produtos = Produto.objects.filter(company=self.company, disponivel=True).select_related("marca")
        servicos = Servico.objects.filter(company=self.company, ativo=True)
        catalog = {}
        for item in produtos:
            catalog[f"produto:{item.pk}"] = (item, self.label_from_instance(item))
        for item in servicos:
            catalog[f"servico:{item.pk}"] = (item, self.label_from_instance(item))
        return catalog

    def label_from_instance(self, item):
        descricao = getattr(item, "descricao", "") or ""
        detalhe = ""
        if isinstance(item, Produto):
            if item.litros:
                detalhe = f"{item.litros}L"
            elif item.medida:
                detalhe = item.medida
            elif item.quantidade_profissionais and item.duracao_horas:
                detalhe = f"{item.quantidade_profissionais} prof. por {item.duracao_horas}h"
        elif isinstance(item, Servico) and item.descricao:
            detalhe = item.descricao
        return f"{item.nome} - R$ {item.valor:.2f}" + (f" | {detalhe}" if detalhe else "")

    def clean_itens_catalogo(self):
        itens = self.cleaned_data.get("itens_catalogo", [])
        invalid = [value for value in itens if value not in self.catalog_map]
        if invalid:
            raise forms.ValidationError("Há itens inválidos na seleção.")
        return itens

    def save_itens(self, orcamento):
        selected = self.cleaned_data.get("itens_catalogo", [])
        produto_ids = set()
        servico_ids = set()
        for value in selected:
            item_kind, item_pk = value.split(":", 1)
            if item_kind == "produto":
                produto_ids.add(int(item_pk))
            else:
                servico_ids.add(int(item_pk))

        orcamento.itens_produto.exclude(produto_id__in=produto_ids).delete()
        orcamento.itens_servico.exclude(servico_id__in=servico_ids).delete()

        for value in selected:
            item, _label = self.catalog_map[value]
            item_kind, item_pk = value.split(":", 1)
            quantidade_key = f"quantidade_{item_kind}_{item_pk}"
            quantidade = self.data.get(quantidade_key) or 1
            valor_key = f"valor_{item_kind}_{item_pk}"
            valor_unitario = self.data.get(valor_key) or item.valor

            if item_kind == "produto":
                OrcamentoProduto.objects.update_or_create(
                    orcamento=orcamento,
                    produto=item,
                    defaults={
                        "quantidade": quantidade,
                        "valor_unitario": valor_unitario,
                    },
                )
            else:
                OrcamentoServico.objects.update_or_create(
                    orcamento=orcamento,
                    servico=item,
                    defaults={
                        "quantidade": quantidade,
                        "valor_unitario": valor_unitario,
                    },
                )


class OrcamentoProdutoForm(BootstrapFormMixin, forms.ModelForm):
    valor_unitario = forms.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = OrcamentoProduto
        fields = ["produto", "quantidade", "valor_unitario"]

    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get("produto")
        if produto and not cleaned_data.get("valor_unitario"):
            cleaned_data["valor_unitario"] = produto.valor
        return cleaned_data


class OrcamentoServicoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = OrcamentoServico
        fields = ["servico", "quantidade", "valor_unitario"]


OrcamentoProdutoFormSet = inlineformset_factory(
    Orcamento,
    OrcamentoProduto,
    form=OrcamentoProdutoForm,
    extra=8,
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
            "cliente",
            "orcamento",
            "titulo",
            "status",
            "documento_modelo",
            "data_assinatura_cliente",
            "data_assinatura_usuario",
            "observacoes",
        ]
        widgets = {
            "data_assinatura_cliente": forms.DateInput(attrs={"type": "date"}),
            "data_assinatura_usuario": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


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
        values = {}
        for name, field in self.fields.items():
            values[field.placeholder_key] = self.cleaned_data.get(name, "")
        return values


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
        widgets = {
            "endereco": forms.Textarea(attrs={"rows": 2}),
            "texto_padrao_orcamento": forms.Textarea(attrs={"rows": 3}),
        }
