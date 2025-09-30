<#
.SYNOPSIS
Automatiza el primer arranque de Inventario Hospitalario en Windows 11.

.DESCRIPTION
Este script prepara el entorno local sin necesidad de consola manual: valida Python,
crea/activa `.venv`, instala dependencias, configura `.env`, verifica PostgreSQL,
aplica migraciones, ejecuta el seed y levanta el servidor Flask abriendo el navegador.
Está pensado para ejecutarse vía `scripts\bootstrap.bat` (doble clic) con ExecutionPolicy Bypass.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step {
    param(
        [int]$Number,
        [int]$Total,
        [string]$Message
    )
    Write-Host "`n[Paso $Number/$Total] $Message" -ForegroundColor Cyan
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "    $Message" -ForegroundColor Green
}

function Write-WarningMessage {
    param([string]$Message)
    Write-Host "    $Message" -ForegroundColor Yellow
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "    $Message" -ForegroundColor Red
}

function Get-ProjectRoot {
    $scriptRoot = $null

    if ($PSScriptRoot) {
        $scriptRoot = $PSScriptRoot
    }
    else {
        $scriptPath = $null

        if ($MyInvocation -and $MyInvocation.PSObject.Properties['MyCommand']) {
            $command = $MyInvocation.MyCommand

            if ($command -and $command.PSObject.Properties['Path'] -and $command.Path) {
                $scriptPath = $command.Path
            }
            elseif ($command -and $command.PSObject.Properties['Definition'] -and $command.Definition) {
                $scriptPath = $command.Definition
            }
        }

        if (-not $scriptPath) {
            throw 'No se pudo determinar la ruta del script.'
        }

        $scriptRoot = Split-Path -Parent $scriptPath
    }

    $candidate = Join-Path $scriptRoot '..'
    return (Resolve-Path -LiteralPath $candidate).Path
}

function Get-PythonLauncher {
    $candidates = @('py', 'python')
    foreach ($candidate in $candidates) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $cmd) {
            return $cmd.Path
        }
    }
    return $null
}

function Invoke-WithPython {
    param(
        [string]$Executable,
        [string[]]$PrefixArgs,
        [string[]]$Args
    )
    if ($PrefixArgs) {
        & $Executable @PrefixArgs @Args
    }
    else {
        & $Executable @Args
    }
}

function Ensure-VirtualEnvironment {
    param(
        [string]$ProjectRoot,
        [string]$PythonLauncherPath,
        [string[]]$LauncherArgs
    )

    $venvPath = Join-Path $ProjectRoot '.venv'
    if (-not (Test-Path -LiteralPath $venvPath)) {
        Write-Info 'Creando entorno virtual (.venv)...'
        Invoke-WithPython -Executable $PythonLauncherPath -PrefixArgs $LauncherArgs -Args @('-m', 'venv', $venvPath)
    }
    else {
        Write-Info 'Entorno virtual ya existe, se reutiliza.'
    }

    $activatePath = Join-Path $venvPath 'Scripts\Activate.ps1'
    if (-not (Test-Path -LiteralPath $activatePath)) {
        throw 'No se encontró el script de activación del entorno virtual (.venv\\Scripts\\Activate.ps1).'
    }

    Write-Info 'Activando entorno virtual...'
    . $activatePath

    $venvPython = Join-Path $venvPath 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "No se encontró $venvPython. Verificá que Python esté instalado correctamente."
    }

    return $venvPython
}

function Install-Requirements {
    param(
        [string]$VenvPython,
        [string]$ProjectRoot
    )

    Write-Info 'Actualizando pip...'
    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo actualizar pip.'
    }

    $requirementsPath = Join-Path $ProjectRoot 'requirements.txt'
    if (-not (Test-Path -LiteralPath $requirementsPath)) {
        Write-WarningMessage 'No se encontró requirements.txt; se omitirá la instalación de dependencias.'
        return
    }

    Write-Info 'Instalando dependencias (requirements.txt)...'
    & $VenvPython -m pip install -r $requirementsPath
    if ($LASTEXITCODE -eq 0) {
        return
    }

    Write-WarningMessage 'La instalación de dependencias falló. Se intentará instalar psycopg2-binary y reintentar.'
    & $VenvPython -m pip install psycopg2-binary
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo instalar psycopg2-binary.'
    }

    & $VenvPython -m pip install -r $requirementsPath
    if ($LASTEXITCODE -ne 0) {
        throw 'La instalación de dependencias desde requirements.txt falló tras reintentar.'
    }
}

