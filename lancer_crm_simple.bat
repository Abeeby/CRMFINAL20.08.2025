@echo off
echo =====================================
echo   GLOBIBAT CRM ELITE - LANCEMENT
echo =====================================
echo.

:: Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo.

:: Lancer l'application
echo Lancement de l'application...
echo.
echo =====================================
echo   ACCES AU CRM ELITE
echo =====================================
echo.
echo  CRM Principal:    http://localhost:5005
echo  Badge Employes:   http://localhost:5005/employee/badge
echo.
echo  Email:     info@globibat.com
echo  Mot de passe: Miser1597532684$
echo.
echo =====================================
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.

:: Lancer l'application
python app.py

pause
