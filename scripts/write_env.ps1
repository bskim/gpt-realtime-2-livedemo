$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

$endpoint   = azd env get-value AZURE_OPENAI_ENDPOINT
$deployment = azd env get-value AZURE_OPENAI_DEPLOYMENT

@"
AZURE_OPENAI_ENDPOINT=$endpoint
AZURE_OPENAI_DEPLOYMENT=$deployment
"@ | Set-Content backend\.env -Encoding UTF8

Write-Host "backend/.env written."
