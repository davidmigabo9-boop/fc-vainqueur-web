@echo off
title FC VAINQUEUR - Tunnel SSH
echo ========================================
echo   FC VAINQUEUR - Tunnel en cours...
echo ========================================
echo.
echo Cherche le lien HTTPS ci-dessous...
echo.
ssh -o StrictHostKeyChecking=no -R 80:localhost:5000 nokey@localhost.run
echo.
echo Tunnel ferme.
pause
