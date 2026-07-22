@echo off
cd /d "%~dp0"

echo ========================================
echo   FC VAINQUEUR - Serveur + Tunnel
echo ========================================
echo.

echo 1. Demarrage Flask...
start "Flask" /min cmd /c start_flask.bat
timeout /t 5 /nobreak >nul

echo 2. Verification...
curl -s http://localhost:5000/ >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Flask ne repond pas!
    pause
    exit /b 1
)
echo    Flask OK!

echo 3. Demarrage tunnel serveo...
ssh -o StrictHostKeyChecking=no -R 80:localhost:5000 serveo.net
echo Tunnel ferme.
pause
