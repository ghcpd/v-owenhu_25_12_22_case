@echo off
setlocal enableextensions enabledelayedexpansion
if "%~1"=="" (
  set TARGET=all
) else (
  set TARGET=%~1
)

rem ensure env vars for tests
if not defined AUTH_SECRET set AUTH_SECRET=test_auth_secret
if not defined PAYMENT_TOKEN set PAYMENT_TOKEN=test_payment_token
if not defined ADMIN_API_KEY set ADMIN_API_KEY=test_admin_key
if not defined ALLOWED_NOTIFY_HOSTS set ALLOWED_NOTIFY_HOSTS=localhost,127.0.0.1

if "%TARGET%"=="backup" (
  python -m unittest tests.test_input_backup -v
  exit /b %ERRORLEVEL%
) else if "%TARGET%"=="fixed" (
  python -m unittest tests.test_input_fixed -v
  exit /b %ERRORLEVEL%
) else if "%TARGET%"=="all" (
  python -m unittest tests.test_input_backup -v || exit /b %ERRORLEVEL%
  python -m unittest tests.test_input_fixed -v || exit /b %ERRORLEVEL%
) else (
  echo Unknown target %TARGET%
  exit /b 2
)
