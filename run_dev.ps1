Param(
  [string]$Python="py"
)

$ErrorActionPreference = "Stop"
Write-Host "== Inventario Hospital :: setup y arranque =="

# 1) venv
if (-not (Test-Path ".\.venv")) {
  Write-Host "Creando venv..."
  & $Python -m venv .venv
}
Write-Host "Activando venv..."
. .\.venv\Scripts\Activate.ps1

# 2) pip up + deps
Write-Host "Actualizando pip..."
python -m pip install --upgrade pip
Write-Host "Instalando dependencias..."
python -m pip install -r requirements.txt

# 3) Variables de entorno (si no existen en el ambiente actual)
if (-not $env:FLASK_APP) { $env:FLASK_APP = "wsgi.py" }
if (-not $env:FLASK_ENV) { $env:FLASK_ENV = "development" }
if (-not $env:SQLALCHEMY_DATABASE_URI -and $env:FLASK_ENV -eq "development") {
  $env:SQLALCHEMY_DATABASE_URI = "sqlite:///inventario.db"
}

# 4) Migraciones
Write-Host "Aplicando migraciones..."
flask db upgrade

# 5) Seed demo (idempotente)
Write-Host "Cargando datos de demo..."
flask seed-demo

# 6) Levantar server
Write-Host "Levantando servidor en http://127.0.0.1:5000 ..."
flask run --host=127.0.0.1 --port=5000
