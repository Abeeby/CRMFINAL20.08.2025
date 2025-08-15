@echo off
echo =====================================
echo   GLOBIBAT CRM ELITE - SETUP
echo =====================================
echo.

echo [1/3] Creation de l'environnement virtuel...
python -m venv venv
echo.

echo [2/3] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo.

echo [3/3] Installation des dependances...
pip install -r requirements.txt
echo.

echo =====================================
echo   INSTALLATION TERMINEE !
echo =====================================
echo.
echo Pour lancer le CRM, executez: lancer_crm.bat
echo.

pause
