param(
    [string]$Service = "ddc-comercial-django",
    [string]$Region = "southamerica-east1"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$envPath = Join-Path $projectRoot ".env"

if (-not (Test-Path -LiteralPath $envPath)) {
    throw "Arquivo .env não encontrado. Copie .env.example para .env e preencha os valores."
}

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "gcloud não está instalado ou não está disponível no PATH."
}

$variables = [ordered]@{}
foreach ($line in Get-Content -LiteralPath $envPath) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) {
        continue
    }

    $parts = $trimmed.Split("=", 2)
    if ($parts.Count -ne 2) {
        throw "Linha inválida no .env: $line"
    }

    $variables[$parts[0].Trim()] = $parts[1]
}

$required = @(
    "DJANGO_ENV",
    "SECRET_KEY",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_SSLMODE"
)
foreach ($name in $required) {
    if (-not $variables.Contains($name) -or -not $variables[$name]) {
        throw "Variável obrigatória ausente no .env: $name"
    }
}

if ($variables["DJANGO_ENV"] -ne "production") {
    throw "Para Cloud Run, DJANGO_ENV deve ser production."
}

$tempFile = Join-Path ([IO.Path]::GetTempPath()) "cloud-run-env-$([guid]::NewGuid()).json"
try {
    $variables | ConvertTo-Json | Set-Content -LiteralPath $tempFile -Encoding utf8

    $arguments = @(
        "run", "deploy", $Service,
        "--source", $projectRoot,
        "--region", $Region,
        "--allow-unauthenticated",
        "--memory", "512Mi",
        "--cpu", "1",
        "--min-instances", "0",
        "--max-instances", "1",
        "--concurrency", "20",
        "--set-env-vars-file", $tempFile
    )

    & gcloud @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "O deploy falhou com código $LASTEXITCODE."
    }
}
finally {
    if (Test-Path -LiteralPath $tempFile) {
        Remove-Item -LiteralPath $tempFile -Force
    }
}
