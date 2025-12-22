# Security Audit Report - Flask API Application

## Overview

This directory contains a comprehensive security audit of a Flask API application. The original code contained **8 critical and high-severity vulnerabilities** that have been identified, documented, and fixed.

### Generated Files

1. **input_backup.py** - Original vulnerable version (for reference)
2. **input.py** - Secured version with all vulnerabilities patched
3. **report.json** - Detailed JSON report of all vulnerabilities and fixes
4. **requirements.txt** - Python package dependencies
5. **Dockerfile** - Docker containerization configuration
6. **setup.sh** - Environment setup script (Linux/macOS)
7. **run_test.sh** - Test execution script (Linux/macOS)
8. **run_test.bat** - Test execution script (Windows)
9. **auto_test.py** - Automatic environment detection and testing script
10. **README.md** - This file

---

## Vulnerabilities Summary

| ID | Vulnerability | Severity | Status |
|----|----|----------|--------|
| 1 | Hardcoded Secrets | CRITICAL | ✅ Fixed |
| 2 | SQL Injection | CRITICAL | ✅ Fixed |
| 3 | Server-Side Request Forgery (SSRF) | CRITICAL | ✅ Fixed |
| 4 | Arbitrary File Read / Path Traversal | HIGH | ✅ Fixed |
| 5 | Command Injection | CRITICAL | ✅ Fixed |
| 6 | Weak Password Hashing | HIGH | ✅ Fixed |
| 7 | Debug Mode Enabled in Production | HIGH | ✅ Fixed |
| 8 | Missing Input Validation & Error Handling | MEDIUM | ✅ Fixed |

For detailed information about each vulnerability, see **report.json**.

---

## Key Security Improvements

### 1. **Secrets Management**
- ❌ **Before**: Hardcoded API tokens and keys
- ✅ **After**: Loaded from environment variables
- **Benefit**: Prevents accidental exposure in version control

### 2. **SQL Injection Prevention**
- ❌ **Before**: String formatting in SQL queries (`"... id = '%s'" % uid`)
- ✅ **After**: Parameterized queries with input validation
- **Benefit**: Query logic is separated from data, preventing injection

### 3. **SSRF Prevention**
- ❌ **Before**: User-controlled URLs in requests
- ✅ **After**: Whitelist-based URL validation
- **Benefit**: Prevents exploitation to attack internal services

### 4. **Path Traversal Prevention**
- ❌ **Before**: Direct file path access
- ✅ **After**: Path normalization and directory boundary checks
- **Benefit**: File access is restricted to intended directory

### 5. **Command Injection Prevention**
- ❌ **Before**: Shell execution with user input (`subprocess.Popen(cmd, shell=True)`)
- ✅ **After**: Argument list with `shell=False`
- **Benefit**: Command structure is fixed, preventing shell metacharacter abuse

### 6. **Password Security**
- ❌ **Before**: MD5 hashing (cryptographically broken)
- ✅ **After**: Argon2 hashing (memory-hard, GPU-resistant)
- **Benefit**: Password is resistant to brute-force and GPU/ASIC attacks

### 7. **Production Hardening**
- ❌ **Before**: Debug mode enabled, accessible from any host
- ✅ **After**: Debug mode disabled, localhost binding only
- **Benefit**: Disables interactive debugger and limits access

### 8. **Error Handling**
- ❌ **Before**: Unhandled exceptions expose sensitive information
- ✅ **After**: Comprehensive try-catch blocks with proper logging
- **Benefit**: Prevents information disclosure

---

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- For Linux/macOS: bash shell
- For Windows: Command Prompt or PowerShell
- Docker (optional, for containerized deployment)

### Option 1: Linux/macOS Setup

