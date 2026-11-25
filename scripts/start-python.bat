@echo off
chcp 65001 >nul
title AICS Python AI Service (8000)
cd /d "%~dp0.."

netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>nul
if not errorlevel 1 (
    echo [WARN] Port 8000 is already in use.
    echo        The Python service may already be running.
    echo        Check with: netstat -ano ^| findstr :8000
    echo.
    pause
    exit /b 1
)

echo ============================================
echo  Starting Python AI service on http://127.0.0.1:8000
echo  Wait for this log line: AI service started
echo  Keep this window open. Closing it stops the service.
echo ============================================
echo.

set PYTHONPATH=./python-service
set PYTHONIOENCODING=utf-8
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo [EXIT] Python service stopped.
echo If this is an error, send the log above to Claude.
pause
