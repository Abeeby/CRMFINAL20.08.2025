# 🚀 ACCÈS RAPIDE AU PROJET

## COMMANDES À COPIER-COLLER :

### 1️⃣ ALLER AU PROJET
```bash
cd /workspace/crm-saas
```

### 2️⃣ VOIR LES FICHIERS
```bash
ls -la
```

### 3️⃣ DÉMARRER LE SERVEUR
```bash
npm run dev
```

### 4️⃣ OUVRIR LA BASE DE DONNÉES
```bash
npx prisma studio
```

### 5️⃣ TESTER L'API
```bash
node test-api.js
```

## 📁 STRUCTURE DU PROJET

```
/workspace/crm-saas/
├── src/              # Code TypeScript
├── prisma/           # Base de données
├── node_modules/     # Dépendances
├── package.json      # Config npm
├── README.md         # Documentation
├── dev.db           # Base SQLite
└── test-api.js      # Script de test
```

## 🌐 ACCÈS WEB

Une fois le serveur démarré :
- API : http://localhost:3333
- Health : http://localhost:3333/health

## 👤 COMPTES DE TEST

- Email : admin@test.com
- Password : Admin123!

## 💾 SAUVEGARDER LE PROJET

Pour copier sur votre bureau :
```bash
cp -r /workspace/crm-saas ~/Desktop/
```

Ou utiliser l'archive :
```bash
cp /workspace/crm-saas-complet.tar.gz ~/Desktop/
```