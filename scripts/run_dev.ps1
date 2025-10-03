[CmdletBinding()]
param(
    [string]$Python = "py",
    [switch]$Rebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptRoot = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $ScriptRoot
$VenvPath = Join-Path -Path $ProjectRoot -ChildPath ".venv"
$ReqPath = Join-Path -Path $ProjectRoot -ChildPath "requirements.txt"
$DbPath = Join-Path -Path $ProjectRoot -ChildPath "inventario.db"

Write-Host "== Inventario Hospital :: setup y arranque ==" -ForegroundColor Cyan
Write-Host "Tip: Si PowerShell bloquea scripts ejecuta: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" -ForegroundColor Yellow

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$ErrorMessage = "El comando falló"
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$ErrorMessage (código $LASTEXITCODE)."
    }
}

try {
    Write-Host "Verificando intérprete de Python ($Python)..." -ForegroundColor Cyan
    if (-not (Get-Command -Name $Python -ErrorAction SilentlyContinue)) {
        throw "No se encontró el comando '$Python'. Instala Python 3 y asegúrate de que esté en el PATH."
    }

    if (-not (Test-Path -Path $VenvPath)) {
        Write-Host "Creando entorno virtual en $VenvPath..." -ForegroundColor Cyan
        & $Python -m venv $VenvPath
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo crear el entorno virtual (código $LASTEXITCODE)."
        }
    } else {
        Write-Host "Usando entorno virtual existente en $VenvPath." -ForegroundColor DarkGray
    }

    $activateDir = Join-Path -Path $VenvPath -ChildPath "Scripts"
    $activateScript = Join-Path -Path $activateDir -ChildPath "Activate.ps1"
    if (-not (Test-Path -Path $activateScript)) {
        throw "No se encontró el script de activación ($activateScript). Verifica la instalación de Python."
    }

    Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
    . $activateScript

    Push-Location -Path $ProjectRoot
    try {
        Write-Host "Actualizando pip..." -ForegroundColor Cyan
        Invoke-CheckedCommand -FilePath "python" -Arguments @("-m", "pip", "install", "--upgrade", "pip") -ErrorMessage "No se pudo actualizar pip"

        Write-Host "Instalando dependencias desde $ReqPath..." -ForegroundColor Cyan
        Invoke-CheckedCommand -FilePath "python" -Arguments @("-m", "pip", "install", "-r", $ReqPath) -ErrorMessage "La instalación de dependencias falló"

        $env:FLASK_APP = "wsgi.py"
        $env:FLASK_ENV = "development"
        if (-not $env:SQLALCHEMY_DATABASE_URI) {
            $sqlitePath = [IO.Path]::Combine($ProjectRoot, "inventario.db")
            $env:SQLALCHEMY_DATABASE_URI = "sqlite:///$sqlitePath"
        }

        $databaseExisted = Test-Path -Path $DbPath
        if ($Rebuild.IsPresent) {
            Write-Host "Reconstruyendo base de datos desde cero..." -ForegroundColor Yellow
            if (Test-Path -Path $DbPath) {
                Remove-Item -Path $DbPath -Force
            }
            $databaseExisted = $false
        }

        Write-Host "Aplicando migraciones..." -ForegroundColor Cyan
        $headsOutput = & flask db heads 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host $headsOutput -ForegroundColor Yellow
            throw "No se pudo consultar los heads de Alembic (código $LASTEXITCODE)."
        }

        $headIds = @()
        foreach ($line in $headsOutput) {
            $trimmed = $line.Trim()
            if ($trimmed) {
                $firstToken = $trimmed.Split(" ", 2)[0]
                if ($firstToken) {
                    $headIds += $firstToken
                }
            }
        }
        $uniqueHeads = $headIds | Sort-Object -Unique

        if ($uniqueHeads.Count -gt 1) {
            Write-Host "Se detectaron múltiples heads (${($uniqueHeads -join ', ')}). Ejecutando 'flask db upgrade heads'..." -ForegroundColor Yellow
            Invoke-CheckedCommand -FilePath "flask" -Arguments @("db", "upgrade", "heads") -ErrorMessage "No se pudo aplicar 'flask db upgrade heads'"
        } else {
            Invoke-CheckedCommand -FilePath "flask" -Arguments @("db", "upgrade") -ErrorMessage "No se pudo aplicar 'flask db upgrade'"
        }

        $shouldSeed = (-not $databaseExisted) -or $Rebuild.IsPresent
        if ($shouldSeed) {
            Write-Host "Cargando datos de demo..." -ForegroundColor Cyan
            Invoke-CheckedCommand -FilePath "flask" -Arguments @("seed", "demo") -ErrorMessage "La carga de datos demo falló"
        } else {
            Write-Host "La base de datos ya existía. Seeds omitidos." -ForegroundColor DarkGray
        }

        Write-Host "Levantando servidor Flask en http://127.0.0.1:5000 ..." -ForegroundColor Green
        Invoke-CheckedCommand -FilePath "flask" -Arguments @("run", "--host", "127.0.0.1", "--port", "5000") -ErrorMessage "El servidor Flask finalizó con errores"
    }
    finally {
        Pop-Location
    }
}
catch {
    Write-Error $_.Exception.Message
    Write-Host "Tips: usa 'flask db current', 'flask db heads' y 'flask db history' para diagnosticar." -ForegroundColor Yellow
    Write-Host "Si el problema es la política de ejecución: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" -ForegroundColor Yellow
    exit 1
}
