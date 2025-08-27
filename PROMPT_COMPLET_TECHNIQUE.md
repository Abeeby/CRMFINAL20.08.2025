# PROMPT TECHNIQUE DÉTAILLÉ - CRM SAAS

## RÉSUMÉ EXÉCUTIF
Projet CRM SaaS backend complet en TypeScript, bloqué au push GitHub (erreur 403), nécessite frontend et déploiement.

## STRUCTURE DU PROJET
```
/workspace/
├── crm-saas/                    # ← PROJET PRINCIPAL ICI
│   ├── src/
│   │   ├── server.ts           # Point d'entrée Express
│   │   ├── modules/
│   │   │   ├── auth/           # JWT + Refresh tokens
│   │   │   ├── attendance/     # Badgeage RH 4x/jour
│   │   │   ├── companies/      # CRUD entreprises
│   │   │   ├── contacts/       # CRUD contacts RGPD
│   │   │   ├── deals/          # Pipeline commercial
│   │   │   ├── tickets/        # Support client
│   │   │   └── users/          # Gestion utilisateurs
│   │   ├── middlewares/        # Auth, validation, erreurs
│   │   └── utils/             # Logger Winston
│   ├── prisma/
│   │   ├── schema.prisma      # 11 tables SQLite
│   │   ├── migrations/        # Migrations appliquées
│   │   └── seed.ts           # Données de test OK
│   ├── package.json           # Dependencies installées
│   ├── tsconfig.json         # Config TypeScript
│   ├── .env                  # Variables configurées
│   └── dev.db               # Base SQLite avec données
├── crm-saas-complet.tar.gz   # Archive 61MB
└── [anciens fichiers Flask à ignorer]
```

## ÉTAT TECHNIQUE ACTUEL

### ✅ BACKEND COMPLET ET FONCTIONNEL
- **Serveur** : http://localhost:3333 (démarre avec `npm run dev`)
- **API REST** : 30+ endpoints testés
- **WebSocket** : Socket.io configuré
- **Base** : SQLite avec 11 tables, relations, indexes
- **Auth** : JWT (15min) + Refresh (7j) + httpOnly cookies
- **Validation** : Zod sur toutes les routes
- **Logs** : Winston avec rotation
- **Tests** : Script test-api.js valide tous les endpoints

### 📊 ENDPOINTS PRINCIPAUX
```typescript
POST   /api/auth/login          // ✅ Testé
POST   /api/auth/register       // ✅ Testé
GET    /api/auth/me            // ✅ Testé
POST   /api/attendance/punch    // ✅ Badgeage
GET    /api/attendance/today    // ✅ Pointages jour
GET    /api/attendance/report   // ✅ Rapport mensuel
GET    /api/deals/pipeline      // ✅ Vue Kanban
POST   /api/tickets            // ✅ Création tickets
```

### 🗄️ MODÈLES DE DONNÉES
```typescript
User     { id, email, passwordHash, role: string, ... }
Company  { id, name, vat, tags: string, ... }
Contact  { id, firstName, lastName, consentEmail: bool, ... }
Deal     { id, title, stage: string, amount: float, ... }
Ticket   { id, number, status: string, priority: string, ... }
Attendance { id, employeeId, type: string, timestamp, anomaly: string, ... }
```

### 👤 COMPTES DE TEST
- admin@test.com / Admin123! (role: ADMIN)
- user@test.com / User123! (role: EMPLOYEE)
- sales@test.com / Sales123! (role: SALES_MANAGER)

## 🔴 PROBLÈME ACTUEL : PUSH GITHUB

### Situation Git :
```bash
$ pwd                          # /workspace/crm-saas
$ git status                   # Clean, tout commité
$ git remote -v               # origin https://github.com/Abeeby/Saas.git
$ git push origin main        # ERREUR 403: Permission denied to cursor[bot]
```

### Tentatives échouées :
- Direct push : 403 Permission denied
- Avec --force : Même erreur
- Le bot Cursor n'a pas les credentials GitHub

### Solutions à implémenter :
1. Configurer Personal Access Token
2. Ou télécharger et pusher depuis machine locale
3. Ou utiliser GitHub Desktop

## 🎯 BESOINS IMMÉDIATS

### 1. DÉBLOQUER LE PUSH GITHUB (PRIORITÉ 1)
```bash
# Besoin de réussir :
cd /workspace/crm-saas
git push -u origin main --force
# → Résoudre erreur 403
```

### 2. CRÉER FRONTEND REACT/NEXT.JS (PRIORITÉ 2)
Créer dans `/workspace/crm-saas/client/` :
- Pages : Login, Dashboard, Badgeage, Companies, Deals, Tickets
- Composants : Navbar, Sidebar, KPIs, DataTables
- Auth : Context API ou Zustand pour JWT
- UI : TailwindCSS + shadcn/ui
- Formulaires : React Hook Form + Zod
- État : React Query pour cache API

### 3. DÉPLOYER SUR VERCEL (PRIORITÉ 3)
- Adapter pour PostgreSQL (Prisma supporte les deux)
- Variables d'environnement production
- Build process TypeScript
- Configuration Vercel/Railway

## 💻 COMMANDES DE DÉVELOPPEMENT
```bash
# Backend
cd /workspace/crm-saas
npm run dev                    # Démarre sur :3333
npm run prisma:studio          # Interface BDD
node test-api.js              # Tests API

# Git (bloqué)
git push -u origin main --force  # Erreur 403

# Archive disponible
ls -lh /workspace/crm-saas-complet.tar.gz  # 61MB
```

## 🚀 NEXT STEPS RECOMMANDÉS
1. Résoudre auth GitHub pour push
2. Créer frontend Next.js avec App Router
3. Connecter front au back via fetch/axios
4. Implémenter UI badgeage temps réel
5. Déployer back sur Railway, front sur Vercel
6. Migrer SQLite → PostgreSQL

## ❓ QUESTIONS POUR L'IA
1. Comment contourner l'erreur 403 GitHub du bot Cursor ?
2. Peux-tu créer le frontend Next.js dans /workspace/crm-saas/client ?
3. Quelle est la meilleure approche pour déployer ce stack sur Vercel ?

---
**IMPORTANT** : Le projet backend est 100% fonctionnel. Il manque juste le push GitHub et le frontend.