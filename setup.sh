#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p configs logs
cat > configs/sample.yaml <<'YAML'
# sample configuration
service: test
YAML

echo "Created virtualenv and installed requirements."
echo "Add the following environment variables before running tests:"
echo "export PAYMENT_TOKEN=example_token"
echo "export MAIL_SERVER_KEY=example_mail_key"
echo "export INTERNAL_AUTH_SECRET=example_internal_secret"
echo "export ALLOWED_NOTIFY_HOSTS=localhost,127.0.0.1"
