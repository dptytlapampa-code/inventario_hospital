Param(
  [string]$Python = "python"
)

$script = Join-Path $PSScriptRoot "scripts\run_dev.ps1"
Write-Host "Este script fue movido a $script" -ForegroundColor Yellow
& $script -Python $Python
