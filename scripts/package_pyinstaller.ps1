$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "Create the local virtualenv first with scripts/run_dev.ps1."
}

Write-Host "PyInstaller packaging placeholder."
Write-Host "Future command:"
Write-Host ".\.venv\Scripts\python.exe -m PyInstaller --name CingyTechToolKit_Portable --windowed --icon app\assets\icon.ico app\main.py"
