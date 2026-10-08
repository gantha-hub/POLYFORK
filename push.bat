@echo off
set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%backend\.venv\Scripts\python.exe" (
    "%SCRIPT_DIR%backend\.venv\Scripts\python.exe" "%SCRIPT_DIR%push.py" %*
) else (
    python "%SCRIPT_DIR%push.py" %*
)
