#!/bin/bash

echo "🚀 Démarrage du CRM SaaS..."
echo ""

# Kill any existing processes
echo "🧹 Nettoyage des processus..."
pkill -f "tsx.*server" 2>/dev/null || true
pkill -f "node.*server" 2>/dev/null || true
sleep 2

# Start the server
echo "📦 Démarrage du serveur..."
npm run dev &
SERVER_PID=$!

echo "   PID du serveur: $SERVER_PID"
echo ""

# Wait for server to be ready
echo "⏳ En attente du serveur..."
sleep 5

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Serveur démarré!"
    echo ""
    
    # Run tests
    echo "🧪 Lancement des tests..."
    node test-api.js
    
    echo ""
    echo "======================================"
    echo "📊 Serveur CRM SaaS opérationnel!"
    echo "======================================"
    echo ""
    echo "Accès :"
    echo "  - API : http://localhost:3333"
    echo "  - Health : http://localhost:3333/health"
    echo ""
    echo "Pour arrêter le serveur : kill $SERVER_PID"
    echo ""
else
    echo "❌ Le serveur n'a pas pu démarrer"
    echo "Vérifiez les logs avec : npm run dev"
    exit 1
fi