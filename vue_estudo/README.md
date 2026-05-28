# Gestão Comercial Django

Produto Django para cadastrar clientes, marcas, produtos, serviços, orçamentos, contratos com placeholders `{{campo}}`, eventos e dashboard.

## Rodar localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py createsuperuser
python manage.py runserver
```

Depois acesse `http://127.0.0.1:8000/login/`.

Para abrir o dashboard em Streamlit usando a mesma base:

```bash
streamlit run main.py
```

## Documentos com placeholders

Suba um modelo de contrato com campos como `{{nome}}`, `{{cpf}}`, `{{produto}}` e `{{servico}}`.
O sistema detecta os campos e permite preencher os valores antes de gerar o documento final.

Formatos suportados:

- `.docx`: preserva o layout do Word quando o placeholder está no mesmo trecho de texto.
- `.html` e `.txt`: substitui os campos mantendo o arquivo base.
- `.pdf`: tenta substituir os campos no local usando PyMuPDF.
