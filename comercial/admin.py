from django.contrib import admin

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


class OrcamentoProdutoInline(admin.TabularInline):
    model = OrcamentoProduto
    extra = 1


class OrcamentoServicoInline(admin.TabularInline):
    model = OrcamentoServico
    extra = 1


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ["id", "cliente", "responsavel", "valor_total", "criado_em"]
    list_filter = ["forma_pagamento", "criado_em"]
    search_fields = ["cliente__nome_completo", "cliente__documento", "usuario__username"]
    inlines = [OrcamentoProdutoInline, OrcamentoServicoInline]


class EventoProdutoInline(admin.TabularInline):
    model = EventoProduto
    extra = 1


class EventoServicoInline(admin.TabularInline):
    model = EventoServico
    extra = 1


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ["tipo_evento", "cliente", "status", "data", "hora", "valor_total"]
    list_filter = ["status", "data", "forma_pagamento"]
    search_fields = ["cliente__nome_completo", "endereco_evento", "tipo_evento"]
    inlines = [EventoProdutoInline, EventoServicoInline]


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ["titulo", "cliente", "status", "data_evento", "valor_total"]
    list_filter = ["status", "data_evento", "criado_em"]
    search_fields = ["titulo", "cliente__nome_completo", "cliente__documento"]


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "tipo_documento", "documento_formatado", "email"]
    list_filter = ["tipo_documento"]
    search_fields = ["nome_completo", "documento", "email"]


admin.site.register(Produto)
admin.site.register(Servico)
admin.site.register(ConfiguracaoEmpresa)
