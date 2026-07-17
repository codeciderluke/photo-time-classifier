@echo off
setlocal
cd /d "%~dp0"

rem Command-line interface for Photo Time Classifier.
rem Usage: cli.bat SOURCE DESTINATION [options]
rem Example: cli.bat ".\photos" ".\sorted" --month

set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment not found. Run run.bat once first.
    pause
    exit /b 1
)

"%VENV_PY%" cli.py %*
exit /b %errorlevel%
