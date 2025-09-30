[CmdletBinding()]
param(
    [Parameter()]
    [string]$Host,

    [Parameter()]
    [int]$Port,

    [switch]$Debug
)

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$originalLocation = Get-Location
Set-Location $projectRoot

try {
    $venvActivate = Join-Path (Join-Path $projectRoot '.venv') 'Scripts/Activate.ps1'
    if (Test-Path $venvActivate) {
        Write-Host "Activating virtual environment from $venvActivate" -ForegroundColor Cyan
        . $venvActivate
    }

    if (-not $env:FLASK_APP) {
        $env:FLASK_APP = 'wsgi.py'
        Write-Host "FLASK_APP not set. Defaulting to $($env:FLASK_APP)." -ForegroundColor Yellow
    }

    $flaskArgs = @('run')

    if ($Host) {
        $flaskArgs += @('--host', $Host)
    }

    if ($Port) {
        $flaskArgs += @('--port', $Port.ToString())
    }

    if ($Debug.IsPresent) {
        $flaskArgs += '--debug'
    }

    Write-Host "Running: flask $($flaskArgs -join ' ')" -ForegroundColor Green
    & flask @flaskArgs
}
finally {
    Set-Location $originalLocation
}
