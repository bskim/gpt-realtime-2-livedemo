#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ENDPOINT=$(azd env get-value AZURE_OPENAI_ENDPOINT)
DEPLOYMENT=$(azd env get-value AZURE_OPENAI_DEPLOYMENT)

if [[ -z "${ENDPOINT}" || -z "${DEPLOYMENT}" ]]; then
    echo "azd env 에 AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_DEPLOYMENT 가 없습니다." >&2
    echo "  - 'azd env list' / 'azd env select <name>' 으로 환경 확인" >&2
    echo "  - 'azd provision' 으로 재배포" >&2
    exit 1
fi

cat > backend/.env <<EOF
AZURE_OPENAI_ENDPOINT=${ENDPOINT}
AZURE_OPENAI_DEPLOYMENT=${DEPLOYMENT}
EOF

if [[ ! -f backend/.env ]]; then
    echo "backend/.env 생성에 실패했습니다." >&2
    exit 1
fi

echo "backend/.env written. endpoint=${ENDPOINT} deployment=${DEPLOYMENT}"
