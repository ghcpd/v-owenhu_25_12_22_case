# Security Audit: input.py

## Overview ✅
This workspace contains:

- `input.py` — **Hardened** version of the original service code (secrets read from env, parameterized SQL, input validation, SSRF protections, safe zipping, auth checks).
- `input_backup.py` — **Backup of the original file** (kept for comparison/tests).
- `report.json` — Structured report of vulnerabilities, severity, and fixes.
- `tests/run_test.py` — Deterministic static checks for known patterns (used by run_test scripts).
- `run_test.sh` / `run_test.bat` — Test wrappers for Linux/macOS and Windows.
- `auto_test.py` — Automatic orchestrator that detects the environment and runs tests for both `input_backup.py` and `input.py`, logging results to `logs/test_run.log`.
- `requirements.txt`, `Dockerfile`, `setup.sh` — Environment replication files.
- `logs/` — Directory where `test_run.log` is written by `auto_test.py`.

## Setup (Linux/macOS) 🔧
1. Create a virtual environment and install dependencies:

   ./setup.sh

2. Export required environment variables (example):

   export PAYMENT_TOKEN="example_token"
   export MAIL_SERVER_KEY="example_mail_key"
   export INTERNAL_AUTH_SECRET="example_internal_secret"
   export ALLOWED_NOTIFY_HOSTS="localhost,127.0.0.1"

3. Run the tests manually:

   ./run_test.sh input_backup.py
   ./run_test.sh input.py

4. Or run the automated tester:

   python auto_test.py

## Setup (Windows) 🪟
- Use Command Prompt / PowerShell to install dependencies (use venv) and set environment variables.
- Run tests:

  run_test.bat input_backup.py
  run_test.bat input.py

- Or run automated tester:

  python auto_test.py

## Docker 🐳
Build and run:

  docker build -t input-audit .
  docker run --rm input-audit

## How tests work 🧪
- `tests/run_test.py` performs static pattern checks for known insecure constructs (hardcoded tokens, MD5 usage, shell=True, SQL interpolation, debug=True).
- `run_test.sh` and `run_test.bat` invoke the above script for a specific Python source file.
- `auto_test.py` runs tests for `input_backup.py` (expected to be vulnerable) and `input.py` (expected to be secure), logs timestamped output to `logs/test_run.log`, and appends a final `TEST PASSED` or `TEST FAILED` line.

## Interpreting logs 📄
Open `logs/test_run.log`. Each run includes timestamps, stdout/stderr, exit code, and final test status lines. `TEST PASSED` indicates `input_backup.py` was detected as vulnerable and `input.py` is secure.

## Notes & Recommendations 💡
- Secrets must be provided via environment variables in production. Do not commit credentials to source control.
- For production deployments consider using a secrets manager (e.g., AWS Secrets Manager, Azure Key Vault) and stricter host allow-lists.
- Implement full authentication/authorization and rate limiting for production services.

