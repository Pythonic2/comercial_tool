from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    ClienteForm,
    CompanyEmployeeForm,
    CompanyProfileForm,
    ConfiguracaoEmpresaForm,
    ContratoForm,
    EventoForm,
    EventoProdutoFormSet,
    EventoServicoFormSet,
    MarcaForm,
    OrcamentoForm,
    PlaceholderValuesForm,
    ProductImageFormSet,
    ProdutoForm,
    ServicoForm,
    SignupForm,
)
from .models import (
    Cliente,
    CompanyEmployee,
    CompanyProfile,
    ConfiguracaoEmpresa,
    Contrato,
    Evento,
    Marca,
    Orcamento,
    Produto,
    Servico,
)
from .services import extract_placeholders, gerar_pdf_orcamento, render_document_with_values


def _current_company(user):
    employee = (
        CompanyEmployee.objects.filter(user=user, ativo=True)
        .select_related("company")
        .order_by("criado_em")
        .first()
    )
    if employee:
        return employee.company

    company, _ = CompanyProfile.objects.get_or_create(owner=user)
    CompanyEmployee.objects.get_or_create(
        company=company,
        user=user,
        defaults={"role": "owner", "ativo": True},
    )
    return company


def _scope_form(form, company):
    if "cliente" in form.fields:
        form.fields["cliente"].queryset = Cliente.objects.filter(company=company)
    if "marca" in form.fields:
        form.fields["marca"].queryset = Marca.objects.filter(company=company)
    if "produto" in form.fields:
        form.fields["produto"].queryset = Produto.objects.filter(company=company, disponivel=True)
    if "servico" in form.fields:
        form.fields["servico"].queryset = Servico.objects.filter(company=company, ativo=True)
    if "orcamento" in form.fields:
        form.fields["orcamento"].queryset = Orcamento.objects.filter(company=company)


def _scope_formset(formset, company):
    for form in formset.forms:
        _scope_form(form, company)


def signup(request):
    user_form = SignupForm(request.POST or None)
    company_form = CompanyProfileForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and user_form.is_valid() and company_form.is_valid():
        user = user_form.save()
        company, _ = CompanyProfile.objects.get_or_create(owner=user)
        company_data = company_form.save(commit=False)
        company.nome_empresa = company_data.nome_empresa
        company.cnpj = company_data.cnpj
        company.telefone = company_data.telefone
        company.email = company_data.email
        company.endereco = company_data.endereco
        if company_data.logo:
            company.logo = company_data.logo
        company.save()
        CompanyEmployee.objects.get_or_create(
            company=company,
            user=user,
            defaults={"role": "owner", "ativo": True},
        )
        auth_login(request, user)
        messages.success(request, "Cadastro criado. Você já pode montar sua empresa e seus orçamentos.")
        return redirect("home")
    return render(request, "registration/signup.html", {"user_form": user_form, "company_form": company_form})


@login_required
def home(request):
    cards = [
        ("Produtos", "Cadastre produtos, marcas, medidas, litros e estoque.", "produto_list", "bi-box-seam"),
        ("Serviços", "Monte serviços com descrição e valor.", "servico_list", "bi-tools"),
        ("Orçamentos", "Crie orçamentos completos com logo, produtos e serviços.", "orcamento_list", "bi-receipt"),
        ("Contratos", "Suba modelos com {{campos}} e gere versões preenchidas.", "contrato_list", "bi-file-earmark-text"),
        ("Eventos", "Controle endereço, data, itens e conclusão do evento.", "evento_list", "bi-calendar-event"),
        ("Dashboard", "Acompanhe vendas, pendências e filtros por período.", "dashboard", "bi-graph-up"),
        ("Funcionários", "Cadastre quem pode acessar e criar orçamentos.", "funcionario_list", "bi-people"),
        ("Empresa", "Configure os dados e a logo exibidos nos orçamentos.", "configuracao_empresa", "bi-building"),
    ]
    return render(request, "comercial/home.html", {"cards": cards})


