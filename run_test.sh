#!/usr/bin/env bash
# Usage: ./run_test.sh <module-path>
set -euo pipefail
module_file=${1:-}
if [ -z "$module_file" ]; then
  echo "Usage: $0 <module-path>"
  exit 2
fi
PYDIR="$(cd "$(dirname "$0")" && pwd)"
python -u "$PYDIR/tests/run_tests.py" "$module_file"