function Get-DotEnvValues {
    param([string]$Path)

    $result = @{}
    if (-not (Test-Path -LiteralPath $Path)) {
        return $result
    }

    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#') -or -not $trimmed.Contains('=')) {
            continue
        }
        $parts = $trimmed.Split('=', 2)
        $key = $parts[0].Trim()
        $value = ''
        if ($parts.Length -gt 1) {
            $value = $parts[1].Trim().Trim('"').Trim("'")
        }
        $result[$key] = $value
    }

    return $result
}

function Ensure-DotEnv {
    param(
        [string]$ProjectRoot
    )

    $envPath = Join-Path $ProjectRoot '.env'
    if (-not (Test-Path -LiteralPath $envPath)) {
        Write-Info 'Creando archivo .env con datos provistos por el usuario.'
        $defaultHost = 'localhost'
        $defaultDb = 'inventario_hospital'
        $defaultUser = 'salud'
        $defaultPassword = 'Catrilo.20'

        $host = Read-Host "Host de PostgreSQL [$defaultHost]"
        if (-not $host) { $host = $defaultHost }
        $db = Read-Host "Nombre de la base de datos [$defaultDb]"
        if (-not $db) { $db = $defaultDb }
        $user = Read-Host "Usuario [$defaultUser]"
        if (-not $user) { $user = $defaultUser }
        $password = Read-Host "Password [$defaultPassword]"
        if (-not $password) { $password = $defaultPassword }

        $uri = 'postgresql://{0}:{1}@{2}/{3}' -f $user, $password, $host, $db
        $content = @(
            'FLASK_APP=wsgi.py',
            'FLASK_ENV=development',
            "SQLALCHEMY_DATABASE_URI=$uri"
        )
        Set-Content -LiteralPath $envPath -Value $content -Encoding UTF8
        Write-Success "Archivo .env creado en $envPath."
    }
    else {
        Write-Info '.env ya existe. Valores detectados:'
        $values = Get-DotEnvValues -Path $envPath
        foreach ($key in 'FLASK_APP', 'FLASK_ENV', 'SQLALCHEMY_DATABASE_URI') {
            if ($values.ContainsKey($key)) {
                Write-Info "    $key = $($values[$key])"
            }
        }
    }

    return $envPath
}

function Load-DotEnv {
    param([string]$EnvPath)

    $values = Get-DotEnvValues -Path $EnvPath
    foreach ($key in $values.Keys) {
        Set-Item -Path "Env:$key" -Value $values[$key]
    }
    return $values
}

function Test-PostgresConnection {
    param(
        [string]$VenvPython,
        [string]$ConnectionString
    )

    $code = @'
import sys
import psycopg2
from psycopg2 import errors
from urllib.parse import urlparse

uri = sys.argv[1]
parsed = urlparse(uri)
if parsed.scheme not in ('postgresql', 'postgres'):
    print('SCHEME_ERROR')
    sys.exit(4)
if not parsed.path or parsed.path == '/':
    print('NO_DATABASE')
    sys.exit(4)

def connect(dbname):
    kwargs = {
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'dbname': dbname,
    }
    return psycopg2.connect(**kwargs)

try:
    conn = connect(parsed.path.lstrip('/'))
    conn.close()
    print('OK')
    sys.exit(0)
except errors.InvalidCatalogName:
    print('MISSING_DB')
    sys.exit(2)
except psycopg2.OperationalError as exc:
    msg = str(exc)
    if 'does not exist' in msg.lower():
        print('MISSING_DB')
        sys.exit(2)
    print(f'CONNECTION_ERROR:{exc}')
    sys.exit(3)
except Exception as exc:
    print(f'CONNECTION_ERROR:{exc}')
    sys.exit(3)
'@

    $tempFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($tempFile, $code, [System.Text.Encoding]::UTF8)
    try {
        $output = & $VenvPython $tempFile $ConnectionString 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        Remove-Item -LiteralPath $tempFile -ErrorAction SilentlyContinue
    }

    return @{ ExitCode = $exitCode; Output = $output }
}

