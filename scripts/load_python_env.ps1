$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

python -m venv backend\.venv
& backend\.venv\Scripts\pip.exe install --upgrade pip -q
& backend\.venv\Scripts\pip.exe install -r backend\requirements.txt -q
Write-Host "Python environment ready."
