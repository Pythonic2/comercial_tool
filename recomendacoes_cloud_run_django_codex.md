# Plano de migração do projeto Django para Google Cloud Run

## Objetivo

Publicar inicialmente apenas o site Django no Google Cloud Run, com o menor custo possível, usando PostgreSQL externo e mantendo o projeto preparado para continuar funcionando localmente em Docker.

A arquitetura recomendada para o primeiro teste é:

```text
Usuário
  ↓
Google Cloud Run
  ↓
Django + Gunicorn + WhiteNoise
  ↓
PostgreSQL externo, preferencialmente Neon
```

---

## Decisões principais

### Cloud Run

Configuração recomendada:

```text
Faturamento: Request-based
Escalonamento: automático
Número mínimo de instâncias: 0
Número máximo de instâncias: 1
CPU: 1
Memória: 512 MiB
Concorrência inicial: 20
Região: southamerica-east1
```

Motivos:

- `min-instances=0` permite escalar para zero quando não houver acessos.
- `max-instances=1` ajuda a controlar custos e limita conexões simultâneas no PostgreSQL.
- O modo `Request-based` cobra apenas durante o processamento das requisições.
- Uma única instância é suficiente para o primeiro teste.

---

## Banco de dados

O banco atual está configurado assim:

```python
HOST = "postgres_banco2"
PORT = "5433"
```

Essa configuração funciona somente dentro da rede Docker local.

No Cloud Run:

- o nome `postgres_banco2` não existirá;
- o `docker-compose.yml` não será usado;
- o PostgreSQL deve estar acessível externamente;
- a conexão deve usar SSL.

Para baixo custo, usar inicialmente:

```text
Neon PostgreSQL
```

Evitar Cloud SQL neste primeiro teste porque ele normalmente gera custo fixo mesmo com pouco acesso.

---

## Segurança obrigatória

A senha atual do PostgreSQL e a `SECRET_KEY` foram mantidas diretamente no código.

Antes do deploy:

1. trocar a senha do PostgreSQL;
2. remover todas as credenciais do `settings.py`;
3. não salvar senhas no Git;
4. configurar as credenciais como variáveis de ambiente;
5. posteriormente migrar senhas para o Google Secret Manager.

Nunca reutilizar a senha exposta anteriormente.

---

## `settings.py` recomendado

Substituir a configuração atual por uma versão baseada em variáveis de ambiente:

```python
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(name: str, default: str = "") -> list[str]:
    return [
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    ]


SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost,.run.app,ddccomercialtools.gestcloud.com.br",
)

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "https://*.run.app,https://ddccomercialtools.gestcloud.com.br",
)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "comercial",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "banco2_db"),
        "USER": os.getenv("DB_USER", "banco2_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "sslmode": os.getenv("DB_SSLMODE", "prefer"),
        },
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STORAGES = {
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"
```

---

## Variáveis de ambiente para o Cloud Run

Cadastrar no serviço:

```env
DEBUG=False
SECRET_KEY=GERAR_UMA_CHAVE_FORTE

ALLOWED_HOSTS=.run.app,ddccomercialtools.gestcloud.com.br
CSRF_TRUSTED_ORIGINS=https://*.run.app,https://ddccomercialtools.gestcloud.com.br

DB_NAME=neondb
DB_USER=USUARIO_DO_NEON
DB_PASSWORD=SENHA_DO_NEON
DB_HOST=HOST_DO_NEON
DB_PORT=5432
DB_SSLMODE=require
```

No Neon, a string recebida terá formato parecido com:

```text
postgresql://usuario:senha@host.neon.tech/neondb?sslmode=require
```

Separar essa URL nos campos acima.

---

## Dockerfile recomendado para o Django

Usar uma imagem menor e iniciar diretamente com Gunicorn:

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 4 --timeout 120"]
```

O Cloud Run injeta automaticamente a variável `PORT`.

O container deve escutar em:

```text
0.0.0.0:$PORT
```

Para o primeiro teste, usar:

```text
1 worker
4 threads
timeout de 120 segundos
```

---

## Dependências obrigatórias

Confirmar no `requirements.txt`:

```text
Django
gunicorn
psycopg[binary]
whitenoise
```

Manter também as demais bibliotecas utilizadas pelo projeto.

---

## Sobre o `entrypoint.sh`

Para o primeiro deploy, não depender do `entrypoint.sh`.

Motivos possíveis de falha:

- iniciar na porta `8011`;
- aguardar um PostgreSQL local;
- executar migrations em toda inicialização;
- copiar SQLite;
- carregar dados de demonstração;
- tentar acessar volumes que não existem no Cloud Run.

O Dockerfile deve iniciar o Gunicorn diretamente.

O `entrypoint.sh` pode continuar sendo usado localmente, caso necessário, mas não deve ser obrigatório no primeiro teste do Cloud Run.

---

## Docker Compose local

O Cloud Run não usa o `docker-compose.yml` no deploy simples.

O Compose continua útil no servidor pessoal.

A porta local pode ser mapeada assim:

```yaml
ports:
  - "8011:8080"
