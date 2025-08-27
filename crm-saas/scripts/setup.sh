#!/bin/bash

echo "🚀 Configuration du CRM SaaS..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Node.js
echo "Vérification de Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js n'est pas installé${NC}"
    echo "Veuillez installer Node.js version 18 ou supérieure"
    exit 1
else
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✅ Node.js installé: $NODE_VERSION${NC}"
fi

# Check Docker
echo "Vérification de Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker n'est pas installé${NC}"
    echo "Docker est recommandé pour PostgreSQL et Redis"
    echo "Continuer sans Docker ? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Docker installé${NC}"
fi

# Copy .env file
echo ""
echo "Configuration de l'environnement..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Fichier .env créé${NC}"
    echo -e "${YELLOW}⚠️  Veuillez éditer le fichier .env avec vos paramètres${NC}"
else
    echo -e "${GREEN}✅ Fichier .env existe déjà${NC}"
fi

# Install dependencies
echo ""
echo "Installation des dépendances..."
npm install
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dépendances installées${NC}"
else
    echo -e "${RED}❌ Erreur lors de l'installation des dépendances${NC}"
    exit 1
fi

# Start Docker services if Docker is available
if command -v docker &> /dev/null; then
    echo ""
    echo "Démarrage des services Docker..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Services Docker démarrés${NC}"
        
        # Wait for PostgreSQL
        echo "En attente de PostgreSQL..."
        sleep 5
        
        # Counter for retries
        RETRIES=0
        MAX_RETRIES=30
        
        while ! docker exec crm-saas-postgres-1 pg_isready -U postgres > /dev/null 2>&1; do
            RETRIES=$((RETRIES+1))
            if [ $RETRIES -eq $MAX_RETRIES ]; then
                echo -e "${RED}❌ PostgreSQL ne démarre pas${NC}"
                exit 1
            fi
            echo -n "."
            sleep 1
        done
        echo ""
        echo -e "${GREEN}✅ PostgreSQL prêt${NC}"
    else
        echo -e "${RED}❌ Erreur lors du démarrage des services Docker${NC}"
        exit 1
    fi
fi

# Generate Prisma client
echo ""
echo "Génération du client Prisma..."
npx prisma generate
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Client Prisma généré${NC}"
else
    echo -e "${RED}❌ Erreur lors de la génération du client Prisma${NC}"
    exit 1
fi

# Run migrations
echo ""
echo "Application des migrations..."
npx prisma migrate dev --name init
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migrations appliquées${NC}"
else
    echo -e "${RED}❌ Erreur lors des migrations${NC}"
    echo "Vérifiez votre connexion à PostgreSQL dans le fichier .env"
    exit 1
fi

# Seed database
echo ""
echo "Chargement des données de test..."
npm run prisma:seed
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Données de test chargées${NC}"
else
    echo -e "${YELLOW}⚠️  Erreur lors du chargement des données (peut-être déjà chargées)${NC}"
fi

# Create uploads directory
mkdir -p uploads
echo -e "${GREEN}✅ Dossier uploads créé${NC}"

# Create logs directory
mkdir -p logs
echo -e "${GREEN}✅ Dossier logs créé${NC}"

echo ""
echo "======================================"
echo -e "${GREEN}✅ Configuration terminée avec succès!${NC}"
echo "======================================"
echo ""
echo "Pour démarrer l'application :"
echo -e "${YELLOW}npm run dev${NC}"
echo ""
echo "Accès :"
echo "  - API : http://localhost:3333"
echo "  - Health : http://localhost:3333/health"
echo "  - Mailhog : http://localhost:8025"
echo ""
echo "Comptes de test :"
echo "  - Admin    : admin@test.com / Admin123!"
echo "  - User     : user@test.com / User123!"
echo "  - Sales    : sales@test.com / Sales123!"
echo ""
echo "Documentation API :"
echo "  http://localhost:3333/api/docs (à venir)"
echo ""