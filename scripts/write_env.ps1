$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

$endpoint   = azd env get-value AZURE_OPENAI_ENDPOINT
$deployment = azd env get-value AZURE_OPENAI_DEPLOYMENT

if ([string]::IsNullOrWhiteSpace($endpoint) -or [string]::IsNullOrWhiteSpace($deployment)) {
    Write-Error @"
azd env 에 AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_DEPLOYMENT 가 없습니다.
Bicep 배포가 실패했거나 azd env 가 잘못 선택되었을 수 있습니다.
  - 'azd env list' / 'azd env select <name>' 으로 환경 확인
  - 'azd provision' 으로 재배포
이 조건이 먼저 충족되어야 backend/.env 를 만들 수 있습니다.
"@
    exit 1
}

@"
AZURE_OPENAI_ENDPOINT=$endpoint
AZURE_OPENAI_DEPLOYMENT=$deployment
"@ | Set-Content backend\.env -Encoding UTF8

if (-not (Test-Path backend\.env)) {
    Write-Error "backend/.env 생성에 실패했습니다."
    exit 1
}

Write-Host "backend/.env written. endpoint=$endpoint deployment=$deployment"
