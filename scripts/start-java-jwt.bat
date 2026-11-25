@echo off
chcp 65001 >nul
title AICS Java Service (8080, JWT auth)
cd /d "%~dp0..\java-service"

set AICS_AUTH_MODE=jwt
set AICS_DEV_TOKEN_ENABLED=true
set INTERNAL_TOKEN=local-aics-internal-7f3c9b2e6d1a4c8f
set JWT_SECRET=local-aics-jwt-secret-32bytes-min-2026
set SERVER_ADDRESS=127.0.0.1
set INTERNAL_PORT=8081
set MANAGEMENT_PORT=8089

for %%P in (8080 8081 8089) do (
    netstat -ano | findstr ":%%P" | findstr "LISTENING" >nul 2>nul
    if not errorlevel 1 (
        echo [WARN] Port %%P is already in use.
        echo        A service may already be running. Check with:
        echo            netstat -ano ^| findstr :%%P
        echo.
        pause
        exit /b 1
    )
)

if not exist "target\aics-java-1.0.0.jar" (
    echo ============================================
    echo  JAR not found. Building with Maven...
    echo ============================================
    echo.
    call mvn -DskipTests clean package
    if errorlevel 1 (
        echo.
        echo [FAIL] Maven build failed. Send the log above to Claude.
        pause
        exit /b 1
    )
)

echo ============================================
echo  Starting Java service (JWT auth) on http://127.0.0.1:8080
echo  Dev token endpoint (loopback only): POST /api/auth/dev-token
echo  Health:  http://127.0.0.1:8089/actuator/health
echo  Wait for this log line: Started AicsApplication
echo  Keep this window open. Closing it stops the service.
echo ============================================
echo.

java -jar target\aics-java-1.0.0.jar

echo.
echo [EXIT] Java service stopped.
echo If this is an error, send the log above to Claude.
pause