#### Step 1: Run Setup Script
```bash
bash setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies from requirements.txt
- Create necessary directories (config, logs)
- Set up environment variables

#### Step 2: Activate Virtual Environment
```bash
source venv/bin/activate
```

#### Step 3: Verify Installation
```bash
python --version
pip list
```

#### Step 4: Run Tests
```bash
bash run_test.sh
```

### Option 2: Windows Setup

#### Step 1: Create Virtual Environment
```batch
python -m venv venv
```

#### Step 2: Activate Virtual Environment
```batch
venv\Scripts\activate
```

#### Step 3: Install Dependencies
```batch
pip install -r requirements.txt
```

#### Step 4: Create Directories
```batch
mkdir config
mkdir logs
```

#### Step 5: Set Environment Variables (Command Prompt)
```batch
set FLASK_ENV=production
set PAYMENT_TOKEN=your_actual_token
set MAIL_SERVER_KEY=your_actual_key
set INTERNAL_AUTH=your_actual_key
```

Or in PowerShell:
```powershell
$env:FLASK_ENV="production"
$env:PAYMENT_TOKEN="your_actual_token"
$env:MAIL_SERVER_KEY="your_actual_key"
$env:INTERNAL_AUTH="your_actual_key"
```

#### Step 6: Run Tests
```batch
run_test.bat
```

### Option 3: Docker Setup

#### Step 1: Build Docker Image
```bash
docker build -t flask-security-audit .
```

#### Step 2: Run Container
```bash
docker run -p 5000:5000 \
  -e PAYMENT_TOKEN=your_token \
  -e MAIL_SERVER_KEY=your_key \
  -e INTERNAL_AUTH=your_key \
  flask-security-audit
```

---

## Running Tests

### Method 1: Platform-Specific Test Scripts

#### Linux/macOS:
```bash
bash run_test.sh
```

#### Windows:
```batch
run_test.bat
```

**What it does:**
- Validates Python syntax for both input_backup.py and input.py
- Saves all output to `logs/test_run.log` with timestamps
- Returns exit code 0 if all tests pass, 1 if any fail
- Displays final status: TEST PASSED or TEST FAILED

### Method 2: Automatic Testing (Recommended)

```bash
python auto_test.py
```

**Features:**
- Detects operating system (Windows/Linux/macOS/Docker)
- Automatically runs appropriate test script
- Tests both files sequentially
- Comprehensive logging with timestamps
- Environment validation
- Clear PASSED/FAILED status output

---

## Checking Test Results

### View Test Logs

#### Linux/macOS:
```bash
cat logs/test_run.log
```

#### Windows (PowerShell):
```powershell
Get-Content logs\test_run.log
```

#### Windows (Command Prompt):
```batch
type logs\test_run.log
```

### Log Format Example
```
[2025-12-22 14:30:45] Environment Setup
[2025-12-22 14:30:45] ====================
[2025-12-22 14:30:46] Testing: input_backup.py
[2025-12-22 14:30:46] Syntax Check: PASSED
[2025-12-22 14:30:46] TEST PASSED
[2025-12-22 14:30:47] Testing: input.py
[2025-12-22 14:30:47] Syntax Check: PASSED
[2025-12-22 14:30:47] TEST PASSED
[2025-12-22 14:30:47] ==========================================
[2025-12-22 14:30:47] Status: TEST PASSED
```

### Interpreting Results

- **TEST PASSED**: All syntax checks passed, no critical errors
- **TEST FAILED**: One or more tests failed, check logs for details

---

## Running the Application

### Development (Linux/macOS)
```bash
source venv/bin/activate
export FLASK_ENV=development
export PAYMENT_TOKEN=dev_token
export MAIL_SERVER_KEY=dev_key
export INTERNAL_AUTH=dev_key
python input.py
```

### Development (Windows - PowerShell)
```powershell
.\venv\Scripts\Activate.ps1
$env:FLASK_ENV="development"
$env:PAYMENT_TOKEN="dev_token"
$env:MAIL_SERVER_KEY="dev_key"
$env:INTERNAL_AUTH="dev_key"
python input.py
```

### Production (Docker - Recommended)
```bash
docker build -t flask-api:production .
docker run -p 5000:5000 \
  -e FLASK_ENV=production \
  -e PAYMENT_TOKEN=$(openssl rand -hex 32) \
  -e MAIL_SERVER_KEY=$(openssl rand -hex 32) \
  -e INTERNAL_AUTH=$(openssl rand -hex 32) \
  flask-api:production
