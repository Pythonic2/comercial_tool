from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ClienteForm,
    ConfiguracaoEmpresaForm,
    ContratoForm,
    EventoForm,
    EventoProdutoFormSet,
    EventoServicoFormSet,
    OrcamentoForm,
    OrcamentoProdutoFormSet,
    OrcamentoServicoFormSet,
    PlaceholderValuesForm,
    ProdutoForm,
    ServicoForm,
)
from .models import Cliente, ConfiguracaoEmpresa, Contrato, Evento, Orcamento, Produto, Servico
from .services import (
    extract_placeholders,
    fixed_contract_download_name,
    fixed_contract_template_path,
    gerar_pdf_orcamento,
    has_fixed_contract_template,
    render_document_with_values,
    render_fixed_contract_template,
    render_standard_contract,
)


@login_required
def home(request):
    cards = [
        ("Produtos", "Cadastre produtos, litros opcionais, valores e estoque.", "produto_list", "bi-box-seam"),
        ("Serviços", "Cadastre serviços, descrição e valor.", "servico_list", "bi-tools"),
        ("Orçamentos", "Crie propostas com produtos, serviços e responsável.", "orcamento_list", "bi-receipt"),
        ("Contratos", "Formalize vendas, datas e acompanhe a execução.", "contrato_list", "bi-file-earmark-text"),
        ("Dashboard", "Veja vendas, itens e contratos por situação.", "dashboard", "bi-graph-up"),
    ]
    return render(request, "comercial/home.html", {"cards": cards})


def _filter_contracts_by_period(contratos, periodo, today):
    if periodo == "mes":
        return contratos.filter(data_evento__year=today.year, data_evento__month=today.month)
    if periodo == "semestre":
        start_month = 1 if today.month <= 6 else 7
        end_month = 6 if today.month <= 6 else 12
        return contratos.filter(
            data_evento__year=today.year,
            data_evento__month__gte=start_month,
            data_evento__month__lte=end_month,
        )
    if periodo == "ano":
        return contratos.filter(data_evento__year=today.year)
    return contratos


def _sold_items(contratos):
    items = {}
    for contrato in contratos:
        if not contrato.orcamento:
            continue
        for item in contrato.orcamento.itens_produto.all():
            key = ("Produto", item.produto.nome)
            current = items.setdefault(
                key,
                {"tipo": "Produto", "nome": item.produto.nome, "quantidade": Decimal("0"), "valor": Decimal("0")},
            )
            current["quantidade"] += item.quantidade
            current["valor"] += item.total
        for item in contrato.orcamento.itens_servico.all():
            key = ("Serviço", item.servico.nome)
            current = items.setdefault(
                key,
                {"tipo": "Serviço", "nome": item.servico.nome, "quantidade": Decimal("0"), "valor": Decimal("0")},
            )
            current["quantidade"] += item.quantidade
            current["valor"] += item.total
    return sorted(items.values(), key=lambda item: item["valor"], reverse=True)


@login_required
def dashboard(request):
    status = request.GET.get("status", "")
    periodo = request.GET.get("periodo", "mes")
    today = date.today()

    contratos = (
        Contrato.objects.select_related("cliente", "orcamento", "usuario")
        .prefetch_related(
            "orcamento__itens_produto__produto",
            "orcamento__itens_servico__servico",
        )
    )
    contratos = _filter_contracts_by_period(contratos, periodo, today)
    if status:
        contratos = contratos.filter(status=status)

    executados = list(contratos.filter(status="executado"))
    cancelados = contratos.filter(status="cancelado")
    aguardando = contratos.exclude(status__in=["executado", "cancelado"]).filter(
        Q(data_evento__gte=today) | Q(data_evento__isnull=True)
    )
    atrasados = contratos.exclude(status__in=["executado", "cancelado"]).filter(data_evento__lt=today)
    total_vendido = sum((contrato.valor_total for contrato in executados), Decimal("0.00"))

    context = {
        "periodo": periodo,
        "status": status,
        "total_vendido": total_vendido,
        "contratos_executados": len(executados),
        "contratos_aguardando": aguardando.count(),
        "contratos_atrasados": atrasados.count(),
        "contratos_cancelados": cancelados.count(),
        "aguardando": aguardando[:30],
        "atrasados": atrasados[:30],
        "cancelados": cancelados[:30],
        "itens_vendidos": _sold_items(executados),
    }
    template = "comercial/partials/dashboard_content.html" if request.headers.get("HX-Request") else "comercial/dashboard.html"
    return render(request, template, context)


def _list_create_update(request, model, form_class, template, redirect_name, pk=None):
    instance = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Registro salvo com sucesso.")
        return redirect(redirect_name)
    return render(request, template, {"form": form, "instance": instance})


@login_required
def cliente_list(request):
    return render(request, "comercial/clientes/list.html", {"clientes": Cliente.objects.all()})


@login_required
def cliente_create(request):
    return _list_create_update(request, Cliente, ClienteForm, "comercial/form.html", "cliente_list")


