# SmartHome Lite

## Abstract
SmartHome Lite est un système de domotique distribué et embarqué développé pour le projet académique SAE BUT3 FA 2025. Il combine un Raspberry Pi pour la supervision matérielle, un backend FastAPI pour la logique métier et la persistance (PostgreSQL), et une application mobile Android (Kotlin + Jetpack Compose) pour le pilotage et la visualisation. Un classifieur Decision Tree adapte automatiquement les scénarios (jour, nuit, absence, soirée) pour optimiser l’éclairage et le contrôle des appareils. Les échanges se font via des API REST sécurisées (JWT, API Key). L’architecture privilégie la modularité, l’historisation des événements et l’intégration de règles et d’IA pour une domotique contextuelle et évolutive.

---

## Principales fonctionnalités
- Contrôle manuel et automatisé des éclairages et appareils.
- Détection de présence et scénarios contextuels basés sur un Decision Tree.
- Moteur de règles pour exécuter des automatisations conditionnelles.
- Historisation des événements et état des appareils (base PostgreSQL).
- API REST sécurisée (JWT pour les utilisateurs, clés API pour les périphériques).
- Application mobile Android pour supervision en temps réel.

## Architecture
- Raspberry Pi exécutant un service Flask pour capteurs/actionneurs.
- Backend : FastAPI (logique métier, API, moteur de règles, module IA).
- Base de données : PostgreSQL.
- Client mobile : Kotlin + Jetpack Compose (Android).
- Communication : API REST (HTTPS), JWT, API Keys.

## Intelligence artificielle
- Modèle : Decision Tree Classifier.
- Objectif : classifier le contexte d’utilisation pour sélectionner le scénario adapté (ex. jour, nuit, absence, soirée).
- Usage : ajuster automatiquement les règles et les paramètres d’actionneurs.

## Sécurité
- Authentification des utilisateurs via JWT.
- Authentification des périphériques via clés API.
- Recommandation : utiliser TLS/HTTPS en production et rotation des clés.

## Déploiement rapide (local / dev)
1. Préparer PostgreSQL et créer la base.
2. Lancer le backend FastAPI (uvicorn).
3. Déployer le service Flask sur le Raspberry Pi et connecter à l’API backend.
4. Installer l’application Android sur un appareil de test.
5. Charger ou entraîner le Decision Tree avec les données d’historique.

## Structure du dépôt
- /backend — FastAPI, logique métier, IA, migrations.
- /raspberrypi — service Flask pour capteurs/actionneurs.
- /mobile — application Android (Kotlin + Jetpack Compose).
- /db — scripts SQL / migrations.
- /docs — documentation supplémentaire.
