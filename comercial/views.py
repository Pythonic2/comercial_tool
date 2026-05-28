from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    ClienteForm,
    ConfiguracaoEmpresaForm,
    ContratoForm,
    EventoForm,
    EventoProdutoFormSet,
    EventoServicoFormSet,
    MarcaForm,
    OrcamentoForm,
    OrcamentoProdutoFormSet,
    OrcamentoServicoFormSet,
    PlaceholderValuesForm,
    ProdutoForm,
    ServicoForm,
)
from .models import Cliente, ConfiguracaoEmpresa, Contrato, Evento, Marca, Orcamento, Produto, Servico
from .services import extract_placeholders, gerar_pdf_orcamento, render_document_with_values


@login_required
def home(request):
    cards = [
        ("Produtos", "Cadastre produtos, marcas, medidas, litros e estoque.", "produto_list", "bi-box-seam"),
        ("Serviços", "Monte serviços com descrição e valor.", "servico_list", "bi-tools"),
        ("Orçamentos", "Crie orçamentos completos com logo, produtos e serviços.", "orcamento_list", "bi-receipt"),
        ("Contratos", "Suba modelos com {{campos}} e gere versões preenchidas.", "contrato_list", "bi-file-earmark-text"),
        ("Eventos", "Controle endereço, data, itens e conclusão do evento.", "evento_list", "bi-calendar-event"),
        ("Dashboard", "Acompanhe vendas, pendências e filtros por período.", "dashboard", "bi-graph-up"),
    ]
    return render(request, "comercial/home.html", {"cards": cards})


@login_required
def dashboard(request):
    status = request.GET.get("status", "")
    periodo = request.GET.get("periodo", "mes")
    today = date.today()

    orcamentos = Orcamento.objects.select_related("cliente").all()
    eventos = Evento.objects.select_related("cliente", "contrato").all()

    if periodo == "mes":
        orcamentos = orcamentos.filter(criado_em__year=today.year, criado_em__month=today.month)
        eventos = eventos.filter(data__year=today.year, data__month=today.month)
    elif periodo == "semestre":
        start_month = 1 if today.month <= 6 else 7
        end_month = 6 if today.month <= 6 else 12
        orcamentos = orcamentos.filter(criado_em__year=today.year, criado_em__month__gte=start_month, criado_em__month__lte=end_month)
        eventos = eventos.filter(data__year=today.year, data__month__gte=start_month, data__month__lte=end_month)
    elif periodo == "ano":
        orcamentos = orcamentos.filter(criado_em__year=today.year)
        eventos = eventos.filter(data__year=today.year)

    if status:
        eventos = eventos.filter(status=status)

    executados = orcamentos.filter(status="executado")
    total_vendido = sum((orcamento.valor_total for orcamento in executados), 0)
    pendentes = orcamentos.exclude(status__in=["executado", "cancelado"])

    context = {
        "periodo": periodo,
        "status": status,
        "total_vendido": total_vendido,
        "orcamentos_executados": executados.count(),
        "orcamentos_pendentes": pendentes.count(),
        "eventos_completos": eventos.filter(status="completo").count(),
        "eventos_pendentes": eventos.exclude(status="completo").count(),
        "eventos": eventos[:30],
        "pendentes": pendentes[:30],
        "streamlit_dashboard_url": settings.STREAMLIT_DASHBOARD_URL,
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
def marca_list(request):
    return render(request, "comercial/marcas/list.html", {"marcas": Marca.objects.all()})


@login_required
def marca_create(request):
    return _list_create_update(request, Marca, MarcaForm, "comercial/form.html", "marca_list")


@login_required
def produto_list(request):
    return render(request, "comercial/produtos/list.html", {"produtos": Produto.objects.select_related("marca")})


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
    return render(request, "comercial/orcamentos/form.html", {"form": form, "produto_formset": produto_formset, "servico_formset": servico_formset, "orcamento": instance})


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
    orcamento = get_object_or_404(Orcamento, pk=pk)
    arquivo = gerar_pdf_orcamento(orcamento)
    return FileResponse(arquivo.open("rb"), as_attachment=True, filename=arquivo.name.split("/")[-1])


@login_required
def contrato_list(request):
    contratos = Contrato.objects.select_related("cliente", "usuario", "orcamento")
    return render(request, "comercial/contratos/list.html", {"contratos": contratos})


@login_required
def contrato_create(request):
    form = ContratoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        contrato = form.save(commit=False)
        contrato.usuario = request.user
        contrato.save()
        contrato.placeholders = extract_placeholders(contrato.documento_modelo.path)
        contrato.save(update_fields=["placeholders"])
        messages.success(request, "Contrato criado. Agora preencha os campos encontrados.")
        return redirect("contrato_campos", pk=contrato.pk)
    return render(request, "comercial/form.html", {"form": form})


@login_required
def contrato_detail(request, pk):
    contrato = get_object_or_404(Contrato.objects.select_related("cliente", "usuario", "orcamento"), pk=pk)
    return render(request, "comercial/contratos/detail.html", {"contrato": contrato})


@login_required
def contrato_campos(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    if not contrato.placeholders:
        contrato.placeholders = extract_placeholders(contrato.documento_modelo.path)
        contrato.save(update_fields=["placeholders"])
    form = PlaceholderValuesForm(contrato.placeholders, request.POST or None, initial=contrato.valores_preenchidos)
    if request.method == "POST" and form.is_valid():
        contrato.valores_preenchidos = form.cleaned_placeholder_values()
        contrato.save(update_fields=["valores_preenchidos"])
        render_document_with_values(contrato)
        messages.success(request, "Documento final gerado mantendo o modelo original quando o formato permite.")
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
    return render(request, "comercial/eventos/form.html", {"form": form, "produto_formset": produto_formset, "servico_formset": servico_formset, "evento": instance})


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
