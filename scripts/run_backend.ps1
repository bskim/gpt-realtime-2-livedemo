# venv 활성화 없이 백엔드를 실행하는 헬퍼.
# PowerShell 실행 정책(RemoteSigned 미설정)으로 Activate.ps1 이 차단되는 환경에서도 동작한다.
# 사용: pwsh -ExecutionPolicy Bypass -File scripts\run_backend.ps1
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

$py = Join-Path (Get-Location) 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
    Write-Error "venv 가 없습니다. 먼저 'azd up' 또는 scripts\load_python_env.ps1 을 실행하세요."
}

Push-Location backend
try {
    & $py -m uvicorn main:app --reload --port 8000
}
finally {
    Pop-Location
}