@login_required
def cliente_update(request, pk):
    return _list_create_update(request, Cliente, ClienteForm, "comercial/form.html", "cliente_list", pk)


@login_required
def produto_list(request):
    return render(request, "comercial/produtos/list.html", {"produtos": Produto.objects.all()})


@login_required
def produto_create(request):
    return _list_create_update(request, Produto, ProdutoForm, "comercial/form.html", "produto_list")


@login_required
def produto_update(request, pk):
    return _list_create_update(request, Produto, ProdutoForm, "comercial/form.html", "produto_list", pk)


@login_required
def servico_list(request):
    return render(request, "comercial/servicos/list.html", {"servicos": Servico.objects.all()})


@login_required
def servico_create(request):
    return _list_create_update(request, Servico, ServicoForm, "comercial/form.html", "servico_list")


@login_required
def servico_update(request, pk):
    return _list_create_update(request, Servico, ServicoForm, "comercial/form.html", "servico_list", pk)


@login_required
def orcamento_list(request):
    orcamentos = Orcamento.objects.select_related("cliente", "usuario")
    return render(request, "comercial/orcamentos/list.html", {"orcamentos": orcamentos})


def _save_orcamento(request, instance=None):
    form = OrcamentoForm(request.POST or None, request.FILES or None, instance=instance)
    produto_formset = OrcamentoProdutoFormSet(request.POST or None, instance=instance, prefix="produtos")
    servico_formset = OrcamentoServicoFormSet(request.POST or None, instance=instance, prefix="servicos")
    if request.method == "POST" and form.is_valid() and produto_formset.is_valid() and servico_formset.is_valid():
        orcamento = form.save(commit=False)
        if not orcamento.pk:
            orcamento.usuario = request.user
        orcamento.save()
        produto_formset.instance = orcamento
        servico_formset.instance = orcamento
        produto_formset.save()
        servico_formset.save()
        messages.success(request, "Orçamento salvo com sucesso.")
        return redirect(orcamento)
    return render(
        request,
        "comercial/orcamentos/form.html",
        {
            "form": form,
            "produto_formset": produto_formset,
            "servico_formset": servico_formset,
            "orcamento": instance,
        },
    )


@login_required
def orcamento_create(request):
    return _save_orcamento(request)


@login_required
def orcamento_update(request, pk):
    return _save_orcamento(request, get_object_or_404(Orcamento, pk=pk))


@login_required
def orcamento_detail(request, pk):
    orcamento = get_object_or_404(Orcamento.objects.select_related("cliente", "usuario"), pk=pk)
    return render(request, "comercial/orcamentos/detail.html", {"orcamento": orcamento})


@login_required
def orcamento_pdf(request, pk):
    orcamento = get_object_or_404(Orcamento.objects.select_related("cliente", "usuario"), pk=pk)
    arquivo = gerar_pdf_orcamento(orcamento)
    return FileResponse(arquivo.open("rb"), as_attachment=True, filename=arquivo.name.split("/")[-1])


@login_required
def contrato_list(request):
    contratos = Contrato.objects.select_related("cliente", "usuario", "orcamento")
    return render(request, "comercial/contratos/list.html", {"contratos": contratos})


def _save_contrato(request, instance=None):
    form = ContratoForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        contrato = form.save(commit=False)
        if not contrato.pk:
            contrato.usuario = request.user
        contrato.save()
        if contrato.documento_final:
            contrato.documento_final.delete(save=False)
            contrato.documento_final = None
            contrato.save(update_fields=["documento_final"])
        if contrato.tipo_modelo == "personalizado":
            if contrato.documento_modelo and (
                not instance or "documento_modelo" in form.changed_data
            ):
                contrato.placeholders = extract_placeholders(contrato.documento_modelo.path)
                contrato.save(update_fields=["placeholders"])
            messages.success(request, "Contrato salvo. Preencha os campos do documento.")
            if contrato.placeholders:
                return redirect("contrato_campos", pk=contrato.pk)
        elif has_fixed_contract_template(contrato.tipo_modelo):
            template_path = fixed_contract_template_path(contrato.tipo_modelo)
            contrato.placeholders = extract_placeholders(template_path)
            contrato.valores_preenchidos = {}
            contrato.save(update_fields=["placeholders", "valores_preenchidos"])
            if contrato.placeholders:
                messages.success(request, "Contrato salvo. Preencha os campos do modelo fixo.")
                return redirect("contrato_campos", pk=contrato.pk)
            render_fixed_contract_template(contrato)
            messages.success(request, "Contrato gerado pelo modelo fixo.")
        else:
            contrato.placeholders = []
            contrato.valores_preenchidos = {}
            contrato.save(update_fields=["placeholders", "valores_preenchidos"])
            render_standard_contract(contrato)
            messages.success(request, "Contrato padrão gerado com sucesso.")
        return redirect("contrato_detail", pk=contrato.pk)
    return render(
        request,
        "comercial/contratos/form.html",
        {"form": form, "instance": instance},
    )


@login_required
def contrato_create(request):
    return _save_contrato(request)


