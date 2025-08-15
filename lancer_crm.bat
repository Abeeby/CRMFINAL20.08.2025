@echo off
echo =====================================
echo   GLOBIBAT CRM ELITE - LANCEMENT
echo =====================================
echo.

:: Vérifier si l'environnement virtuel existe
if not exist "venv" (
    echo [1/5] Creation de l'environnement virtuel...
    python -m venv venv
    echo.
)

:: Activer l'environnement virtuel
echo [2/5] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo.

:: Installer les dépendances
echo [3/5] Installation des dependances...
pip install -r requirements.txt --quiet
echo.

:: Arrêter les processus Python existants
echo [4/5] Arret des processus en cours...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak > nul
echo.

:: Lancer l'application
echo [5/5] Lancement de l'application...
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