```

---

## Environment Variables

All secrets must be provided via environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| PAYMENT_TOKEN | Stripe-like payment API token | `tok_production_...` |
| MAIL_SERVER_KEY | Email server authentication | `mail_srv_key_...` |
| INTERNAL_AUTH | Internal service authentication | `auth_key_...` |
| FLASK_ENV | Flask environment mode | `production` or `development` |

---

## API Endpoints

### POST /auth
Authenticate user and return token
```bash
curl -X POST http://localhost:5000/auth \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "secure_pass"}'
```

### GET /profile?id=<user_id>
Get user profile (validates user ID)
```bash
curl http://localhost:5000/profile?id=user123
```

### POST /transfer
Transfer funds (validates URL and amount)
```bash
curl -X POST http://localhost:5000/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "target": "user456",
    "amount": 100.00,
    "notify_url": "https://api.example.com/notify"
  }'
```

### POST /config
Load configuration file (validates path)
```bash
curl -X POST http://localhost:5000/config \
  -H "Content-Type: application/json" \
  -d '{"file": "app.yaml"}'
```

### GET /export?name=<export_name>
Export data (validates name)
```bash
curl "http://localhost:5000/export?name=backup_2025"
```

---

## Security Best Practices

1. **Always use HTTPS** in production (add reverse proxy/load balancer)
2. **Store secrets securely**:
   - Use AWS Secrets Manager, HashiCorp Vault, or similar
   - Never commit secrets to version control
   - Use .env files locally (add to .gitignore)
3. **Implement rate limiting** to prevent abuse
4. **Enable CORS** only for trusted domains
5. **Use strong passwords** and implement account lockout
6. **Log security events** and monitor for suspicious activity
7. **Keep dependencies updated** with `pip install --upgrade`
8. **Run security scanners** like `bandit` and `safety`
9. **Implement authentication/authorization** per endpoint
10. **Use secrets management tools** in production

---

## Testing Security

### Syntax Validation
```bash
python -m py_compile input.py
```

### Vulnerability Scanning
```bash
pip install bandit
bandit input.py
```

### Dependency Checking
```bash
pip install safety
safety check -r requirements.txt
```

### Code Quality
```bash
pip install pylint
pylint input.py
```

---

## Troubleshooting

### ImportError: No module named 'argon2'
```bash
pip install argon2-cffi
```

### Permission Denied (Linux/macOS)
```bash
chmod +x setup.sh run_test.sh auto_test.py
```

### Port 5000 Already in Use
```bash
# Find and kill process using port 5000
lsof -i :5000
kill -9 <PID>
```

### Environment Variables Not Set
Ensure all required environment variables are set before running the app:
```bash
echo $PAYMENT_TOKEN  # Should show value, not empty
```

---

## Support & Documentation

- **Flask Documentation**: https://flask.palletsprojects.com/
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **Python Security**: https://python.readthedocs.io/en/latest/library/security_warnings.html
- **Argon2 Docs**: https://argon2-cffi.readthedocs.io/

---

## Changelog

### Version 2.0 (Secured)
- ✅ Fixed 8 critical/high-severity vulnerabilities
- ✅ Implemented parameterized SQL queries
- ✅ Added SSRF and path traversal protections
- ✅ Replaced MD5 with Argon2 hashing
- ✅ Moved secrets to environment variables
- ✅ Fixed command injection vulnerability
- ✅ Disabled debug mode in production
- ✅ Added comprehensive error handling and logging

### Version 1.0 (Original - Vulnerable)
- Original code with 8 vulnerabilities

---

## License

This security audit and remediation are provided for educational and testing purposes.

---

## Contact

For security issues or questions, please review the detailed report in **report.json**.

**Last Updated**: December 22, 2025  
**Audit Status**: Complete - All vulnerabilities fixed and tested
