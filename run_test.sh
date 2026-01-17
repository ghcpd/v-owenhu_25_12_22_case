#!/bin/bash

# run_test.sh - Test execution script for Linux/macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/test_run.log"

# ANSI color codes
GREEN='\033[92m'
RED='\033[91m'
RESET='\033[0m'

# Create logs directory if it doesn't exist
mkdir -p "${LOG_DIR}"

# Initialize log file
cat > "${LOG_FILE}" << 'EOF'
================================================================================
Security Audit Test Execution Log
================================================================================
EOF

# Function to log messages
log_message() {
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[${timestamp}] $1" | tee -a "${LOG_FILE}"
}

# Function to test a Python file
test_python_file() {
    local file=$1
    local file_name=$(basename "$file")
    
    # Check if file exists
    if [ ! -f "${SCRIPT_DIR}/${file}" ]; then
        printf "  %-30s ${RED}ERROR${RESET} (File not found)\n" "${file_name}"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${file_name}: ERROR - File not found" >> "${LOG_FILE}"
        return 1
    fi
    
    # Run Python syntax check
    if python -m py_compile "${SCRIPT_DIR}/${file}" 2>&1 | tee -a "${LOG_FILE}"; then
        printf "  %-30s ${GREEN}PASSED${RESET}\n" "${file_name}"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${file_name}: PASSED" >> "${LOG_FILE}"
        return 0
    else
        printf "  %-30s ${RED}ERROR${RESET}\n" "${file_name}"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${file_name}: ERROR" >> "${LOG_FILE}"
        return 1
    fi
}

# Set environment variables
export FLASK_ENV=production
export PAYMENT_TOKEN="test_token_12345"
export MAIL_SERVER_KEY="test_mail_key"
export INTERNAL_AUTH="test_internal_key"

log_message "Environment Setup"
log_message "=================="
log_message "OS: $(uname -s)"
log_message "Python: $(python --version 2>&1)"
log_message "Working Directory: $(pwd)"
log_message ""

# Test header
log_message ""
log_message "Running Tests..."
log_message ""

echo ""
echo "Test Results"
echo "============"
echo ""

TEST_PASSED=true

# Test input_backup.py
if ! test_python_file "input_backup.py"; then
    TEST_PASSED=false
fi

# Test input.py
if ! test_python_file "input.py"; then
    TEST_PASSED=false
fi

# Summary
echo ""
log_message ""
log_message "=========================================="
log_message "Test Execution Summary"
log_message "=========================================="

if [ "$TEST_PASSED" = true ]; then
    printf "${GREEN}TEST PASSED${RESET}\n"
    log_message "Status: TEST PASSED"
    exit 0
else
    printf "${RED}TEST FAILED${RESET}\n"
    log_message "Status: TEST FAILED"
    exit 1
fi
