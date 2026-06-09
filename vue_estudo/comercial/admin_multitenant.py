"""
Exemplo de Admin Django Multi-Tenant

Para registrar no Django Admin, adicione ao admin.py:

from django.contrib import admin
from .models import CompanyProfile, Subscription, Cliente, Marca, Produto, ProductImage, Servico
from .admin import (
    CompanyProfileAdmin, SubscriptionInline, ClienteAdmin, ProdutoAdmin,
    MarcaAdmin, ProductImageInline, ServicoAdmin
)

admin.site.register(CompanyProfile, CompanyProfileAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Marca, MarcaAdmin)
admin.site.register(Produto, ProdutoAdmin)
admin.site.register(Servico, ServicoAdmin)
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CompanyProfile, Subscription, Cliente, Marca, Produto, 
    ProductImage, Servico, Orcamento, Contrato, Evento
)


# Inline para Subscription dentro de CompanyProfile
class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ('pago', 'data_pagamento', 'proximo_pagamento', 'valor_mensalidade')
    readonly_fields = ('data_pagamento', 'proximo_pagamento')
    can_delete = False


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    """Admin para CompanyProfile (Empresa)"""
    list_display = ('nome_empresa', 'owner', 'cnpj', 'email', 'logo_preview')
    list_filter = ('criado_em',)
    search_fields = ('nome_empresa', 'cnpj', 'email')
    readonly_fields = ('criado_em', 'atualizado_em', 'logo_preview')
    inlines = [SubscriptionInline]
    
    fieldsets = (
        ('Proprietário', {
            'fields': ('owner',)
        }),
        ('Informações da Empresa', {
            'fields': ('nome_empresa', 'cnpj', 'telefone', 'email', 'endereco')
        }),
        ('Logo', {
            'fields': ('logo', 'logo_preview')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="100" height="100" />',
                obj.logo.url,
            )
        return "Sem logo"
    logo_preview.short_description = "Preview da Logo"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin para Subscription"""
    list_display = ('company', 'pago', 'data_pagamento', 'proximo_pagamento', 'valor_mensalidade')
    list_filter = ('pago', 'criado_em')
    search_fields = ('company__nome_empresa',)
    readonly_fields = ('criado_em', 'atualizado_em', 'data_pagamento')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Admin para Cliente com filtro por company"""
    list_display = ('nome_completo', 'company', 'cpf', 'email', 'celular')
    list_filter = ('company', 'criado_em')
    search_fields = ('nome_completo', 'cpf', 'email')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Empresa', {
            'fields': ('company',)
        }),
        ('Dados do Cliente', {
            'fields': ('nome_completo', 'cpf', 'email', 'endereco_residencial', 'celular')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filtrar por company do usuário"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'company_profile'):
            return qs.filter(company=request.user.company_profile)
        return qs.none()


# Inline para ProductImage dentro de Produto
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('imagem', 'ordem', 'descricao')


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    """Admin para Marca com filtro por company"""
    list_display = ('nome', 'company')
    list_filter = ('company', 'criado_em')
    search_fields = ('nome',)
    readonly_fields = ('criado_em', 'atualizado_em')
    
    def get_queryset(self, request):
        """Filtrar por company do usuário"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'company_profile'):
            return qs.filter(company=request.user.company_profile)
        return qs.none()


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    """Admin para Produto com galeria de imagens"""
    list_display = ('nome', 'company', 'marca', 'valor', 'unidade_medida', 'disponivel')
    list_filter = ('company', 'disponivel', 'criado_em')
    search_fields = ('nome', 'descricao')
    readonly_fields = ('criado_em', 'atualizado_em')
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Empresa', {
            'fields': ('company',)
        }),
        ('Informações do Produto', {
            'fields': ('nome', 'marca', 'valor', 'unidade_medida', 'medida', 'litros')
        }),
        ('Estoque', {
            'fields': ('disponivel', 'estoque_quantidade')
        }),
        ('Descrição', {
            'fields': ('descricao',)
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filtrar por company do usuário"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'company_profile'):
            return qs.filter(company=request.user.company_profile)
        return qs.none()


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    """Admin para Serviço"""
    list_display = ('nome', 'company', 'valor', 'ativo')
    list_filter = ('company', 'ativo', 'criado_em')
    search_fields = ('nome',)
    readonly_fields = ('criado_em', 'atualizado_em')
    
    def get_queryset(self, request):
        """Filtrar por company do usuário"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'company_profile'):
            return qs.filter(company=request.user.company_profile)
        return qs.none()


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    """Admin para Orçamento"""
    list_display = ('__str__', 'company', 'cliente', 'status', 'valor_total')
    list_filter = ('company', 'status', 'criado_em')
    search_fields = ('cliente__nome_completo',)
    readonly_fields = ('criado_em', 'atualizado_em', 'valor_total')
    
    def get_queryset(self, request):
        """Filtrar por company do usuário"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'company_profile'):
            return qs.filter(company=request.user.company_profile)
        return qs.none()


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    """Admin para Contrato"""
    list_display = ('titulo', 'company', 'cliente', 'status', 'criado_em')
    list_filter = ('company', 'status', 'criado_em')
    search_fields = ('titulo', 'cliente__nome_completo')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    def get_queryset(self, request):
        """Filtrar por company do usuário"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'company_profile'):
            return qs.filter(company=request.user.company_profile)
        return qs.none()


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """Admin para Evento"""
    list_display = ('tipo_evento', 'company', 'cliente', 'data', 'status', 'valor_total')
    list_filter = ('company', 'status', 'data')
    search_fields = ('tipo_evento', 'cliente__nome_completo')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    def get_queryset(self, request):
        """Filtrar por company do usuário"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'company_profile'):
            return qs.filter(company=request.user.company_profile)
        return qs.none()
