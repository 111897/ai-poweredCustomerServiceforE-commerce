@echo off
chcp 65001 >nul
title AICS Chat Test
cd /d "%~dp0"

curl.exe -s -m 2 -o nul http://127.0.0.1:8089/actuator/health
if errorlevel 1 (
    echo ============================================
    echo  [WARN] Java service on port 8080 is not running.
    echo  Start start-python.bat and start-java.bat first,
    echo  then run this test again.
    echo ============================================
    pause
    exit /b 1
)

:again
echo ============================================
echo  Test chat (user 1001): order / shipping query
echo ============================================
echo.

curl.exe -sN -X POST http://127.0.0.1:8080/api/chat/stream -H "Content-Type: application/json" -H "X-Debug-User-Id: 1001" -d @test-body.json

echo.
echo ============================================
echo  Test finished. This is NOT an error.
echo  Press Enter to run the test again,
echo  or type N then Enter to close this window.
echo  Note: closing this window does not stop
echo  the Python / Java service windows.
echo ============================================
set "again="
set /p "again=Run again? (Enter=yes / N=no): "
if /i "%again%"=="n" exit /b 0
cls
goto again
