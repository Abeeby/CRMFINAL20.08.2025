#!/bin/bash

echo "======================================"
echo "   PUSH AUTOMATIQUE VERS GITHUB"
echo "======================================"
echo ""
echo "📦 Projet : CRM SaaS Complet"
echo "🔗 Repo   : https://github.com/Abeeby/Saas"
echo ""
echo "Appuyez sur ENTER pour continuer..."
read

# Vérifier si git est configuré
echo "Configuration Git..."
git config user.email "abeeby@github.com" 2>/dev/null
git config user.name "Abeeby" 2>/dev/null

# Configurer le remote
echo "Configuration du repository..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/Abeeby/Saas.git

# Afficher le status
echo ""
echo "📊 Fichiers à pusher :"
git ls-files | wc -l
echo "fichiers prêts"

echo ""
echo "======================================"
echo "   AUTHENTIFICATION GITHUB REQUISE"
echo "======================================"
echo ""
echo "GitHub va vous demander :"
echo "  1. Username : votre-username"
echo "  2. Password : VOTRE TOKEN (pas le mot de passe!)"
echo ""
echo "Si vous n'avez pas de token :"
echo "👉 https://github.com/settings/tokens/new"
echo "   - Nom : CRM Token"
echo "   - Cochez : ✅ repo"
echo "   - Generate token"
echo "   - COPIEZ LE TOKEN"
echo ""
echo "Appuyez sur ENTER pour pusher..."
read

# Push
echo "🚀 Push en cours..."
git push -u origin main --force

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "   ✅ SUCCÈS !"
    echo "======================================"
    echo ""
    echo "Votre CRM est maintenant sur :"
    echo "👉 https://github.com/Abeeby/Saas"
    echo ""
    echo "Pour cloner ailleurs :"
    echo "git clone https://github.com/Abeeby/Saas.git"
else
    echo ""
    echo "======================================"
    echo "   ⚠️  ERREUR D'AUTHENTIFICATION"
    echo "======================================"
    echo ""
    echo "1. Créez un token : https://github.com/settings/tokens/new"
    echo "2. Réessayez avec :"
    echo "   git push -u origin main --force"
    echo "3. Utilisez le TOKEN comme mot de passe"
fi