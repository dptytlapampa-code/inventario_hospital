[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Username
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $projectRoot

$venvPath = Join-Path $projectRoot ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "No se encontró el entorno virtual. Ejecute primero .\\scripts\\run_dev.ps1" -ForegroundColor Yellow
    exit 1
}

try {
    . $activateScript
    if (-not $env:FLASK_APP) { $env:FLASK_APP = "wsgi.py" }
    if (-not $env:FLASK_ENV) { $env:FLASK_ENV = "development" }
    if (-not $env:SQLALCHEMY_DATABASE_URI) { $env:SQLALCHEMY_DATABASE_URI = "sqlite:///inventario.db" }

    Write-Host "Promoviendo usuario '$Username' al rol Superadmin..." -ForegroundColor Cyan
    flask promote-superadmin --username $Username
    Write-Host "Operación finalizada." -ForegroundColor Green
}
catch {
    Write-Error $_.Exception.Message
    Write-Host "Asegúrese de que el servidor se haya inicializado al menos una vez con scripts\\run_dev.ps1." -ForegroundColor Yellow
    exit 1
}
