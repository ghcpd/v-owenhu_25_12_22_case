# Security audit & fixes for `input.py` ✅

## What I changed / generated

- `input_backup.py` — exact copy of the original, vulnerable file (backup).
- `input.py` — fixed, secure implementation (no hardcoded secrets, input validation, safe I/O).
- `report.json` — structured vulnerability report (findings + fixes).
- `tests/` — unit tests covering vulnerable and fixed behavior:
  - `tests/test_input_backup.py` (verifies vulnerabilities exist)
  - `tests/test_input_fixed.py` (verifies fixes)
- `requirements.txt` — Python dependencies.
- `run_test.sh` / `run_test.bat` — platform test runners.
- `auto_test.py` — automatic environment-detecting test runner that logs to `logs/test_run.log`.
- `setup.sh` — bootstrap (virtualenv + install deps).
- `Dockerfile` — reproducible environment that runs the tests.


## Quick start (Linux/macOS)

1. Create a virtualenv and install deps:
   ```bash
   ./setup.sh
   source .venv/bin/activate
   ```
2. Run all tests:
   ```bash
   ./run_test.sh all
   ```
3. Run automatic tester (detects OS and runs appropriate scripts):
   ```bash
   python auto_test.py
   ```


## Quick start (Windows - PowerShell)

1. Install requirements:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Run tests:
   ```powershell
   .\run_test.bat all
   ```
3. Run automatic tester:
   ```powershell
   python auto_test.py
   ```


## How the tests are organized

- `tests/test_input_backup.py` demonstrates the original issues (SQLi, command injection, secret exfiltration, arbitrary file read).
- `tests/test_input_fixed.py` validates the mitigations (parameterised queries, safe zip creation, allowlist for notify URL, restricted config reads).


## Interpreting logs

- `logs/test_run.log` contains timestamped outputs from `auto_test.py` runs.
- Each test run ends with `TEST PASSED` or `TEST FAILED` and an exit code is returned by `auto_test.py`.


## Notes & recommendations

- Provision secrets via environment variables or a secret manager (do not store them in source control).
- Run the Flask app behind a WSGI server (gunicorn/uvicorn) and do not enable `debug` in production.
- Consider adding input rate-limiting, authentication, and monitoring in front of these endpoints.

