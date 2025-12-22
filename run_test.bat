@echo off
REM run_test.bat - Test execution script for Windows

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set LOG_DIR=%SCRIPT_DIR%logs
set LOG_FILE=%LOG_DIR%\test_run.log

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Initialize log file
(
    echo ================================================================================
    echo Security Audit Test Execution Log
    echo ================================================================================
) > "%LOG_FILE%"

REM Set environment variables
set FLASK_ENV=production
set PAYMENT_TOKEN=test_token_12345
set MAIL_SERVER_KEY=test_mail_key
set INTERNAL_AUTH=test_internal_key

REM Get current timestamp function
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)

REM Log initial setup
echo [%mydate% %mytime%] Environment Setup >> "%LOG_FILE%"
echo ==================== >> "%LOG_FILE%"
python --version >> "%LOG_FILE%" 2>&1
echo Working Directory: %CD% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo.
echo Test Results
echo ============
echo.

setlocal enabledelayedexpansion
set TEST_PASSED=true

REM Test input_backup.py
if exist "%SCRIPT_DIR%input_backup.py" (
    python -m py_compile "%SCRIPT_DIR%input_backup.py" >> "%LOG_FILE%" 2>&1
    if !errorlevel! equ 0 (
        echo   input_backup.py                  PASSED
        echo [%date% %time%] input_backup.py: PASSED >> "%LOG_FILE%"
    ) else (
        echo   input_backup.py                  ERROR
        echo [%date% %time%] input_backup.py: ERROR >> "%LOG_FILE%"
        set TEST_PASSED=false
    )
) else (
    echo   input_backup.py                  ERROR
    echo [%date% %time%] input_backup.py: ERROR - File not found >> "%LOG_FILE%"
    set TEST_PASSED=false
)

REM Test input.py
if exist "%SCRIPT_DIR%input.py" (
    python -m py_compile "%SCRIPT_DIR%input.py" >> "%LOG_FILE%" 2>&1
    if !errorlevel! equ 0 (
        echo   input.py                         PASSED
        echo [%date% %time%] input.py: PASSED >> "%LOG_FILE%"
    ) else (
        echo   input.py                         ERROR
        echo [%date% %time%] input.py: ERROR >> "%LOG_FILE%"
        set TEST_PASSED=false
    )
) else (
    echo   input.py                         ERROR
    echo [%date% %time%] input.py: ERROR - File not found >> "%LOG_FILE%"
    set TEST_PASSED=false
)

echo.
echo ==========================================
if "%TEST_PASSED%"=="true" (
    echo TEST PASSED
    echo [%date% %time%] Status: TEST PASSED >> "%LOG_FILE%"
    exit /b 0
) else (
    echo TEST FAILED
    echo [%date% %time%] Status: TEST FAILED >> "%LOG_FILE%"
    exit /b 1
)
