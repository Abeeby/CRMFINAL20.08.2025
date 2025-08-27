@echo off
echo ====================================
echo    CRM SAAS - DEMARRAGE
echo ====================================
echo.

echo [1] Installation des dependances...
call npm install >nul 2>&1

echo [2] Generation du client Prisma...
call npx prisma generate >nul 2>&1

echo [3] Migration de la base de donnees...
call npx prisma migrate deploy >nul 2>&1

echo [4] Demarrage du serveur...
echo.
echo ====================================
echo    SERVEUR DEMARRE !
echo ====================================
echo.
echo Acces :
echo   - API : http://localhost:3333
echo   - Health : http://localhost:3333/health
echo.
echo Comptes de test :
echo   - Admin : admin@test.com / Admin123!
echo   - User : user@test.com / User123!
echo   - Sales : sales@test.com / Sales123!
echo.
echo Pour arreter : Fermer cette fenetre ou CTRL+C
echo.

call npm run dev