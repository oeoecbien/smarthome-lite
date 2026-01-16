# Web - Interface Next.js

Interface web moderne développée avec Next.js 16, React 19, TypeScript et Tailwind CSS pour la gestion du système SmartHome Lite.

## Table des Matières

- [Technologies](#technologies)
- [Structure du Projet](#structure-du-projet)
- [Installation](#installation)
- [Configuration](#configuration)
- [Développement](#développement)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Déploiement](#déploiement)

## Technologies

- **Framework** : Next.js 16.0.10 (App Router)
- **UI Library** : React 19.2.0
- **Langage** : TypeScript 5
- **Styling** : Tailwind CSS 4.1.9
- **Composants UI** : Radix UI (primitives accessibles)
- **Formulaires** : React Hook Form + Zod (validation)
- **Graphiques** : Recharts 2.15.4
- **Thème** : next-themes (mode sombre/clair)
- **Notifications** : Sonner (toasts)
- **Icônes** : Lucide React

## Structure du Projet

```
web/
├── app/                          # App Router Next.js
│   ├── (protected)/             # Routes protégées (requièrent authentification)
│   │   ├── layout.tsx           # Layout pour routes protégées
│   │   ├── dashboard/           # Tableau de bord principal
│   │   ├── devices/             # Gestion des appareils
│   │   ├── rules/               # Gestion des règles d'automatisation
│   │   ├── smart-dimming/       # Contrôle et visualisation smart dimming
│   │   ├── presence/            # Historique de présence
│   │   ├── light-readings/      # Graphiques de luminosité
│   │   ├── events/              # Journal des événements
│   │   ├── ai/                  # Interface IA (scénarios, prédictions)
│   │   └── admin/              # Interface d'administration
│   ├── login/                   # Page de connexion
│   ├── forgot-password/         # Page de réinitialisation de mot de passe
│   ├── layout.tsx               # Layout racine
│   ├── page.tsx                 # Page d'accueil
│   └── globals.css              # Styles globaux
│
├── components/                  # Composants réutilisables
│   ├── ui/                      # Composants UI (shadcn/ui)
│   └── ...                      # Autres composants métier
│
├── hooks/                       # Hooks React personnalisés
│
├── lib/                         # Utilitaires et helpers
│   ├── api.ts                   # Client API (fetch vers backend)
│   ├── auth-context.tsx         # Contexte d'authentification React
│   ├── services/                # Services API
│   │   └── auth-service.ts      # Service d'authentification (login, register, forgot-password, reset-password)
│   ├── types.ts                 # Types TypeScript
│   └── utils.ts                 # Fonctions utilitaires
│
├── public/                      # Assets statiques
│
├── styles/                      # Styles additionnels
│
├── package.json                 # Dépendances
├── tsconfig.json                # Configuration TypeScript
├── next.config.mjs              # Configuration Next.js
├── tailwind.config.js           # Configuration Tailwind
└── components.json              # Configuration shadcn/ui
```

## Installation

### Prérequis

- **Node.js** : 18.0 ou supérieur
- **npm** ou **pnpm** ou **yarn**

### Étapes d'Installation

```bash
# Naviguer vers le dossier web
cd web

# Installer les dépendances
npm install
# ou
pnpm install
# ou
yarn install
```

## Configuration

### Variables d'Environnement

Créer un fichier `.env.local` à la racine du dossier `web` :

```env
# URL du backend FastAPI
NEXT_PUBLIC_API_URL=http://localhost:8000

# URL alternative pour développement
# NEXT_PUBLIC_API_URL=http://10.109.150.75:8000
```

**Note** : Les variables d'environnement préfixées par `NEXT_PUBLIC_` sont accessibles côté client.

### Configuration API

Le client API est configuré dans `lib/api.ts`. Par défaut, il utilise `NEXT_PUBLIC_API_URL` ou `http://localhost:8000`.

## Développement

### Lancer le serveur de développement

```bash
npm run dev
# ou
pnpm dev
# ou
yarn dev
```

Le serveur démarre sur http://localhost:3000

### Build de production

```bash
npm run build
npm run start
```

### Linting

```bash
npm run lint
```

## Fonctionnalités

### Authentification

- **Page de connexion** : `/login`
  - Affichage/masquage du mot de passe avec icône œil
  - Lien "Mot de passe oublié ?" pour accéder à la réinitialisation
- **Réinitialisation de mot de passe** : `/forgot-password`
  - Demande de token de réinitialisation (username ou email)
  - Réinitialisation avec token et nouveau mot de passe
  - Affichage/masquage des mots de passe avec icônes œil
- **Gestion des tokens JWT** : Stockage sécurisé dans le navigateur
- **Routes protégées** : Toutes les routes sous `(protected)` nécessitent une authentification
- **Redirection automatique** : Redirection vers `/login` si non authentifié

### Tableau de Bord

- **Vue d'ensemble** : `/dashboard`
  - Liste des appareils avec état en temps réel
  - Indicateurs de présence
  - Scénario IA actif
  - Luminosité ambiante
  - Statut smart dimming

### Gestion des Appareils

- **Liste des appareils** : `/devices`
  - Filtrage par type (lampe, prise)
  - Filtrage par localisation
  - Contrôle ON/OFF
  - Ajustement d'intensité (slider)
  - Création/édition/suppression

### Règles d'Automatisation

- **Gestion des règles** : `/rules`
  - Liste des règles actives/inactives
  - Création de règles IF-THEN
  - Édition et suppression
  - Test manuel des règles

### Smart Dimming

- **Interface smart dimming** : `/smart-dimming`
  - Jauge de luminosité ambiante en temps réel
  - Graphique d'évolution (24h)
  - Historique des ajustements automatiques
  - Toggle pour activer/désactiver
  - Pause temporaire par appareil

### Historique et Visualisation

- **Présence** : `/presence`
  - Graphique des détections sur 24h
  - Filtrage par localisation
  - Identification des utilisateurs (via MAC Bluetooth)

- **Luminosité** : `/light-readings`
  - Graphique en courbe de l'évolution
  - Superposition avec intensité des lampes
  - Visualisation de l'impact du smart dimming

- **Événements** : `/events`
  - Journal chronologique
  - Filtrage par appareil, type, source
  - Recherche par date

### Intelligence Artificielle

- **Interface IA** : `/ai`
  - Affichage du scénario actif (Day, Night, Evening, Away)
  - Métriques du modèle (accuracy, état)
  - Prédictions d'intensité
  - Recommandations (si Ollama configuré)

### Administration

- **Interface admin** : `/admin`
  - Statistiques globales du système
  - Vue d'ensemble des utilisateurs
  - Appareils par type et état
  - Événements récents
  - (Accès réservé aux administrateurs)

## Architecture

### App Router (Next.js 16)

L'application utilise le nouveau App Router de Next.js avec :
- **Server Components** : Par défaut pour les composants
- **Client Components** : Marqué avec `"use client"` pour l'interactivité
- **Layouts** : Layouts imbriqués pour les routes protégées
- **Route Groups** : `(protected)` pour organiser les routes

### Authentification

- **Middleware** : Vérification du token JWT avant d'accéder aux routes protégées
- **Stockage** : Token stocké dans les cookies ou localStorage
- **Refresh** : Gestion automatique de l'expiration (redirection vers login)

### Client API

Le client API (`lib/api.ts`) :
- **Base URL** : Configuré via `NEXT_PUBLIC_API_URL`
- **Headers** : Ajout automatique du token JWT dans `Authorization: Bearer {token}`
- **Gestion d'erreurs** : Interception des erreurs 401 (redirection login)
- **Types** : Types TypeScript générés depuis les schémas backend

### Composants UI

L'application utilise **shadcn/ui** (basé sur Radix UI) :
- Composants accessibles (ARIA)
- Personnalisables via Tailwind CSS
- Mode sombre/clair supporté
- Responsive design

### State Management

- **Server State** : React Query ou SWR (optionnel, pour cache)
- **Client State** : React hooks (useState, useContext)
- **Form State** : React Hook Form

## Déploiement

### Build de Production

```bash
# Build optimisé
npm run build

# Vérifier le build
npm run start
```

### Déploiement Vercel (Recommandé)

1. Connecter le repository GitHub/GitLab
2. Configurer les variables d'environnement dans Vercel
3. Déployer automatiquement à chaque push

### Déploiement Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Variables d'Environnement en Production

Assurer que `NEXT_PUBLIC_API_URL` pointe vers le backend en production.

## Dépannage

### Erreur de connexion au backend

- Vérifier que `NEXT_PUBLIC_API_URL` est correct
- Vérifier que le backend est accessible depuis le navigateur
- Vérifier les CORS dans le backend

### Erreur d'authentification

- Vérifier que le token JWT est valide
- Vérifier l'expiration du token
- Se reconnecter si nécessaire

### Erreurs de build

- Vérifier la version de Node.js (18+)
- Supprimer `.next` et `node_modules`, puis réinstaller
- Vérifier les erreurs TypeScript : `npm run lint`

## Ressources

- [Documentation Next.js](https://nextjs.org/docs)
- [Documentation React](https://react.dev)
- [Documentation Tailwind CSS](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Radix UI](https://www.radix-ui.com)

---

**Note** : Cette interface web est en développement actif. Certaines fonctionnalités peuvent être partiellement implémentées.