```

O Gunicorn escuta internamente em `8080`, enquanto o servidor pessoal continua expondo `8011`.

Exemplo de variáveis locais:

```yaml
environment:
  DEBUG: "False"
  SECRET_KEY: "${SECRET_KEY}"

  ALLOWED_HOSTS: "ddccomercialtools.gestcloud.com.br,127.0.0.1,localhost"
  CSRF_TRUSTED_ORIGINS: "https://ddccomercialtools.gestcloud.com.br"

  DB_NAME: "banco2_db"
  DB_USER: "banco2_user"
  DB_PASSWORD: "${DB_PASSWORD}"
  DB_HOST: "postgres_banco2"
  DB_PORT: "5432"
  DB_SSLMODE: "prefer"
```

Observação:

```text
A porta interna padrão do PostgreSQL geralmente é 5432.
A porta 5433 pode ser apenas o mapeamento externo do host.
```

Dentro da mesma rede Docker, normalmente deve ser usado:

```text
postgres_banco2:5432
```

---

## Arquivos estáticos

Continuar usando WhiteNoise para:

- CSS;
- JavaScript;
- imagens estáticas do projeto.

Configurações:

```python
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

E no build:

```dockerfile
RUN python manage.py collectstatic --noinput
```

---

## Arquivos de mídia e uploads

O diretório:

```python
MEDIA_ROOT = BASE_DIR / "media"
```

não é persistente no Cloud Run.

Uploads realizados no admin podem desaparecer quando:

- o container for reiniciado;
- a instância for encerrada;
- o serviço escalar para zero;
- uma nova revisão for implantada.

Para o primeiro teste:

- arquivos já incluídos na imagem podem ser visualizados;
- não confiar em uploads feitos no Cloud Run;
- evitar cadastrar conteúdo importante.

Para produção, usar posteriormente:

```text
Google Cloud Storage
ou
Cloudflare R2
```

---

## Migrations

Não executar `migrate` automaticamente toda vez que o container iniciar.

Para o primeiro teste, executar localmente apontando para o Neon:

```powershell
$env:DB_NAME="neondb"
$env:DB_USER="USUARIO_DO_NEON"
$env:DB_PASSWORD="SENHA_DO_NEON"
$env:DB_HOST="HOST_DO_NEON"
$env:DB_PORT="5432"
$env:DB_SSLMODE="require"
$env:SECRET_KEY="CHAVE_TEMPORARIA"

python manage.py migrate
python manage.py createsuperuser
```

Depois validar:

```powershell
python manage.py check --deploy
```

---

## Deploy sugerido

Na raiz do projeto, onde estão `Dockerfile` e `manage.py`:

```powershell
gcloud auth login
gcloud config set project ID_DO_PROJETO
```

Habilitar APIs:

```powershell
gcloud services enable `
  run.googleapis.com `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com `
  cloudresourcemanager.googleapis.com
```

Deploy:

```powershell
gcloud run deploy ddc-comercial-django `
  --source . `
  --region southamerica-east1 `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --min-instances 0 `
  --max-instances 1 `
  --concurrency 20
```

As variáveis podem ser cadastradas pelo painel do Cloud Run:

```text
Cloud Run
→ Serviço
→ Editar e implantar nova revisão
→ Contêineres
→ Variáveis e secrets
```

---

## Validação após o deploy

Verificar:

```text
1. A URL pública abre sem erro.
2. O Django responde usando HTTPS.
3. O login funciona.
4. O admin funciona.
5. O banco Neon está acessível.
6. Os arquivos estáticos carregam.
7. Não há erro de CSRF.
8. Não há erro de ALLOWED_HOSTS.
9. O container escuta em $PORT.
10. O serviço usa no máximo uma instância.
```

