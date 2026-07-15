# Deploy do Django no Google Cloud Run

Este deploy publica o Django.

## Configuração sugerida

- Região: southamerica-east1
- CPU: 1
- Memória: 512 MiB
- Concorrência: 20
- Instâncias mínimas: 0
- Instâncias máximas: 1
- Faturamento: baseado em requisições

Use .env.example como referência, mas configure as variáveis no Cloud Run.
Defina DJANGO_ENV=production, DEBUG=false, DB_SSLMODE=require e SERVE_MEDIA=false.
SECRET_KEY e DB_PASSWORD não devem ser salvos no Git.

Para Neon, use DB_SSLMODE=require e DB_SCHEMA=public. O banco deve estar
acessível publicamente pelo Cloud Run.

## Migrations

O container não executa migrations no startup. Antes do deploy, execute
python manage.py migrate e python manage.py createsuperuser apontando para o
PostgreSQL externo, ou use um Cloud Run Job.

## Mídia

WhiteNoise atende apenas os arquivos estáticos. Arquivos gravados em MEDIA_ROOT
são efêmeros no Cloud Run e podem desaparecer ao reiniciar, escalar para zero
ou publicar uma revisão. Não armazene uploads importantes no primeiro teste.
Planeje Google Cloud Storage ou Cloudflare R2 para produção.

## Deploy

    gcloud run deploy ddc-comercial-django --source . --region southamerica-east1 --allow-unauthenticated --memory 512Mi --cpu 1 --min-instances 0 --max-instances 1 --concurrency 20

O Docker Compose é somente local. Nele, o Django fica disponível na porta 8011,
encaminhada para a porta 8080 do Gunicorn.

## Um único arquivo de configuração real

A aplicação lê somente .env. O arquivo .env.example é apenas um modelo e nunca
é carregado. O .env também não entra na imagem Docker.

Para enviar as mesmas variáveis do .env ao Cloud Run, execute:

    .deploy-cloud-run.ps1

O script cria um arquivo temporário fora do projeto, envia as variáveis ao
Cloud Run e apaga o temporário no final.