@login_required
def dashboard(request):
    company = _current_company(request.user)
    status = request.GET.get("status", "")
    periodo = request.GET.get("periodo", "mes")
    today = date.today()

    orcamentos = Orcamento.objects.select_related("cliente").filter(company=company)
    eventos = Evento.objects.select_related("cliente", "contrato").filter(company=company)

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
        "embed_streamlit_dashboard": settings.STREAMLIT_DASHBOARD_URL.startswith("https://"),
    }
    template = "comercial/partials/dashboard_content.html" if request.headers.get("HX-Request") else "comercial/dashboard.html"
    return render(request, template, context)


def _list_create_update(request, model, form_class, template, redirect_name, pk=None):
    company = _current_company(request.user)
    queryset = model.objects.all()
    if any(field.name == "company" for field in model._meta.fields):
        queryset = queryset.filter(company=company)
    instance = get_object_or_404(queryset, pk=pk) if pk else None
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    _scope_form(form, company)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if hasattr(obj, "company_id") and not obj.company_id:
            obj.company = company
        obj.save()
        if hasattr(form, "save_m2m"):
            form.save_m2m()
        messages.success(request, "Registro salvo com sucesso.")
        return redirect(redirect_name)
    return render(request, template, {"form": form, "instance": instance})


@login_required
def cliente_list(request):
    company = _current_company(request.user)
    return render(request, "comercial/clientes/list.html", {"clientes": Cliente.objects.filter(company=company)})


@login_required
def cliente_create(request):
    return _list_create_update(request, Cliente, ClienteForm, "comercial/form.html", "cliente_list")


@login_required
def cliente_update(request, pk):
    return _list_create_update(request, Cliente, ClienteForm, "comercial/form.html", "cliente_list", pk)


@login_required
def marca_list(request):
    company = _current_company(request.user)
    return render(request, "comercial/marcas/list.html", {"marcas": Marca.objects.filter(company=company)})


@login_required
def marca_create(request):
    return _list_create_update(request, Marca, MarcaForm, "comercial/form.html", "marca_list")


@login_required
def produto_list(request):
    company = _current_company(request.user)
    produtos = Produto.objects.filter(company=company).select_related("marca").prefetch_related("product_images")
    return render(request, "comercial/produtos/list.html", {"produtos": produtos})


@login_required
def produto_create(request):
    return _save_produto(request)


@login_required
def produto_update(request, pk):
    return _save_produto(request, pk)


def _save_produto(request, pk=None):
    company = _current_company(request.user)
    queryset = Produto.objects.filter(company=company)
    produto = get_object_or_404(queryset, pk=pk) if pk else None
    form = ProdutoForm(request.POST or None, request.FILES or None, instance=produto)
    _scope_form(form, company)
    image_formset = ProductImageFormSet(request.POST or None, request.FILES or None, instance=produto, prefix="imagens")
    if request.method == "POST" and form.is_valid() and image_formset.is_valid():
        produto = form.save(commit=False)
        produto.company = company
        produto.save()
        image_formset.instance = produto
        image_formset.save()
        messages.success(request, "Produto ou serviço salvo com sucesso.")
        return redirect("produto_list")
    return render(
        request,
        "comercial/produtos/form.html",
        {"form": form, "image_formset": image_formset, "produto": produto},
    )


@login_required
def servico_list(request):
    company = _current_company(request.user)
    return render(request, "comercial/servicos/list.html", {"servicos": Servico.objects.filter(company=company)})


@login_required
def servico_create(request):
    return _list_create_update(request, Servico, ServicoForm, "comercial/form.html", "servico_list")


@login_required
def servico_update(request, pk):
    return _list_create_update(request, Servico, ServicoForm, "comercial/form.html", "servico_list", pk)


@login_required
def orcamento_list(request):
    company = _current_company(request.user)
    orcamentos = Orcamento.objects.filter(company=company).select_related("cliente", "usuario")
    return render(request, "comercial/orcamentos/list.html", {"orcamentos": orcamentos})


def _save_orcamento(request, instance=None):
    company = _current_company(request.user)
    form = OrcamentoForm(request.POST or None, request.FILES or None, instance=instance, company=company)
    _scope_form(form, company)
    if request.method == "POST" and form.is_valid():
        orcamento = form.save(commit=False)
        orcamento.company = company
        if not orcamento.pk:
            orcamento.usuario = request.user
            orcamento.criado_por = CompanyEmployee.objects.filter(company=company, user=request.user).first()
            if not orcamento.logo and company.logo:
                orcamento.logo = company.logo
        orcamento.save()
        form.save_itens(orcamento)
        messages.success(request, "Orçamento salvo com sucesso.")
        return redirect(orcamento)
    return render(request, "comercial/orcamentos/form.html", {"form": form, "orcamento": instance})


