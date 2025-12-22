#!/usr/bin/env bash
set -euo pipefail
FILE="$1"
if [ -z "$FILE" ]; then echo "usage: run_test.sh <file>"; exit 2; fi
SCRIPT_DIR=$(dirname "$0")
python -u "$SCRIPT_DIR/tests/run_test.py" "$FILE"
