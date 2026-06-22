# Gestão Comercial Django

Aplicação Django para clientes CPF/CNPJ, produtos, serviços, orçamentos,
contratos e dashboard de vendas.

## Rodar localmente

    python -m venv venv
    venvScriptsactivate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

Acesse http://127.0.0.1:8000/login/.

O servidor de desenvolvimento aceita HTTP, não HTTPS. HTTPS é terminado pelo
Cloud Run/Cloudflare em produção.

## Fluxo principal

1. Cadastre clientes, produtos e serviços.
2. Crie o orçamento; o usuário autenticado fica registrado como responsável.
3. Gere o PDF com identificação e linha de assinatura do funcionário.
4. Crie um contrato associado ao orçamento, informe data e status.
5. Acompanhe vendas, itens, contratos futuros, atrasados e cancelados no dashboard.

## Contratos com placeholders

Modelos podem conter campos como {{nome_cliente}}, {{documento}}, {{produto}}
e {{valor_total}}.

Formatos suportados: .docx, .html, .txt e .pdf.