Comandos úteis:

```powershell
gcloud run services describe ddc-comercial-django `
  --region southamerica-east1
```

Logs:

```powershell
gcloud run services logs read ddc-comercial-django `
  --region southamerica-east1 `
  --limit 100
```

---

## Erros esperados e causas prováveis

### `DisallowedHost`

Adicionar o domínio recebido em:

```env
ALLOWED_HOSTS=.run.app,DOMINIO
```

### Erro CSRF

Adicionar a origem completa com HTTPS em:

```env
CSRF_TRUSTED_ORIGINS=https://*.run.app,https://DOMINIO
```

### Container não escuta na porta correta

Garantir:

```text
gunicorn ... --bind 0.0.0.0:${PORT:-8080}
```

### Erro ao conectar no banco

Verificar:

```text
DB_HOST
DB_PORT=5432
DB_SSLMODE=require
usuário
senha
nome do banco
```

### Arquivos estáticos não aparecem

Verificar:

```text
WhiteNoise no middleware
STATIC_ROOT
collectstatic durante o build
```

### Upload desapareceu

Comportamento esperado do armazenamento efêmero do Cloud Run. Migrar mídia para Cloud Storage ou R2.

---

## Ordem de execução recomendada para o Codex

1. Examinar a estrutura atual do projeto.
2. Localizar `settings.py`, `Dockerfile`, `entrypoint.sh`, `requirements.txt` e `docker-compose.yml`.
3. Remover credenciais fixas do código.
4. Refatorar o banco para variáveis de ambiente.
5. Ajustar `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`.
6. Ajustar o Dockerfile para Gunicorn e `$PORT`.
7. Confirmar dependências.
8. Não remover o funcionamento local no Docker.
9. Ajustar o Compose local para usar a porta interna `8080`.
10. Não executar migrations automaticamente no startup.
11. Criar um `.env.example` sem senhas reais.
12. Atualizar o `.gitignore`.
13. Executar validações locais.
14. Mostrar todas as alterações antes de aplicá-las.

---

## Prompt sugerido para o Codex

```text
Analise este projeto Django e prepare-o para deploy no Google Cloud Run com baixo custo.

Objetivos:
- publicar inicialmente apenas o Django;
- manter compatibilidade com Docker Compose no servidor local;
- usar PostgreSQL externo no Cloud Run;
- usar o PostgreSQL local no Docker Compose;
- usar Gunicorn;
- usar WhiteNoise;
- usar variáveis de ambiente;
- manter min-instances=0 e max-instances=1;
- não executar migrations automaticamente na inicialização;
- não armazenar credenciais no código;
- não quebrar o funcionamento local.

Tarefas:
1. Analise settings.py, Dockerfile, entrypoint.sh, requirements.txt e docker-compose.yml.
2. Remova SECRET_KEY e senha do banco do código.
3. Faça DATABASES usar DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT e DB_SSLMODE.
4. Configure ALLOWED_HOSTS e CSRF_TRUSTED_ORIGINS por variáveis de ambiente.
5. Faça o container escutar em 0.0.0.0:$PORT.
6. Configure Gunicorn com 1 worker, 4 threads e timeout de 120 segundos.
7. Use python:3.13-slim.
8. Execute collectstatic durante o build.
9. Confirme Django, gunicorn, psycopg[binary] e whitenoise no requirements.txt.
10. Ajuste o Compose local para mapear 8011:8080.
11. Use postgres_banco2:5432 somente no ambiente local.
12. Crie um .env.example seguro.
13. Garanta que .env e credenciais estejam no .gitignore.
14. Antes de editar, apresente o plano e os arquivos que serão modificados.
15. Depois, aplique as mudanças e mostre o diff final.
16. Informe os comandos para validar localmente e publicar no Cloud Run.

Considere que os uploads em /app/media não são persistentes no Cloud Run. Não implemente Cloud Storage agora, apenas documente essa limitação.
```

---

## Resultado esperado

Ao final, o projeto deve:

```text
- funcionar localmente com Docker Compose;
- funcionar no Cloud Run;
- conectar ao PostgreSQL por variáveis de ambiente;
- não conter senha no código;
- servir arquivos estáticos com WhiteNoise;
- escutar corretamente na porta do Cloud Run;
- usar uma única instância no primeiro teste;
- estar preparado para migrar uploads para Cloud Storage ou R2 futuramente.
```
