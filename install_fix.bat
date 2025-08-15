@echo off
echo =====================================
echo   GLOBIBAT CRM ELITE - FIX INSTALL
echo =====================================
echo.

echo [1/3] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo.

echo [2/3] Mise a jour de pip...
python -m pip install --upgrade pip
echo.

echo [3/3] Installation des dependances une par une...
echo.

echo Installation de Flask...
pip install Flask==3.0.0

echo Installation de Flask-SQLAlchemy...
pip install Flask-SQLAlchemy==3.1.1

echo Installation de Flask-Login...
pip install Flask-Login==0.6.3

echo Installation de Flask-SocketIO...
pip install Flask-SocketIO==5.3.5

echo Installation de python-socketio...
pip install python-socketio==5.10.0

echo Installation de SQLAlchemy...
pip install SQLAlchemy==2.0.23

echo Installation de Werkzeug...
pip install Werkzeug==3.0.1

echo Installation de python-dotenv...
pip install python-dotenv==1.0.0

echo Installation de reportlab...
pip install reportlab==4.0.7

echo Installation de openpyxl...
pip install openpyxl==3.1.2

echo Installation de pyotp...
pip install pyotp==2.9.0

echo Installation de qrcode...
pip install qrcode==7.4.2

echo Installation de Pillow...
pip install Pillow==10.1.0

echo.
echo =====================================
echo   INSTALLATION TERMINEE !
echo =====================================
echo.
echo Pour lancer le CRM, executez: lancer_crm.bat
echo.

pause
