[CmdletBinding()]
param(
    [string]$Host = '127.0.0.1',
    [int]$Port = 5000,
    [switch]$Debug
)

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot '..')
$originalLocation = Get-Location

function Write-Info([string]$Message) {
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Success([string]$Message) {
    Write-Host $Message -ForegroundColor Green
}

function Write-WarningMessage([string]$Message) {
    Write-Warning $Message
}

function Write-ErrorMessage([string]$Message) {
    Write-Host $Message -ForegroundColor Red
}

function Invoke-LoadDotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return
    }

    foreach ($rawLine in Get-Content $Path) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith('#') -or -not $line.Contains('=')) {
            continue
        }
        $parts = $line.Split('=', 2)
        $key = $parts[0].Trim()
        if (-not $key) {
            continue
        }
        $value = ''
        if ($parts.Length -gt 1) {
            $value = $parts[1].Trim().Trim('"').Trim("'")
        }
        if (-not (Test-Path Env:$key)) {
            Set-Item -Path Env:$key -Value $value
        }
    }
}

try {
    Set-Location $projectRoot

    $venvActivate = Join-Path $projectRoot '.venv/Scripts/Activate.ps1'
    if (Test-Path $venvActivate) {
        Write-Info "Activating virtual environment: $venvActivate"
        . $venvActivate
    }

    $dotenvPath = Join-Path $projectRoot '.env'
    Invoke-LoadDotEnv -Path $dotenvPath

    if (-not $env:FLASK_APP) {
        $env:FLASK_APP = 'wsgi.py'
        Write-WarningMessage 'FLASK_APP no estaba definido. Se usará wsgi.py.'
    }

    if (-not $env:SQLALCHEMY_DATABASE_URI) {
        throw "SQLALCHEMY_DATABASE_URI no está configurada. Editá .env y agregá la cadena de conexión a PostgreSQL."
    }

    $databaseUri = $env:SQLALCHEMY_DATABASE_URI
    if ($databaseUri -match '^(?i)sqlite') {
        Write-ErrorMessage "SQLite no es compatible para este proyecto (URI actual: $databaseUri). Configurá SQLALCHEMY_DATABASE_URI a postgresql://..."
        exit 1
    }

    & python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('psycopg2') else 1)"
    if ($LASTEXITCODE -ne 0) {
        Write-WarningMessage 'psycopg2 no está instalado. Ejecutando "python -m pip install psycopg2-binary~=2.9".'
        & python -m pip install psycopg2-binary~=2.9
        if ($LASTEXITCODE -ne 0) {
            throw 'No se pudo instalar psycopg2-binary.'
        }
    }

    Write-Info 'Actualizando base de datos con flask dbsafe-upgrade...'
    & flask dbsafe-upgrade
    if ($LASTEXITCODE -ne 0) {
        throw 'La actualización de la base de datos falló.'
    }

    $flaskArgs = @('run', '--host', $Host, '--port', $Port.ToString())
    if ($Debug.IsPresent) {
        $flaskArgs += '--debug'
    }

    Write-Success "Iniciando servidor: flask $($flaskArgs -join ' ')"
    & flask @flaskArgs
}
finally {
    Set-Location $originalLocation
}
