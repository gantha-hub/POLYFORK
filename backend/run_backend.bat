@echo off
REM ============================================================================
REM VrikshaVision Windows Startup Script (Run without Docker/Redis/Celery)
REM ============================================================================

echo Starting VrikshaVision Backend...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Virtual environment not found. Please run 'python -m venv .venv' first.
    pause
    exit /b 1
)

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
