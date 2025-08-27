#!/bin/bash

echo "🚀 PUSH DU CRM SAAS VERS GITHUB"
echo "================================"
echo ""

# Configuration du remote GitHub
echo "📦 Configuration du repository GitHub..."
git remote add origin https://github.com/Abeeby/Saas.git

# Vérifier si le remote existe déjà
if [ $? -ne 0 ]; then
    echo "Le remote existe déjà, mise à jour..."
    git remote set-url origin https://github.com/Abeeby/Saas.git
fi

# Afficher le status
echo ""
echo "📊 Status du repository :"
git status --short

# Push vers GitHub
echo ""
echo "🔄 Push vers GitHub..."
echo "Tentative de push..."
git push -u origin main --force

echo ""
echo "================================"
echo "✅ Si le push a réussi, votre projet est maintenant sur :"
echo "   https://github.com/Abeeby/Saas"
echo ""
echo "⚠️  Si vous avez une erreur d'authentification :"
echo "   1. Créez un Personal Access Token sur GitHub"
echo "   2. Utilisez-le comme mot de passe"
echo ""
echo "Ou exécutez manuellement :"
echo "   git push -u origin main --force"
echo "================================"