@login_required
def contrato_update(request, pk):
    return _save_contrato(request, get_object_or_404(Contrato, pk=pk))


@login_required
def contrato_detail(request, pk):
    contrato = get_object_or_404(Contrato.objects.select_related("cliente", "usuario", "orcamento"), pk=pk)
    context = {
        "contrato": contrato,
        "tem_modelo_original": bool(
            contrato.documento_modelo or has_fixed_contract_template(contrato.tipo_modelo)
        ),
        "tem_documento_final": bool(
            contrato.documento_final or contrato.tipo_modelo != "personalizado"
        ),
    }
    return render(request, "comercial/contratos/detail.html", context)


def _regenerate_contract_if_needed(contrato):
    if contrato.documento_final and contrato.documento_final.storage.exists(contrato.documento_final.name):
        return contrato.documento_final
    if contrato.tipo_modelo == "personalizado":
        if not contrato.documento_modelo:
            raise Http404("Contrato sem documento modelo.")
        return render_document_with_values(contrato)
    if has_fixed_contract_template(contrato.tipo_modelo):
        return render_fixed_contract_template(contrato)
    return render_standard_contract(contrato)


@login_required
def contrato_documento_final(request, pk):
    contrato = get_object_or_404(Contrato.objects.select_related("cliente", "usuario", "orcamento"), pk=pk)
    arquivo = _regenerate_contract_if_needed(contrato)
    return FileResponse(arquivo.open("rb"), as_attachment=True, filename=arquivo.name.split("/")[-1])


@login_required
def contrato_documento_modelo(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    if contrato.tipo_modelo == "personalizado":
        if not contrato.documento_modelo:
            raise Http404("Contrato sem documento modelo.")
        return FileResponse(
            contrato.documento_modelo.open("rb"),
            as_attachment=True,
            filename=contrato.documento_modelo.name.split("/")[-1],
        )

    template_path = fixed_contract_template_path(contrato.tipo_modelo)
    if not template_path or not template_path.exists():
        raise Http404("Modelo fixo nao encontrado.")
    return FileResponse(
        template_path.open("rb"),
        as_attachment=True,
        filename=fixed_contract_download_name(contrato.tipo_modelo) or template_path.name,
    )

@login_required
def contrato_campos(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    if not contrato.placeholders:
        if contrato.tipo_modelo == "personalizado" and contrato.documento_modelo:
            contrato.placeholders = extract_placeholders(contrato.documento_modelo.path)
        elif has_fixed_contract_template(contrato.tipo_modelo):
            contrato.placeholders = extract_placeholders(fixed_contract_template_path(contrato.tipo_modelo))
        contrato.save(update_fields=["placeholders"])
    if not contrato.placeholders:
        messages.info(request, "Este modelo não possui campos editáveis.")
        return redirect("contrato_update", pk=contrato.pk)
    form = PlaceholderValuesForm(contrato.placeholders, request.POST or None, initial=contrato.valores_preenchidos)
    if request.method == "POST" and form.is_valid():
        contrato.valores_preenchidos = form.cleaned_placeholder_values()
        contrato.save(update_fields=["valores_preenchidos"])
        if contrato.tipo_modelo == "personalizado":
            render_document_with_values(contrato)
        else:
            render_fixed_contract_template(contrato)
        messages.success(request, "Documento final gerado.")
        return redirect("contrato_detail", pk=contrato.pk)
    return render(request, "comercial/contratos/campos.html", {"contrato": contrato, "form": form})


@login_required
def evento_list(request):
    eventos = Evento.objects.select_related("cliente", "contrato")
    return render(request, "comercial/eventos/list.html", {"eventos": eventos})


def _save_evento(request, instance=None):
    form = EventoForm(request.POST or None, instance=instance)
    produto_formset = EventoProdutoFormSet(request.POST or None, instance=instance, prefix="produtos")
    servico_formset = EventoServicoFormSet(request.POST or None, instance=instance, prefix="servicos")
    if request.method == "POST" and form.is_valid() and produto_formset.is_valid() and servico_formset.is_valid():
        evento = form.save()
        produto_formset.instance = evento
        servico_formset.instance = evento
        produto_formset.save()
        servico_formset.save()
        messages.success(request, "Evento salvo com sucesso.")
        return redirect("evento_list")
    return render(
        request,
        "comercial/eventos/form.html",
        {
            "form": form,
            "produto_formset": produto_formset,
            "servico_formset": servico_formset,
            "evento": instance,
        },
    )


@login_required
def evento_create(request):
    return _save_evento(request)


@login_required
def evento_update(request, pk):
    return _save_evento(request, get_object_or_404(Evento, pk=pk))


@login_required
def configuracao_empresa(request):
    config, _ = ConfiguracaoEmpresa.objects.get_or_create(pk=1)
    form = ConfiguracaoEmpresaForm(request.POST or None, request.FILES or None, instance=config)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Configuração salva.")
        return redirect("home")
    return render(request, "comercial/form.html", {"form": form, "instance": config})

