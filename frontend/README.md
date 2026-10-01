# HGW-Dashboard (Frontend Angular)

Interface utilisateur finale pour la gestion de passerelle domestique (Home Gateway).

## 📋 Description

HGW-Dashboard est une application **Angular standalone** qui fournit une interface web intuitive pour :
- ✅ Authentification utilisateur (login/logout)
- ✅ Tableau de bord de surveillance (dashboard)
- ✅ Gestion des entrées/événements réseau
- ✅ Chat AI intégré pour le contrôle conversationnel
- ✅ Panneau administrateur pour la gestion des utilisateurs
- ✅ Gestion des thèmes et layouts

## 🏗️ Structure du Projet

```
src/
├── main.ts                 # Point d'entrée de l'application
├── app/
│   ├── app.ts             # Composant racine
│   ├── app.config.ts      # Configuration Angular
│   ├── app.routes.ts      # Définition des routes
│   ├── guards/            # Garde d'authentification
│   ├── interceptors/       # Intercepteurs HTTP (auth)
│   ├── layout/            # Composants de layout (sidebar, topbar)
│   ├── pages/             # Pages principales
│   │   ├── auth/          # Pages d'authentification (login)
│   │   ├── dashboard/     # Tableau de bord
│   │   ├── admin/         # Panel administrateur
│   │   ├── chat/          # Interface de chat AI
│   │   └── entries/       # Gestion des entrées
│   └── services/          # Services (auth, layout, theme)
└── styles.scss            # Styles globaux
```

## 🚀 Installation

### Prérequis
- **Node.js** >= 20.x
- **npm** >= 10.x
- **Angular CLI** >= 19.x

### Étapes

```bash
# 1. Naviguer au dossier du projet
cd hgw-dashboard

# 2. Installer les dépendances
npm install

# 3. Démarrer le serveur de développement
npm start

# 4. Ouvrir dans le navigateur
# L'app s'ouvre automatiquement à http://localhost:4200
```

## 🔧 Configuration

### Backend API
L'application communique avec le backend FastAPI (Telecom02) sur **http://localhost:8000**.

Modifiez les URLs dans [src/app/services/auth.service.ts](src/app/services/auth.service.ts) si nécessaire :

```typescript
private apiUrl = 'http://localhost:8000/api';
```

### Routes Disponibles

| Route | Composant | Description |
|-------|-----------|-------------|
| `/` | Redirection | Vers `/dashboard` |
| `/login` | LoginComponent | Authentification utilisateur |
| `/dashboard` | DashboardComponent | Tableau de bord principal |
| `/chat` | ChatComponent | Interface de chat AI |
| `/entries` | EntriesComponent | Gestion des entrées |
| `/admin` | AdminStatsComponent | Panel administrateur |

## 📦 Dépendances Principales

- **@angular/core** >= 19.x - Framework Angular
- **@angular/router** >= 19.x - Routage
- **rxjs** >= 7.x - Programmation réactive
- **@angular/common** >= 19.x - Modules communs

Voir [package.json](package.json) pour la liste complète.

## 📝 Fichiers Clés

- **[app.config.ts](src/app/app.config.ts)** - Configuration globale de l'application
- **[app.routes.ts](src/app/app.routes.ts)** - Définition des routes et lazy loading
- **[auth.guard.ts](src/app/guards/auth.guard.ts)** - Garde pour protéger les routes
- **[auth.interceptor.ts](src/app/interceptors/auth.interceptor.ts)** - Injection automatique du token JWT
- **[auth.service.ts](src/app/services/auth.service.ts)** - Service d'authentification

## 🔐 Sécurité

### Token JWT
- Le token est stocké dans `localStorage` après le login
- L'interceptor ajoute automatiquement le header `Authorization: Bearer <token>` à toutes les requêtes HTTP
- Le token est supprimé au logout

### Authentification
- Protégée par `auth.guard.ts`
- Les routes protégées redirigent vers `/login` si l'utilisateur n'est pas authentifié

## 🧪 Tests

```bash
# Lancer les tests unitaires
npm run test

# Tests avec coverage
npm run test:coverage

# Tests en mode watch
npm run test:watch
```

## 🏗️ Build Production

```bash
# Construire l'application
npm run build

# L'output est généré dans ./dist/
```

## 🔗 Intégration avec les Autres Projets

### Backend (Telecom02)
- **URL** : `http://localhost:8000`
- **Endpoints** : `/api/auth`, `/api/chat`, `/api/devices`, etc.
- **Documentation** : Voir [Telecom02 README](../../Telecom02/README.md)

### MCP Server
- Utilisé indirectement via le backend FastAPI
- Pour la gestion réseau conversationnelle

### MCP Client (Streamlit)
- Application de démonstration alternative
- Référence pour l'intégration du chat

## 🐛 Débogage

### Build échoue ?
1. Vérifier que `node_modules/` est à jour : `npm install`
2. Nettoyer le cache : `rm -rf dist/ .angular/`
3. Relancer : `npm start`

### Problèmes de CORS ?
- Vérifier que le backend accepte les requêtes de `http://localhost:4200`
- Vérifier la configuration CORS dans `src/main.py` du backend

### Erreurs de TypeScript ?
- Fichiers `tsconfig.app.json` et `tsconfig.spec.json` ont `rootDir` correctement défini
- Relancer la compilation : `ng build`

## 📚 Ressources

- [Documentation Angular](https://angular.dev)
- [Angular Router](https://angular.dev/guide/routing)
- [RxJS Documentation](https://rxjs.dev)

## 👥 Contribution

1. Créer une branche feature : `git checkout -b feature/ma-feature`
2. Faire les modifications
3. Tester localement : `npm start`
4. Committer : `git commit -m "feat: description"`
5. Push : `git push origin feature/ma-feature`

## 📄 Licence

Tous droits réservés © 2026 HGW Project

---

**Dernière mise à jour** : April 21, 2026
