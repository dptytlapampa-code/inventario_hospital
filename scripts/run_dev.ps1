[CmdletBinding()]
param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "== Inventario Hospital :: setup y arranque ==" -ForegroundColor Cyan
Write-Host "Si PowerShell bloquea el script ejecute: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" -ForegroundColor Yellow

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $projectRoot

try {
    if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
        throw [System.Management.Automation.CommandNotFoundException]::new("No se encontró '$Python'. Instale Python 3 y agréguelo al PATH.")
    }

    $venvPath = Join-Path $projectRoot ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creando entorno virtual en $venvPath ..." -ForegroundColor Cyan
        & $Python -m venv $venvPath
    } else {
        Write-Host "Usando entorno virtual existente ($venvPath)." -ForegroundColor DarkGray
    }

    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        throw "No se encontró el script de activación ($activateScript). Revise la instalación de Python."
    }

    Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
    . $activateScript

    Write-Host "Verificando pip..." -ForegroundColor Cyan
    try {
        python -m pip --version | Out-Null
    } catch {
        Write-Warning "pip no estaba disponible. Ejecutando ensurepip..."
        python -m ensurepip --upgrade
    }

    Write-Host "Actualizando pip..." -ForegroundColor Cyan
    python -m pip install --upgrade pip

    Write-Host "Instalando dependencias del proyecto..." -ForegroundColor Cyan
    python -m pip install -r requirements.txt

    if (-not $env:FLASK_APP) { $env:FLASK_APP = "wsgi.py" }
    $env:FLASK_ENV = "development"

    $instanceDir = Join-Path $projectRoot "instance"
    if (-not (Test-Path $instanceDir)) {
        New-Item -ItemType Directory -Path $instanceDir | Out-Null
    }

    $candidateDatabases = @(
        Join-Path $instanceDir "inventario.db",
        Join-Path $projectRoot "inventario.db"
    )

    $existingDatabase = $candidateDatabases |
        Where-Object { Test-Path $_ } |
        Select-Object -First 1

    if ($existingDatabase) {
        $databasePath = $existingDatabase
        $isNewDatabase = $false
    } else {
        $databasePath = $candidateDatabases[0]
        $isNewDatabase = $true
    }

    Write-Host "Aplicando migraciones..." -ForegroundColor Cyan
    flask dbsafe-upgrade
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Las migraciones no pudieron aplicarse (código $LASTEXITCODE)."
        Write-Host "Revise el estado con 'flask db current', 'flask db heads' y 'flask db history'." -ForegroundColor Yellow
        Write-Host "Solucione el problema y vuelva a ejecutar scripts/run_dev.ps1." -ForegroundColor Yellow
        throw "La migración falló con código de salida $LASTEXITCODE."
    }

    if ($isNewDatabase) {
        Write-Host "Base de datos nueva detectada. Ejecutando seed demo..." -ForegroundColor Cyan
        flask seed demo
        if ($LASTEXITCODE -ne 0) {
            throw "La carga de datos demo falló con código de salida $LASTEXITCODE."
        }
    } else {
        Write-Host "Base de datos existente detectada en $databasePath. Puede ejecutar 'flask seed demo' manualmente si necesita resembrar." -ForegroundColor DarkGray
    }

    Write-Host "Levantando servidor en http://127.0.0.1:5000 ..." -ForegroundColor Green
    flask run --host=127.0.0.1 --port=5000
    if ($LASTEXITCODE -ne 0) {
        throw "El servidor Flask terminó con código de salida $LASTEXITCODE."
    }
}
catch [System.Management.Automation.CommandNotFoundException] {
    Write-Error $_.Exception.Message
    Write-Host "Descarga Python desde https://www.python.org/downloads/ y repite la ejecución." -ForegroundColor Yellow
    exit 1
}
catch {
    Write-Error $_.Exception.Message
    Write-Host "Recomendaciones: ejecute 'flask db current', 'flask db heads' y 'flask db history' para diagnosticar el estado de Alembic." -ForegroundColor Yellow
    Write-Host "Para problemas de políticas ejecute: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" -ForegroundColor Yellow
    Write-Host "Si falta SQLite instale el componente 'Optional Feature: SQLite' o revise la instalación de Python." -ForegroundColor Yellow
    exit 1
}
