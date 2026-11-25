@echo off
chcp 65001 >nul
title AICS Web Demo (5500)
cd /d "%~dp0.."

netstat -ano | findstr ":5500" | findstr "LISTENING" >nul 2>nul
if not errorlevel 1 (
    echo [WARN] Port 5500 is already in use.
    echo        A web server may already be running.
    pause
    exit /b 1
)

echo ============================================
echo  Serving web demo at http://127.0.0.1:5500
echo  Open that URL in your browser.
echo  Keep this window open. Press Ctrl+C to stop.
echo ============================================
echo.

python -m http.server 5500 --directory web

echo.
echo [EXIT] Web demo stopped.
pause
