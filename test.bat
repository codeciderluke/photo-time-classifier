@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment not found. Run run.bat once first.
    pause
    exit /b 1
)

rem --- pytest lives in requirements-dev.txt, which run.bat does not install ---
"%VENV_PY%" -m pytest --version >nul 2>nul
if errorlevel 1 (
    echo [SETUP] Installing test dependencies...
    "%VENV_PY%" -m pip install -r requirements-dev.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install test dependencies.
        pause
        exit /b 1
    )
)

echo [TEST] Running unit tests...
"%VENV_PY%" -m pytest
set "EXIT_CODE=%errorlevel%"

pause
endlocal
exit /b %EXIT_CODE%
