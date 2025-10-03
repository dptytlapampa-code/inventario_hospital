[CmdletBinding()]
param(
    [string]$Python = "py",
    [switch]$Rebuild
)

$child = Join-Path -Path $PSScriptRoot -ChildPath "scripts/run_dev.ps1"
& $child @PSBoundParameters
