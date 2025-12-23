@echo off
REM Usage: run_test.bat <module-path>
if "%~1"=="" (
  echo Usage: %~n0 ^<module-path^>
  exit /b 2
)
python -u "%~dp0tests\run_tests.py" "%~1"
exit /b %errorlevel%
