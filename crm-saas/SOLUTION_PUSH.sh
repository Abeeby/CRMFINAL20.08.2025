#!/bin/bash

clear
echo "================================================"
echo "    🔧 SOLUTION POUR PUSHER SUR GITHUB"
echo "================================================"
echo ""
echo "❌ Erreur : Permission denied (403)"
echo "   Le bot Cursor n'a pas accès à votre GitHub"
echo ""
echo "✅ MAIS voici 3 solutions simples :"
echo ""
echo "================================================"
echo "    SOLUTION 1 : Token GitHub (RECOMMANDÉ)"
echo "================================================"
echo ""
echo "1️⃣  Créez un token sur GitHub :"
echo "    👉 https://github.com/settings/tokens/new"
echo "    - Nom : 'CRM Push'"
echo "    - Cochez : ✅ repo (tout)"
echo "    - Cliquez : Generate token"
echo "    - COPIEZ LE TOKEN !"
echo ""
echo "2️⃣  Entrez vos informations ci-dessous :"
echo ""
read -p "Votre username GitHub : " username
echo ""
echo "Votre token GitHub (sera caché) : "
read -s token
echo ""

if [ ! -z "$username" ] && [ ! -z "$token" ]; then
    echo "Configuration en cours..."
    
    # Configurer git
    git config user.name "$username"
    git config user.email "$username@users.noreply.github.com"
    
    # Configurer le remote avec authentification
    git remote set-url origin https://${username}:${token}@github.com/Abeeby/Saas.git
    
    echo "🚀 Push en cours..."
    git push -u origin main --force
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "================================================"
        echo "    ✅ SUCCÈS ! Projet uploadé sur GitHub !"
        echo "================================================"
        echo ""
        echo "👉 Votre projet : https://github.com/Abeeby/Saas"
        echo ""
        # Nettoyer le token de l'URL pour la sécurité
        git remote set-url origin https://github.com/Abeeby/Saas.git
    else
        echo "❌ Erreur lors du push. Vérifiez votre token."
    fi
else
    echo "❌ Username ou token manquant"
fi

echo ""
echo "================================================"
echo "    SOLUTION 2 : Commande Manuelle"
echo "================================================"
echo ""
echo "Copiez cette commande dans VOTRE terminal local :"
echo ""
echo "cd /workspace/crm-saas && git push -u origin main --force"
echo ""
echo "================================================"
echo "    SOLUTION 3 : Download & Push"
echo "================================================"
echo ""
echo "1. Téléchargez : /workspace/crm-saas-complet.tar.gz"
echo "2. Extrayez sur votre machine"
echo "3. Pushez depuis votre terminal local"
echo ""