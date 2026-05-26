#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ENDPOINT=$(azd env get-value AZURE_OPENAI_ENDPOINT)
DEPLOYMENT=$(azd env get-value AZURE_OPENAI_DEPLOYMENT)

cat > backend/.env <<EOF
AZURE_OPENAI_ENDPOINT=${ENDPOINT}
AZURE_OPENAI_DEPLOYMENT=${DEPLOYMENT}
EOF

echo "backend/.env written."