function Ensure-Database {
    param(
        [string]$VenvPython,
        [string]$ConnectionString
    )

    if (-not $ConnectionString) {
        throw 'SQLALCHEMY_DATABASE_URI no está definido en .env.'
    }

    Write-Info 'Verificando conexión a PostgreSQL...'
    $result = Test-PostgresConnection -VenvPython $VenvPython -ConnectionString $ConnectionString
    $exitCode = $result.ExitCode
    $output = $result.Output
    if ($exitCode -eq 0) {
        Write-Success 'Conexión a PostgreSQL verificada.'
        return
    }

    if ($exitCode -eq 2) {
        Write-WarningMessage 'La base de datos indicada no existe.'
        $choice = Read-Host '¿Deseás crearla ahora? (S/N)'
        if ($choice.ToUpperInvariant() -eq 'S') {
            $creationResult = Invoke-DbCreation -VenvPython $VenvPython -ConnectionString $ConnectionString
            if ($creationResult) {
                Write-Success 'Base de datos creada correctamente.'
                $postCreate = Test-PostgresConnection -VenvPython $VenvPython -ConnectionString $ConnectionString
                if ($postCreate.ExitCode -ne 0) {
                    Write-ErrorMessage ($postCreate.Output -join [Environment]::NewLine)
                    throw 'No se pudo validar la conexión luego de crear la base de datos.'
                }
                Write-Success 'Conexión a PostgreSQL verificada.'
                return
            }
            throw 'No se pudo crear la base de datos.'
        }
        throw 'Base de datos ausente. Abortando.'
    }

    Write-ErrorMessage ($output -join [Environment]::NewLine)
    throw 'No se pudo establecer conexión con PostgreSQL. Verificá host, puerto, credenciales y que el servicio esté activo.'
}

function Invoke-DbCreation {
    param(
        [string]$VenvPython,
        [string]$ConnectionString
    )

    $code = @'
import sys
import psycopg2
from psycopg2 import errors
from urllib.parse import urlparse

uri = sys.argv[1]
parsed = urlparse(uri)
if parsed.scheme not in ('postgresql', 'postgres'):
    print('SCHEME_ERROR')
    sys.exit(4)
if not parsed.path or parsed.path == '/':
    print('NO_DATABASE')
    sys.exit(4)

user = parsed.username
password = parsed.password
host = parsed.hostname or 'localhost'
port = parsed.port or 5432
dbname = parsed.path.lstrip('/')

conn = None
try:
    conn = psycopg2.connect(user=user, password=password, host=host, port=port, dbname='postgres')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (dbname,))
    if cur.fetchone():
        print('EXISTS')
        sys.exit(0)
    cur.execute('CREATE DATABASE "{}"'.format(dbname.replace('"', '""')))
    print('CREATED')
    sys.exit(0)
except Exception as exc:
    print(f'ERROR:{exc}')
    sys.exit(3)
finally:
    if conn:
        conn.close()
'@

    $tempFile = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($tempFile, $code, [System.Text.Encoding]::UTF8)
    try {
        $output = & $VenvPython $tempFile $ConnectionString 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        Remove-Item -LiteralPath $tempFile -ErrorAction SilentlyContinue
    }

    if ($exitCode -eq 0) {
        return $true
    }

    Write-ErrorMessage ($output -join [Environment]::NewLine)
    return $false
}

