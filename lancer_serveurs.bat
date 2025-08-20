@echo off
echo ========================================
echo DEMARRAGE DES SERVEURS GLOBIBAT
echo ========================================

echo.
echo [1] Demarrage du CRM (port 5005)...
start /B cmd /c "cd /d %~dp0 && venv\Scripts\activate && python app.py"

timeout /t 5 /nobreak > nul

echo [2] Demarrage du Site Web (port 5001)...
start /B cmd /c "cd /d %~dp0 && venv\Scripts\activate && python globibat_website.py"

timeout /t 5 /nobreak > nul

echo.
echo ========================================
echo SERVEURS DEMARRE AVEC SUCCES !
echo ========================================
echo.
echo CRM:      http://localhost:5005
echo Site Web: http://localhost:5001
echo.
echo Appuyez sur une touche pour fermer cette fenetre...
pause > nul
