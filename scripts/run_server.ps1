<#
.SYNOPSIS
Inicia rápidamente el servidor Flask cuando el entorno ya fue provisionado.

.DESCRIPTION
Activa `.venv`, carga las variables de `.env`, valida que la URI de SQLAlchemy apunte
a PostgreSQL y ejecuta `python -m flask run --debug` escuchando en 127.0.0.1:5000.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Get-DotEnvValues {
    param([string]$Path)

    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path -ErrorAction Stop) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#') -or -not $trimmed.Contains('=')) {
            continue
        }
        $pair = $trimmed.Split('=', 2)
        $key = $pair[0].Trim()
        $value = ''
        if ($pair.Length -gt 1) {
            $value = $pair[1].Trim().Trim('"').Trim("'")
        }
        $values[$key] = $value
    }

    return $values
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path (Join-Path $scriptRoot '..')).Path

Push-Location -LiteralPath $projectRoot
$scriptFailed = $false
try {
    $activatePath = Join-Path $projectRoot '.venv\Scripts\Activate.ps1'
    $venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'

    if (-not (Test-Path -LiteralPath $activatePath)) {
        throw 'No se encontró .venv\Scripts\Activate.ps1. Ejecutá scripts\bootstrap.bat primero.'
    }
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw 'No se encontró .venv\Scripts\python.exe. Ejecutá scripts\bootstrap.bat primero.'
    }

    Write-Info "Activando entorno virtual: $activatePath"
    . $activatePath

    $envPath = Join-Path $projectRoot '.env'
    if (-not (Test-Path -LiteralPath $envPath)) {
        throw 'No se encontró .env. Generá la configuración ejecutando scripts\bootstrap.bat.'
    }

    $envValues = Get-DotEnvValues -Path $envPath
    foreach ($key in $envValues.Keys) {
        Set-Item -Path "Env:$key" -Value $envValues[$key]
    }

    if (-not $envValues.ContainsKey('SQLALCHEMY_DATABASE_URI')) {
        throw 'La variable SQLALCHEMY_DATABASE_URI no está definida en .env.'
    }

    $databaseUri = $envValues['SQLALCHEMY_DATABASE_URI']
    if ($databaseUri -match '^(?i)sqlite') {
        throw "La URI configurada ($databaseUri) apunta a SQLite. Configurá PostgreSQL antes de continuar."
    }

    Write-Info 'Levantando servidor Flask en http://127.0.0.1:5000 (modo debug).'
    & $venvPython -m flask run --host=127.0.0.1 --port=5000 --debug
    if ($LASTEXITCODE -ne 0) {
        throw 'El servidor Flask finalizó con errores.'
    }
}
catch {
    $scriptFailed = $true
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.InnerException) {
        Write-Host "Detalles: $($_.Exception.InnerException.Message)" -ForegroundColor Red
    }
}
finally {
    Pop-Location
}

if ($scriptFailed) {
    exit 1
}
