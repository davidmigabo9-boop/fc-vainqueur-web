@echo off
echo Demarrage de Flask...
cd /d "C:\Users\LENOVO\Documents\New OpenCode Project\fc_vainqueur_web"
start /b python app.py > nul 2>&1
timeout /t 4 /nobreak > nul
echo Demarrage du tunnel SSH...
ssh -o StrictHostKeyChecking=no -N -R 80:localhost:5000 nokey@localhost.run > url.txt 2>&1
