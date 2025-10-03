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

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)] [scriptblock]$Command,
        [Parameter(Mandatory = $true)] [string]$ErrorMessage
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "${ErrorMessage} (código de salida $LASTEXITCODE)."
    }
}

try {
    if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
        throw [System.Management.Automation.CommandNotFoundException]::new(
            "No se encontró '$Python'. Instale Python 3 y agréguelo al PATH."
        )
    }

    $venvPath = Join-Path $projectRoot ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creando entorno virtual en $venvPath ..." -ForegroundColor Cyan
        Invoke-CheckedCommand -Command { & $Python -m venv $venvPath } -ErrorMessage "No se pudo crear el entorno virtual"
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
        Invoke-CheckedCommand -Command { python -m ensurepip --upgrade } -ErrorMessage "No se pudo inicializar pip"
    }

    Write-Host "Actualizando pip..." -ForegroundColor Cyan
    Invoke-CheckedCommand -Command { python -m pip install --upgrade pip } -ErrorMessage "No se pudo actualizar pip"

    Write-Host "Instalando dependencias del proyecto..." -ForegroundColor Cyan
    Invoke-CheckedCommand -Command { python -m pip install -r requirements.txt } -ErrorMessage "No se pudieron instalar las dependencias"

    if (-not $env:FLASK_APP) { $env:FLASK_APP = "wsgi.py" }
    $env:FLASK_ENV = "development"
    if (-not $env:SQLALCHEMY_DATABASE_URI) { $env:SQLALCHEMY_DATABASE_URI = "sqlite:///inventario.db" }

    $seedFlag = Join-Path $projectRoot ".seeded.flag"

    Write-Host "Aplicando migraciones..." -ForegroundColor Cyan
    try {
        Invoke-CheckedCommand -Command { flask db upgrade } -ErrorMessage "La migración falló"
    } catch {
        Write-Host "Sugerencias: ejecute 'flask db heads' y 'flask db history' para diagnosticar conflictos." -ForegroundColor Yellow
        throw
    }

    if (-not (Test-Path $seedFlag)) {
        Write-Host "Ejecutando seed demo (idempotente)..." -ForegroundColor Cyan
        Invoke-CheckedCommand -Command { flask seed demo } -ErrorMessage "La carga de datos demo falló"
        New-Item -ItemType File -Path $seedFlag -Force | Out-Null
    } else {
        Write-Host "Seed demo ya ejecutado anteriormente (se omite)." -ForegroundColor DarkGray
    }

    Write-Host "Levantando servidor en http://127.0.0.1:5000 ..." -ForegroundColor Green
    flask run --host=127.0.0.1 --port=5000
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "El servidor Flask terminó con código de salida $exitCode."
    }
}
catch [System.Management.Automation.CommandNotFoundException] {
    Write-Error $_.Exception.Message
    Write-Host "Descarga Python desde https://www.python.org/downloads/ y repite la ejecución." -ForegroundColor Yellow
    exit 1
}
catch {
    Write-Error $_.Exception.Message
    Write-Host "Para problemas de políticas ejecute: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" -ForegroundColor Yellow
    Write-Host "Si falta SQLite instale el componente 'Optional Feature: SQLite' o revise la instalación de Python." -ForegroundColor Yellow
    exit 1
}
