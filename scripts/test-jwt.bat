@echo off
chcp 65001 >nul
title AICS JWT Demo Test
cd /d "%~dp0"

curl.exe -s -m 2 -o nul http://127.0.0.1:8089/actuator/health
if errorlevel 1 (
    echo ============================================
    echo  [WARN] Java service on port 8080 is not running.
    echo  Start start-python.bat and start-java-jwt.bat first.
    echo ============================================
    pause
    exit /b 1
)

set PYTHONIOENCODING=utf-8
python jwt_demo.py

echo.
echo ============================================
echo  JWT demo finished. This is NOT an error.
echo ============================================
pause
