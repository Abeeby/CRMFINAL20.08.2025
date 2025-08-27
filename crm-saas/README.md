# CRM SaaS - Solution Complète avec Badgeage et RH

CRM professionnel multi-modules avec gestion commerciale, support client, badgeage/présence et fonctionnalités RH.

## 🚀 Démarrage Rapide

```bash
# 1. Installation automatique
chmod +x scripts/setup.sh
./scripts/setup.sh

# 2. Démarrer l'application
npm run dev

# L'application est maintenant accessible sur http://localhost:3333
```

## ✨ Fonctionnalités

### 🔐 Authentification & Sécurité
- JWT avec refresh tokens
- Cookies httpOnly sécurisés
- RBAC (contrôle d'accès basé sur les rôles)
- Protection CSRF
- Rate limiting

### 👥 Gestion Commerciale (CRM)
- **Companies** : Gestion complète des entreprises
- **Contacts** : Base de contacts avec consentements RGPD
- **Deals** : Pipeline de vente avec stages personnalisables
- **Activités** : Historique complet des interactions

### ⏰ Badgeage & Présence
- **4 pointages par jour** : Entrée/Sortie matin, Entrée/Sortie après-midi
- **Détection d'anomalies** : Retards, absences, chevauchements
- **Géolocalisation** : Support optionnel avec coordonnées GPS
- **Rapports** : Export CSV pour la paie, statistiques mensuelles
- **Validation** : Workflow de validation des anomalies

### 🎫 Support Client
- **Tickets** : Gestion complète avec priorités et SLA
- **Messages** : Fil de discussion avec pièces jointes
- **Assignation** : Distribution automatique ou manuelle
- **Statuts** : NEW, OPEN, PENDING, SOLVED, CLOSED

### 📊 Tableau de Bord
- KPIs en temps réel
- Pipeline de vente
- Tickets en attente
- Présences du jour
- Alertes et notifications

### 🔌 Intégrations
- **WebSocket** : Mises à jour temps réel
- **Email** : Envoi via SMTP (Mailhog en dev)
- **Stockage** : Support S3/MinIO pour les fichiers
- **Export** : CSV, PDF (à venir)

## 📦 Architecture Technique

```
crm-saas/
├── src/
│   ├── server.ts           # Point d'entrée
│   ├── modules/            # Modules métier
│   │   ├── auth/          # Authentification
│   │   ├── attendance/    # Badgeage/Présence
│   │   ├── companies/     # Entreprises
│   │   ├── contacts/      # Contacts
│   │   ├── deals/         # Opportunités
│   │   ├── tickets/       # Support
│   │   └── users/         # Utilisateurs
│   ├── middlewares/        # Middlewares Express
│   └── utils/             # Utilitaires
├── prisma/
│   ├── schema.prisma      # Schéma de base de données
│   └── seed.ts           # Données de démo
├── docker-compose.yml     # Services Docker
└── scripts/              # Scripts d'installation
```

## 🛠️ Stack Technique

- **Backend** : Node.js, Express, TypeScript
- **Database** : PostgreSQL avec Prisma ORM
- **Cache** : Redis (BullMQ pour les jobs)
- **Auth** : JWT + Refresh Tokens
- **Validation** : Zod
- **Logs** : Winston
- **Tests** : Jest (à venir)

## 📝 API Endpoints

### Authentication
```
POST   /api/auth/register     # Inscription
POST   /api/auth/login        # Connexion
POST   /api/auth/logout       # Déconnexion
POST   /api/auth/refresh      # Actualiser le token
GET    /api/auth/me          # Utilisateur actuel
```

### Attendance (Badgeage)
```
POST   /api/attendance/punch       # Pointer
GET    /api/attendance/today      # Pointages du jour
GET    /api/attendance/report     # Rapport mensuel
GET    /api/attendance/anomalies  # Liste des anomalies
GET    /api/attendance/export     # Export CSV pour paie
```

### Companies
```
GET    /api/companies         # Liste des entreprises
GET    /api/companies/:id     # Détail entreprise
POST   /api/companies         # Créer entreprise
PUT    /api/companies/:id     # Modifier entreprise
DELETE /api/companies/:id     # Supprimer entreprise
```

### Deals (Pipeline)
```
GET    /api/deals             # Liste des deals
GET    /api/deals/pipeline    # Vue pipeline
GET    /api/deals/:id         # Détail deal
POST   /api/deals             # Créer deal
PUT    /api/deals/:id         # Modifier deal
PATCH  /api/deals/:id/stage   # Changer le stage
```

### Tickets
```
GET    /api/tickets                    # Liste des tickets
GET    /api/tickets/:id                # Détail ticket
POST   /api/tickets                    # Créer ticket
PUT    /api/tickets/:id                # Modifier ticket
PATCH  /api/tickets/:id/status         # Changer statut
PATCH  /api/tickets/:id/assign         # Assigner
POST   /api/tickets/:id/messages       # Ajouter message
```

## 👤 Comptes de Démo

| Email | Mot de passe | Rôle | Permissions |
|-------|--------------|------|-------------|
| admin@test.com | Admin123! | ADMIN | Accès total |
| sales@test.com | Sales123! | SALES_MANAGER | Ventes, deals, companies |
| user@test.com | User123! | EMPLOYEE | Badgeage, profil |

## 🐳 Services Docker

```yaml
postgres    # Base de données PostgreSQL
redis       # Cache et queue
mailhog     # Serveur SMTP de développement
```

## 🔧 Configuration

Variables d'environnement principales (`.env`):

```env
# Database
DATABASE_URL="postgresql://postgres:password@localhost:5432/crm_saas"

# Auth
JWT_SECRET="your-secret-key"
JWT_EXPIRES_IN="15m"
JWT_REFRESH_SECRET="your-refresh-secret"
JWT_REFRESH_EXPIRES_IN="7d"

# Server
PORT=3333
NODE_ENV=development
```

## 📊 Modèles de Données

### User
- Gestion des utilisateurs avec rôles (ADMIN, SALES_MANAGER, SALES_REP, SUPPORT_AGENT, HR, EMPLOYEE)
- Support multi-timezone et multi-locale

### Attendance
- Types: IN_MORNING, OUT_MORNING, IN_AFTERNOON, OUT_EVENING
- Sources: WEB, MOBILE, QR, MANUAL
- Anomalies: NONE, MISSING, OVERLAP, LATE, EARLY

### Deal
- Stages: NEW, QUALIFIED, PROPOSAL, NEGOTIATION, WON, LOST
- Pipeline avec drag & drop (frontend à venir)
- Activités et historique

### Ticket
- Priorités: LOW, MEDIUM, HIGH, URGENT
- Statuts: NEW, OPEN, PENDING, SOLVED, CLOSED
- Support des pièces jointes

## 🚦 Commandes Utiles

```bash
# Développement
npm run dev              # Démarrer en mode dev

# Base de données
npm run prisma:studio    # Interface graphique Prisma
npm run prisma:migrate  # Appliquer les migrations
npm run prisma:seed     # Charger les données de test

# Docker
docker-compose up -d     # Démarrer les services
docker-compose down      # Arrêter les services
docker-compose logs -f   # Voir les logs

# Logs
tail -f logs/error.log   # Logs d'erreur
tail -f logs/combined.log # Tous les logs
```

## 🧪 Tests

```bash
npm test                 # Tests unitaires (à venir)
npm run test:e2e        # Tests E2E (à venir)
```

## 📈 Performances

- Rate limiting: 100 requêtes/minute par IP
- Pagination par défaut: 20 éléments
- Cache Redis pour les données fréquentes
- Indexes PostgreSQL optimisés
- Compression gzip activée

## 🔒 Sécurité

- Helmet.js pour les headers de sécurité
- CORS configuré
- Validation des entrées avec Zod
- SQL Injection protection via Prisma
- XSS protection
- Rate limiting
- Logs d'audit

## 🚀 Déploiement

### Production avec PM2
```bash
npm run build
pm2 start dist/server.js --name crm-saas
```

### Docker
```bash
docker build -t crm-saas .
docker run -p 3333:3333 crm-saas
```

### Variables d'environnement Production
```env
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/db
JWT_SECRET=<strong-random-string>
REDIS_URL=redis://redis:6379
```

## 📄 License

MIT

## 🤝 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Email : support@crm-saas.com

---

**Développé avec ❤️ pour une gestion d'entreprise moderne et efficace**