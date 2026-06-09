from django.urls import path

from . import views


urlpatterns = [
    path("cadastro/", views.signup, name="signup"),
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("clientes/", views.cliente_list, name="cliente_list"),
    path("clientes/novo/", views.cliente_create, name="cliente_create"),
    path("clientes/<int:pk>/editar/", views.cliente_update, name="cliente_update"),
    path("marcas/", views.marca_list, name="marca_list"),
    path("marcas/nova/", views.marca_create, name="marca_create"),
    path("produtos/", views.produto_list, name="produto_list"),
    path("produtos/novo/", views.produto_create, name="produto_create"),
    path("produtos/<int:pk>/editar/", views.produto_update, name="produto_update"),
    path("funcionarios/", views.funcionario_list, name="funcionario_list"),
    path("funcionarios/novo/", views.funcionario_create, name="funcionario_create"),
    path("servicos/", views.servico_list, name="servico_list"),
    path("servicos/novo/", views.servico_create, name="servico_create"),
    path("servicos/<int:pk>/editar/", views.servico_update, name="servico_update"),
    path("orcamentos/", views.orcamento_list, name="orcamento_list"),
    path("orcamentos/novo/", views.orcamento_create, name="orcamento_create"),
    path("orcamentos/<int:pk>/", views.orcamento_detail, name="orcamento_detail"),
    path("orcamentos/<int:pk>/editar/", views.orcamento_update, name="orcamento_update"),
    path("orcamentos/<int:pk>/pdf/", views.orcamento_pdf, name="orcamento_pdf"),
    path("contratos/", views.contrato_list, name="contrato_list"),
    path("contratos/novo/", views.contrato_create, name="contrato_create"),
    path("contratos/<int:pk>/", views.contrato_detail, name="contrato_detail"),
    path("contratos/<int:pk>/campos/", views.contrato_campos, name="contrato_campos"),
    path("eventos/", views.evento_list, name="evento_list"),
    path("eventos/novo/", views.evento_create, name="evento_create"),
    path("eventos/<int:pk>/editar/", views.evento_update, name="evento_update"),
    path("configuracao/", views.configuracao_empresa, name="configuracao_empresa"),
]