@login_required
def orcamento_create(request):
    return _save_orcamento(request)


@login_required
def orcamento_update(request, pk):
    company = _current_company(request.user)
    return _save_orcamento(request, get_object_or_404(Orcamento, pk=pk, company=company))


@login_required
def orcamento_detail(request, pk):
    company = _current_company(request.user)
    orcamento = get_object_or_404(Orcamento.objects.select_related("cliente", "usuario"), pk=pk, company=company)
    return render(request, "comercial/orcamentos/detail.html", {"orcamento": orcamento})


@login_required
def orcamento_pdf(request, pk):
    company = _current_company(request.user)
    orcamento = get_object_or_404(Orcamento, pk=pk, company=company)
    arquivo = gerar_pdf_orcamento(orcamento)
    return FileResponse(arquivo.open("rb"), as_attachment=True, filename=arquivo.name.split("/")[-1])


@login_required
def contrato_list(request):
    company = _current_company(request.user)
    contratos = Contrato.objects.filter(company=company).select_related("cliente", "usuario", "orcamento")
    return render(request, "comercial/contratos/list.html", {"contratos": contratos})


@login_required
def contrato_create(request):
    company = _current_company(request.user)
    form = ContratoForm(request.POST or None, request.FILES or None)
    _scope_form(form, company)
    if request.method == "POST" and form.is_valid():
        contrato = form.save(commit=False)
        contrato.company = company
        contrato.usuario = request.user
        contrato.save()
        contrato.placeholders = extract_placeholders(contrato.documento_modelo.path)
        contrato.save(update_fields=["placeholders"])
        messages.success(request, "Contrato criado. Agora preencha os campos encontrados.")
        return redirect("contrato_campos", pk=contrato.pk)
    return render(request, "comercial/form.html", {"form": form})


@login_required
def contrato_detail(request, pk):
    company = _current_company(request.user)
    contrato = get_object_or_404(Contrato.objects.select_related("cliente", "usuario", "orcamento"), pk=pk, company=company)
    return render(request, "comercial/contratos/detail.html", {"contrato": contrato})


@login_required
def contrato_campos(request, pk):
    company = _current_company(request.user)
    contrato = get_object_or_404(Contrato, pk=pk, company=company)
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
    company = _current_company(request.user)
    eventos = Evento.objects.filter(company=company).select_related("cliente", "contrato")
    return render(request, "comercial/eventos/list.html", {"eventos": eventos})


def _save_evento(request, instance=None):
    company = _current_company(request.user)
    form = EventoForm(request.POST or None, instance=instance)
    produto_formset = EventoProdutoFormSet(request.POST or None, instance=instance, prefix="produtos")
    servico_formset = EventoServicoFormSet(request.POST or None, instance=instance, prefix="servicos")
    _scope_form(form, company)
    _scope_formset(produto_formset, company)
    _scope_formset(servico_formset, company)
    if request.method == "POST" and form.is_valid() and produto_formset.is_valid() and servico_formset.is_valid():
        evento = form.save(commit=False)
        evento.company = company
        evento.save()
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
    company = _current_company(request.user)
    return _save_evento(request, get_object_or_404(Evento, pk=pk, company=company))


@login_required
def configuracao_empresa(request):
    config = _current_company(request.user)
    form = CompanyProfileForm(request.POST or None, request.FILES or None, instance=config)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Dados da empresa salvos.")
        return redirect("home")
    return render(request, "comercial/form.html", {"form": form, "instance": config})


@login_required
def funcionario_list(request):
    company = _current_company(request.user)
    funcionarios = CompanyEmployee.objects.filter(company=company).select_related("user")
    return render(request, "comercial/funcionarios/list.html", {"funcionarios": funcionarios})


@login_required
def funcionario_create(request):
    company = _current_company(request.user)
    form = CompanyEmployeeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save(company=company)
        messages.success(request, "Funcionário cadastrado com acesso ao sistema.")
        return redirect("funcionario_list")
    return render(request, "comercial/form.html", {"form": form})