function Ensure-Migrations {
    param(
        [string]$ProjectRoot,
        [string]$VenvPython
    )

    $migrationsPath = Join-Path $ProjectRoot 'migrations'
    if (-not (Test-Path -LiteralPath $migrationsPath)) {
        Write-WarningMessage 'No se encontró directorio de migraciones. Inicializando...'
        & $VenvPython -m flask db init
        if ($LASTEXITCODE -ne 0) {
            throw 'No se pudo inicializar el directorio de migraciones.'
        }
        & $VenvPython -m flask db migrate -m 'initial'
        if ($LASTEXITCODE -ne 0) {
            throw 'No se pudo generar la migración inicial.'
        }
    }

    Write-Info 'Revisando heads de Alembic...'
    $headsOutput = & $VenvPython -m flask db heads
    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo obtener la lista de heads de Alembic.'
    }

    $heads = @()
    foreach ($line in $headsOutput) {
        $trimmed = $line.Trim()
        if ($trimmed) {
            $heads += $trimmed
        }
    }

    if ($heads.Count -gt 1) {
        Write-WarningMessage "Se detectaron múltiples heads (${($heads -join ', ')}). Se realizará un merge automático."
        & $VenvPython -m flask db merge -m 'merge heads' heads
        if ($LASTEXITCODE -ne 0) {
            throw 'El merge de migraciones falló.'
        }
    }

    Write-Info 'Aplicando migraciones (flask db upgrade)...'
    & $VenvPython -m flask db upgrade
    if ($LASTEXITCODE -ne 0) {
        throw 'La aplicación de migraciones falló.'
    }
}

function Run-Seed {
    param([string]$VenvPython)

    Write-Info 'Ejecutando seeds (python -m seeds.seed)...'
    & $VenvPython -m seeds.seed
    if ($LASTEXITCODE -ne 0) {
        throw 'La ejecución del seed falló.'
    }
}

function Start-FlaskServer {
    param(
        [string]$VenvPython,
        [string]$Host,
        [int]$Port
    )

    Write-Info 'Iniciando servidor Flask...'
    Start-Job -ScriptBlock {
        Start-Sleep -Seconds 3
        Start-Process 'http://127.0.0.1:5000'
    } | Out-Null

    & $VenvPython -m flask run --host=$Host --port=$Port --debug
    if ($LASTEXITCODE -ne 0) {
        throw 'El servidor Flask finalizó con errores.'
    }
}

$projectRoot = Get-ProjectRoot
Push-Location -LiteralPath $projectRoot
$scriptFailed = $false
try {
    $totalSteps = 7

    Write-Step -Number 1 -Total $totalSteps -Message 'Verificando instalación de Python.'
    $pythonLauncher = Get-PythonLauncher
    $launcherArgs = @()
    if ($null -eq $pythonLauncher) {
        throw 'Python no está disponible en el PATH. Descargalo desde https://www.python.org/downloads/windows/ e instalalo antes de continuar.'
    }

    if ((Split-Path -Leaf $pythonLauncher).ToLowerInvariant() -eq 'py.exe') {
        $launcherArgs = @('-3')
    }

    Write-Success "Python detectado: $pythonLauncher"

    Write-Step -Number 2 -Total $totalSteps -Message 'Creando/activando entorno virtual.'
    $venvPython = Ensure-VirtualEnvironment -ProjectRoot $projectRoot -PythonLauncherPath $pythonLauncher -LauncherArgs $launcherArgs

    Write-Step -Number 3 -Total $totalSteps -Message 'Instalando dependencias.'
    Install-Requirements -VenvPython $venvPython -ProjectRoot $projectRoot

    Write-Step -Number 4 -Total $totalSteps -Message 'Configurando variables de entorno (.env).'
    $envPath = Ensure-DotEnv -ProjectRoot $projectRoot
    $envValues = Load-DotEnv -EnvPath $envPath

    $uri = $envValues['SQLALCHEMY_DATABASE_URI']

    Write-Step -Number 5 -Total $totalSteps -Message 'Validando conexión a la base de datos.'
    Ensure-Database -VenvPython $venvPython -ConnectionString $uri

    Write-Step -Number 6 -Total $totalSteps -Message 'Aplicando migraciones y seeds.'
    Ensure-Migrations -ProjectRoot $projectRoot -VenvPython $venvPython
    Run-Seed -VenvPython $venvPython

    Write-Step -Number 7 -Total $totalSteps -Message 'Levantando servidor Flask.'
    Write-Success '✅ Listo: servidor en http://127.0.0.1:5000'
    Start-FlaskServer -VenvPython $venvPython -Host '127.0.0.1' -Port 5000
}
catch {
    $scriptFailed = $true
    $message = $_.Exception.Message
    Write-ErrorMessage "[ERROR] $message"
    if ($_.Exception.InnerException) {
        Write-ErrorMessage "Detalles: $($_.Exception.InnerException.Message)"
    }
}
finally {
    Pop-Location
}

if ($scriptFailed) {
    exit 1
}
