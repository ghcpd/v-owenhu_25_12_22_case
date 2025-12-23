#!/usr/bin/env bash
set -euo pipefail
TARGET=${1:-all}

# ensure required env vars for secure tests
export AUTH_SECRET=${AUTH_SECRET:-test_auth_secret}
export PAYMENT_TOKEN=${PAYMENT_TOKEN:-test_payment_token}
export ADMIN_API_KEY=${ADMIN_API_KEY:-test_admin_key}
export ALLOWED_NOTIFY_HOSTS=${ALLOWED_NOTIFY_HOSTS:-localhost,127.0.0.1}

run() {
  echo "Running: $1"
  python -m unittest "$1" -v
}

case "$TARGET" in
  backup)
    run tests.test_input_backup
    ;;
  fixed)
    run tests.test_input_fixed
    ;;
  all)
    run tests.test_input_backup
    run tests.test_input_fixed
    ;;
  *)
    echo "Unknown target: $TARGET" >&2
    exit 2
    ;;
esac
