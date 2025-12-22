@echo off
if "%1"=="" (
  echo usage: run_test.bat ^<file^>
  exit /b 2
)
REM run from script dir to ensure tests/run_test.py is found
python -u "%~dp0tests\run_test.py" "%~1"
