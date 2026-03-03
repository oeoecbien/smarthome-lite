# SmartHome Lite

## Table des Matières

- [1. Contexte et Objectifs](#1-contexte-et-objectifs)
  - [1.1 Contexte du Projet](#11-contexte-du-projet)
  - [1.2 Contraintes du Projet](#12-contraintes-du-projet)
  - [1.3 Objectifs Prioritaires](#13-objectifs-prioritaires)
- [2. Architecture Globale](#2-architecture-globale)
  - [2.1 Vue d'Ensemble](#21-vue-densemble)
  - [2.2 Architecture Modulaire](#22-architecture-modulaire)
  - [2.3 Composants Principaux](#23-composants-principaux)
  - [2.4 Base de Données avec TimescaleDB](#24-base-de-données-avec-timescaledb)
  - [2.5 Configuration Matérielle Raspberry Pi](#25-configuration-matérielle-raspberry-pi)
- [3. Fonctionnalités Principales](#3-fonctionnalités-principales)
  - [3.1 Vision d'Ensemble du Système](#31-vision-densemble-du-système)
  - [3.2 Contrôle Manuel des Appareils](#32-contrôle-manuel-des-appareils)
    - [F1 : Gestion des Lampes](#f1--gestion-des-lampes)
    - [F2 : Gestion des Prises](#f2--gestion-des-prises)
    - [F3 : Tableau de Bord Centralisé](#f3--tableau-de-bord-centralisé)
  - [3.3 Détection de Présence](#33-détection-de-présence)
    - [F4 : Système de Détection](#f4--système-de-détection)
    - [F5 : Historique de Présence](#f5--historique-de-présence)
  - [3.4 Automatisation Intelligente](#34-automatisation-intelligente)
    - [F6 : Moteur de Règles IF-THEN](#f6--moteur-de-règles-if-then)
    - [F7 : Scénarios Prédéfinis](#f7--scénarios-prédéfinis)
  - [3.5 Intelligence Artificielle et Adaptation Contextuelle](#35-intelligence-artificielle-et-adaptation-contextuelle)
    - [F8 : Intelligence Artificielle Multi-Modèles](#f8--intelligence-artificielle-multi-modèles)
      - [F8.1 : Classification de Scénarios (Améliorée)](#f81--classification-de-scénarios-améliorée)
      - [F8.2 : Régression pour Prédiction d'Intensité (Nouveau)](#f82--régression-pour-prédiction-dintensité-nouveau)
      - [F8.3 : Clustering des Habitudes Utilisateur (Nouveau)](#f83--clustering-des-habitudes-utilisateur-nouveau)
      - [F8.4 : Pipeline d'Inférence](#f84--pipeline-dinférence)
    - [F9 : Adaptation Dynamique à la Luminosité (Smart Dimming)](#f9-adaptation-dynamique-à-la-luminosité-smart-dimming)
  - [3.6 Visualisation](#36-visualisation)
    - [F10 : Graphique de Présence](#f10--graphique-de-présence)
    - [F11 : Graphique de Luminosité](#f11--graphique-de-luminosité)
- [4. Base de Données](#4-base-de-données)
  - [4.1 Choix Technologique](#41-choix-technologique)
  - [4.2 Schéma de Données Complet](#42-schéma-de-données-complet)
  - [4.3 Relations entre Tables](#43-relations-entre-tables)
  - [4.4 Volumétrie Estimée](#44-volumétrie-estimée)
- [5. Technologies et Stack Technique](#5-technologies-et-stack-technique)
  - [5.1 Backend (Serveur)](#51-backend-serveur)
  - [5.2 Raspberry Pi (Contrôleur)](#52-raspberry-pi-contrôleur)
  - [5.3 Application Mobile (Android)](#53-application-mobile-android)
  - [5.4 Application Web (Next.js)](#54-application-web-nextjs)
- [6. Communication entre Composants](#6-communication-entre-composants)
  - [6.1 Protocoles](#61-protocoles)
  - [6.2 Flux de Données : Allumage d'une Lampe (Contrôle Manuel)](#62-flux-de-données--allumage-dune-lampe-contrôle-manuel)
  - [6.3 Flux de Données : Détection de Présence avec Règle](#63-flux-de-données--détection-de-présence-avec-règle)
  - [6.4 Flux de Données : Smart Dimming (Adaptation Dynamique)](#64-flux-de-données--smart-dimming-adaptation-dynamique)
  - [6.5 API Endpoints Principaux](#65-api-endpoints-principaux)
- [7. Sécurité](#7-sécurité)
  - [7.1 Authentification](#71-authentification)
  - [7.2 Hachage des Mots de Passe](#72-hachage-des-mots-de-passe)
  - [7.3 Validation des Entrées](#73-validation-des-entrées)
  - [7.4 HTTPS / TLS](#74-https--tls)
  - [7.5 Sécurité Raspberry Pi](#75-sécurité-raspberry-pi)
- [8. Déploiement](#8-déploiement)
  - [8.1 Environnement de Déploiement](#81-environnement-de-déploiement)
  - [8.2 Installation Backend](#82-installation-backend)
  - [8.3 Installation Raspberry Pi](#83-installation-raspberry-pi)
  - [8.4 Application Web (Next.js)](#84-application-web-nextjs)
  - [8.5 Déploiement Application Mobile](#85-déploiement-application-mobile)
  - [8.6 Scripts de Déploiement Automatisé](#86-scripts-de-déploiement-automatisé)
- [9. Livrables](#9-livrables)
  - [9.1 Code Source](#91-code-source)
  - [9.2 Documentation](#92-documentation)
  - [9.3 Application Mobile](#93-application-mobile)
  - [9.4 Vidéo de Démonstration](#94-vidéo-de-démonstration)
  - [9.5 Présentation Orale](#95-présentation-orale)

---

## 1. Contexte et Objectifs

### 1.1 Contexte du Projet

**Cadre académique :** Projet de développement distribué et embarqué - SAE BUT3 FA 2025

**Problématique :** Développement d'un système de gestion intelligente d'éclairage et d'appareils électriques pour l'habitat, avec détection de présence, adaptation à la luminosité ambiante et automatisation basée sur l'intelligence artificielle.

### 1.2 Contraintes du Projet

- **Durée :** 50 heures
- **Équipe :** 4 étudiants
- **Matériel disponible :** 
  - Un Raspberry Pi par étudiant
  - Actionneurs : ampoules dimmables, prises connectées
  - Bluetooth intégré du Raspberry Pi pour détection de présence
  - Capteurs de luminosité (LDR ou BH1750)

### 1.3 Objectifs Prioritaires

1. Développement d'un **service distribué** déployé sur serveur
2. Intégration d'au moins un **Raspberry Pi** dans l'architecture
3. Hébergement d'une **base de données** sur le système
4. Développement d'une **application mobile** (Kotlin + Jetpack Compose)
5. Intégration d'un **algorithme d'IA** pour classification de scénarios et adaptation contextuelle
6. Contrôle à distance des appareils électriques
7. Détection automatique de présence
8. **Adaptation dynamique à la luminosité ambiante** (smart dimming)
9. Automatisation intelligente par règles

---

## 2. Architecture Globale

### 2.1 Vue d'Ensemble

Le système SmartHome Lite est organisé en **architecture modulaire monolithique** avec séparation claire des responsabilités. Cette architecture permet un développement efficace tout en maintenant une structure claire et maintenable.

**Principes architecturaux :**
- **Modularité** : Séparation des responsabilités en modules indépendants
- **Services** : Logique métier isolée et testable
- **ORM** : SQLAlchemy pour l'accès aux données
- **Validation** : Pydantic pour la validation des données
- **IA multi-modèles** : Classification, régression et clustering
- **Temps réel** : WebSockets pour synchronisation instantanée (optionnel)

### 2.2 Architecture Modulaire

```
┌──────────────────────────────────────────────────────────────────┐
│     APPLICATION MOBILE (Kotlin + Compose)   │  APPLICATION WEB   │
│  • HTTP/REST Client, Optimistic UI         │  (Next.js + React)  │
│                                            │  • Dashboard, Admin │
└──────────────────────┬─────────────────────┴──────────┬───────────┘
                       │                                │
                       │ HTTP/REST, JWT                 │ HTTP/REST, JWT
                       └────────────────┬───────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                         │
│              Architecture Modulaire Monolithique                 │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Routes     │  │   Services   │  │   Models     │            │
│  │              │  │              │  │              │            │
│  │ • auth       │  │ • ai_service │  │ • User       │            │
│  │ • devices    │  │ • device_    │  │ • Device     │            │
│  │ • rules      │  │   service    │  │ • Rule       │            │
│  │ • ai         │  │ • rule_      │  │ • Presence   │            │
│  │ • presence   │  │   engine     │  │ • LightRead  │            │
│  │ • smart_     │  │ • smart_     │  │              │            │
│  │   dimming    │  │   dimming    │  │              │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │   Schemas    │  │    Utils     │                              │
│  │  (Pydantic)  │  │              │                              │
│  │              │  │ • auth (JWT) │                              │
│  │ • Validation │  │ • validators │                              │
│  └──────────────┘  └──────────────┘                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Machine Learning (ML)                         │  │
│  │  • generate_data.py                                        │  │
│  │  • train_model.py                                          │  │
│  │  • models/scenario_classifier.pkl                          │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            │ SQLAlchemy ORM
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DATABASE                                      │
│              (PostgreSQL + TimescaleDB)                          │
│  • Tables relationnelles (users, devices, rules)                 │
│  • Hypertables pour time-series (light_readings)                 │
│  • Partitioning automatique                                      │
└──────────────────────────────────────────────────────────────────┘
                       ▲
                       │
                       │ HTTP/REST + API Key
                       │
┌──────────────────────────────────────────────────────────────────┐
│              RASPBERRY PI (Multiples)                            │
│  • Flask API locale                                              │
│  • Capteurs (Bluetooth, luminosité)                              │
│  • Actionneurs (LED, relais)                                     │
│  • Envoie événements au backend                                  │
│  • Reçoit commandes du backend                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 Composants Principaux

Le backend est organisé en modules fonctionnels clairement séparés :

#### Module Authentification
- Gestion des utilisateurs (CRUD)
- Authentification JWT
- Hachage des mots de passe (bcrypt)

#### Module Gestion des Appareils
- CRUD appareils
- Contrôle des états (ON/OFF, brightness)
- Communication avec Raspberry Pi
- Gestion des mesures de luminosité
- Gestion de la présence

#### Module Intelligence Artificielle
- Classification de scénarios (Decision Tree)
- Régression pour prédiction d'intensité (Random Forest)
- Clustering des habitudes (K-Means) - À implémenter
- Gestion des modèles ML

#### Module Règles d'Automatisation
- CRUD règles
- Moteur IF-THEN pour évaluation des règles
- Déclenchement automatique d'actions

#### Module Smart Dimming
- Ajustement intelligent de l'éclairage
- Adaptation à la luminosité ambiante
- Historique des ajustements

### 2.4 Base de Données avec TimescaleDB

**PostgreSQL standard :**
- Tables relationnelles (users, devices, rules, etc.)
- Relations et contraintes d'intégrité
- Index optimisés

**TimescaleDB (extension) :**
- Hypertables pour données time-series (sensor_readings)
- Partitioning automatique par temps
- Agrégations optimisées (moyennes horaires, etc.)
- Rétention automatique des données anciennes

**Optimisations :**
- Index composites sur (raspberry_pi_id, time DESC)
- Vues matérialisées pour statistiques
- Partitioning des tables d'historique (par mois)

### 2.5 Configuration Matérielle Raspberry Pi

#### Détection de Présence Bluetooth
- **Fonction :** Détection de présence via scan Bluetooth des devices à proximité
- **Technologie :** Bluetooth Classic (pybluez) ou Bluetooth Low Energy (bleak)
- **Portée :** Variable selon la force du signal (RSSI)
- **Avantages :**
  - Identification des personnes via leurs devices (téléphone, montre, etc.)
  - Pas de matériel supplémentaire requis (Bluetooth intégré au Raspberry Pi)
  - Détection de la force du signal (RSSI) pour estimer la proximité
  - Association MAC address → utilisateur pour identification personnalisée
- **Configuration :**
  - Intervalle de scan : 30 secondes (configurable)
  - Durée du scan : 10 secondes (configurable)
  - Seuil RSSI : -80 dBm par défaut (configurable)
  - Liste de devices connus : optionnelle (vide = tous les devices)

#### Capteur de Luminosité BH1750 (I²C)
- **Fonction :** Mesure de l'intensité lumineuse ambiante
- **Plage :** 1 à 65535 lux
- **Précision :** ±20 lux
- **Interface :** I²C
- **Branchement :**
  - Alimentation : 3.3V (Pin 1)
  - Masse : GND (Pin 9)
  - SDA : GPIO 2 (Pin 3)
  - SCL : GPIO 3 (Pin 5)

#### Alternative : Capteur LDR (Photorésistance)
- **Fonction :** Mesure de la luminosité par variation de résistance
- **Composants associés :** Convertisseur ADC (MCP3008)
- **Interface :** SPI
- **Plage relative :** 0-100% (conversion analogique-numérique)

#### Ampoule LED Dimmable
- **Contrôle :** PWM (Modulation de largeur d'impulsion)
- **Intensité :** Variable 0-100%
- **Fréquence PWM :** 1000 Hz
- **GPIO utilisé :** GPIO 18 (Pin 12)
- **Composants :** Transistor NPN (BC547), résistance 220 ohms

#### Prise Connectée
- **Contrôle :** Module relais 5V
- **Type :** ON/OFF binaire
- **Charge max :** 250V AC / 10A
- **GPIO utilisé :** GPIO 23 (Pin 16)

---

## 3. Fonctionnalités Principales

### 3.1 Vision d'Ensemble du Système

**Le système SmartHome Lite opère sur trois niveaux d'intelligence :**

1. **Contrôle manuel :** L'utilisateur pilote directement les appareils via l'application mobile (allumer, éteindre, régler l'intensité).

2. **Automatisations déterministes :** Des règles IF-THEN prédéfinies déclenchent automatiquement des actions selon des conditions fixes (présence, heure, jour, luminosité).

3. **Adaptation contextuelle intelligente :** Un module d'IA classifie le contexte d'utilisation (jour, nuit, soirée, absence) et un système de **smart dimming** ajuste dynamiquement l'intensité lumineuse en fonction de la luminosité naturelle mesurée en temps réel.

**Cette architecture progressive permet au système de passer d'un simple automate à un assistant domotique véritablement adaptatif.**

**Note importante :** L'IA de classification ne "décide" pas de manière autonome : elle reconnaît un contexte parmi quatre scénarios prédéfinis et applique les comportements statiques associés. Le véritable caractère "intelligent" du système réside dans le **smart dimming**, qui adapte dynamiquement l'intensité lumineuse en combinant mesures physiques, règles et préférences apprises.

### 3.2 Contrôle Manuel des Appareils

#### F1 : Gestion des Lampes
**Fonctionnalités :**
- Allumage et extinction individuels
- Ajustement de l'intensité lumineuse (slider 0-100%)
- Affichage en temps réel de l'état
- Temps de réponse garanti < 2 secondes

**Interface mobile :**
- Carte par lampe avec icône et nom
- Toggle switch ON/OFF
- Slider d'intensité (si lampe dimmable)
- Indicateur visuel de l'intensité actuelle

#### F2 : Gestion des Prises
**Fonctionnalités :**
- Activation et désactivation ON/OFF
- Affichage de l'état actuel (actif/inactif)
- Confirmation visuelle immédiate

**Interface mobile :**
- Carte par prise avec icône et nom
- Toggle switch ON/OFF
- Indicateur d'état coloré

#### F3 : Tableau de Bord Centralisé
**Fonctionnalités :**
- Vue d'ensemble de tous les appareils connectés
- Indicateurs visuels d'état (actif/inactif/erreur)
- Rafraîchissement automatique périodique (toutes les 5 secondes)
- Organisation par pièce
- Affichage du scénario actif (jour, nuit, soirée, absence)
- Indicateur de luminosité ambiante en temps réel
- Statut du mode smart dimming (actif/inactif)

### 3.3 Détection de Présence

#### F4 : Système de Détection
**Fonctionnalités :**
- Détection en temps réel via scan Bluetooth périodique
- Enregistrement horodaté des événements avec adresse MAC et force du signal (RSSI)
- Filtrage anti-rebond (ignorer détections < 5 secondes)
- Association avec la localisation (pièce)
- Identification des utilisateurs via mapping MAC address → utilisateur (table `bluetooth_devices`)

**Implémentation technique :**
Le Raspberry Pi scanne périodiquement les devices Bluetooth à proximité (toutes les 30 secondes par défaut). Chaque device détecté est identifié par son adresse MAC et sa force de signal (RSSI). Le système peut mapper les adresses MAC aux utilisateurs via la table `bluetooth_devices`, permettant une identification personnalisée. Chaque détection validée génère un événement envoyé immédiatement au serveur backend avec les informations Bluetooth (MAC, RSSI, user_id si mappé).

#### F5 : Historique de Présence
**Fonctionnalités :**
- Liste chronologique des dernières détections
- Filtrage par date et localisation
- Statistiques de base par appareil
- Graphique des détections sur 24 heures

### 3.4 Automatisation Intelligente

#### F6 : Moteur de Règles IF-THEN

Le moteur de règles permet de définir des automatisations déterministes simples mais puissantes.

**Conditions disponibles :**
- Détection de présence (booléen + localisation)
- Plage horaire (format 24h)
- Jour de la semaine (lundi à dimanche)
- État d'un appareil spécifique
- **Niveau de luminosité ambiante** (seuil en lux ou pourcentage)

**Actions disponibles :**
- Allumer ou éteindre un appareil
- Définir une intensité lumineuse spécifique
- Activer un scénario prédéfini
- **Activer/désactiver le mode smart dimming**

**Exemples de règles :**

1. **Règle présence soirée :**
   - **Condition :** Présence détectée dans le salon ET heure entre 18h et 23h
   - **Action :** Allumer lampe salon à 70%

2. **Règle économie d'énergie :**
   - **Condition :** Aucune présence pendant 10 minutes
   - **Action :** Éteindre toutes les lampes

3. **Règle luminosité naturelle élevée :**
   - **Condition :** Luminosité ambiante > 500 lux ET heure entre 9h et 17h
   - **Action :** Réduire intensité lampe bureau à 20%

4. **Règle crépuscule :**
   - **Condition :** Luminosité < 100 lux ET présence détectée
   - **Action :** Activer smart dimming à 80%

**Format JSON des règles :**
Les règles sont stockées en base de données au format JSONB, permettant une flexibilité maximale dans la définition des conditions et actions.

#### F7 : Scénarios Prédéfinis

Les scénarios définissent des comportements globaux adaptés au contexte. **L'IA identifie automatiquement le scénario actuel**, et le système applique les paramètres correspondants.

**Mode Jour (6h - 18h)**
- Désactivation automatique des lampes si absence détectée
- Intensité maximale (100%) si allumage manuel
- Smart dimming actif : réduction si luminosité naturelle élevée
- Seuil de luminosité basse : 300 lux
- Priorité à l'économie d'énergie

**Mode Soirée (18h - 23h)**
- Intensité modérée (60-80%) pour le confort visuel
- Activation automatique sur détection de présence
- Smart dimming actif avec adaptation progressive
- Seuil de luminosité basse : 150 lux
- Transition douce entre intensités (fade de 2 secondes)

**Mode Nuit (23h - 6h)**
- Intensité minimale (20-30%) pour les déplacements nocturnes
- Réduction du temps d'activation automatique (délai réduit à 1 minute)
- Smart dimming désactivé (priorité confort nocturne)
- Extinction automatique après 2 minutes sans détection

**Mode Absence**
- Extinction de tous les appareils non essentiels
- Enregistrement des détections sans action automatique
- Smart dimming désactivé
- Possibilité de simulation de présence (allumages aléatoires)

### 3.5 Intelligence Artificielle et Adaptation Contextuelle

#### F8 : Intelligence Artificielle Multi-Modèles

**Objectif :**
Le système utilise **trois modèles d'IA complémentaires** pour offrir une intelligence adaptative avancée : classification de contexte, prédiction d'intensité optimale, et détection automatique de profils utilisateur.

**Architecture IA :**
- **Classification** : Reconnaissance du scénario contextuel (Decision Tree amélioré)
- **Régression** : Prédiction de l'intensité lumineuse optimale (Random Forest)
- **Clustering** : Détection automatique des habitudes utilisateur (K-Means)

##### F8.1 : Classification de Scénarios (Améliorée)

**Algorithme :** Decision Tree Classifier (scikit-learn) avec features enrichies

**Variables d'entrée (Features améliorées) :**

| Variable | Type | Plage | Description |
|----------|------|-------|-------------|
| hour | Entier | 0-23 | Heure actuelle de la journée |
| day_of_week | Entier | 0-6 | Jour de la semaine (0=Lundi, 6=Dimanche) |
| presence_detected | Booléen | 0/1 | Mouvement détecté dans les 5 dernières minutes |
| light_on | Booléen | 0/1 | Au moins une lampe est allumée actuellement |
| ambient_light_level | Entier | 0-100 | Niveau de luminosité ambiante (pourcentage) |
| temperature | Float | 15-30 | Température ambiante en °C (optionnel) |
| last_motion_time | Entier | 0-1440 | Minutes depuis dernière détection |

**Scénarios (Labels) :**

| Scénario | Valeur | Description |
|----------|--------|-------------|
| Day | 0 | Journée normale, lumière naturelle suffisante |
| Night | 1 | Période nocturne, éclairage minimal nécessaire |
| Away | 2 | Absence prolongée, économie d'énergie prioritaire |
| Evening | 3 | Soirée détente, ambiance lumineuse |

**Objectifs de performance :**
- Accuracy minimale : **75%** (amélioré de 70%)
- Temps d'inférence : < 100 millisecondes
- Rafraîchissement : toutes les 2 minutes
- F1-score par classe : > 0.70

**Méthodologie d'entraînement :**
1. Génération de données synthétiques cohérentes (1000 échantillons minimum)
2. Division train/test/validation : 70/15/15
3. Entraînement avec Decision Tree (max_depth=7, min_samples_split=10)
4. Optimisation hyperparamètres (GridSearchCV)
5. Évaluation avec matrice de confusion et classification report
6. Sauvegarde du modèle au format joblib
7. Rechargement automatique au démarrage du service IA

##### F8.2 : Régression pour Prédiction d'Intensité (Nouveau)

**Algorithme :** Random Forest Regressor (scikit-learn)

**Objectif :**
Prédire l'intensité lumineuse optimale (0-100%) selon le contexte et les préférences historiques de l'utilisateur.

**Variables d'entrée (Features) :**

| Variable | Type | Plage | Description |
|----------|------|-------|-------------|
| ambient_light_lux | Entier | 0-65535 | Luminosité ambiante mesurée (lux) |
| hour | Entier | 0-23 | Heure actuelle |
| day_of_week | Entier | 0-6 | Jour de la semaine |
| user_preference_avg | Float | 0-100 | Intensité moyenne préférée par l'utilisateur (historique) |
| room_type | Catégoriel | salon/chambre/bureau | Type de pièce |
| scenario | Entier | 0-3 | Scénario actif (de la classification) |
| weather_condition | Catégoriel | ensoleillé/nuageux/sombre | Condition météo (API externe optionnel) |

**Variable cible :**
- `target_brightness` : Intensité lumineuse optimale (0-100%)

**Objectifs de performance :**
- R² score : > 0.80
- MAE (Mean Absolute Error) : < 10%
- Temps d'inférence : < 150 millisecondes

**Méthodologie d'entraînement :**
1. Collecte de données historiques (user_preferences, dimming_adjustments)
2. Feature engineering (normalisation, encodage catégoriel)
3. Division train/validation : 80/20
4. Entraînement Random Forest (n_estimators=100, max_depth=15)
5. Validation croisée (5-fold)
6. Évaluation avec métriques de régression
7. Sauvegarde du modèle

**Apprentissage continu :**
- Le modèle peut être réentraîné périodiquement avec de nouvelles données
- Feedback utilisateur : si l'utilisateur ajuste manuellement après une prédiction, c'est enregistré
- Réentraînement automatique tous les 7 jours (optionnel)

##### F8.3 : Clustering des Habitudes Utilisateur (Nouveau)

**Algorithme :** K-Means Clustering (scikit-learn)

**Objectif :**
Détecter automatiquement les profils d'utilisation pour personnaliser le comportement du système.

**Variables d'entrée (Features) :**

| Variable | Type | Description |
|----------|------|-------------|
| avg_hour_on | Float | Heure moyenne d'allumage des lampes |
| avg_hour_off | Float | Heure moyenne d'extinction |
| avg_brightness | Float | Intensité moyenne préférée |
| usage_frequency | Float | Nombre d'utilisations par jour |
| weekend_vs_weekday | Float | Ratio d'utilisation weekend/semaine |
| presence_duration_avg | Float | Durée moyenne de présence détectée |

**Profils détectés (K=4) :**
- **Early Bird** : Lever tôt, coucher tôt, intensité élevée le matin
- **Night Owl** : Lever tard, coucher tard, intensité faible le matin
- **Regular** : Horaires réguliers, intensité modérée
- **Minimal** : Utilisation minimale, intensité faible

**Utilisation :**
- Le système adapte les recommandations selon le profil détecté
- Les règles par défaut peuvent être ajustées selon le profil
- Visualisation dans l'application mobile

**Méthodologie :**
1. Collecte de données d'utilisation sur 2 semaines minimum
2. Normalisation des features
3. Clustering K-Means (K=4, init='k-means++', n_init=10)
4. Évaluation avec silhouette score
5. Attribution du profil à l'utilisateur
6. Mise à jour périodique (tous les 14 jours)

##### F8.4 : Pipeline d'Inférence

**Flux d'exécution :**

```
1. Nouvelle mesure de luminosité reçue
   ↓
2. Classification : Déterminer le scénario actif
   ↓
3. Récupération des préférences utilisateur (historique)
   ↓
4. Régression : Prédire l'intensité optimale
   ↓
5. Clustering : Vérifier le profil utilisateur (si disponible)
   ↓
6. Ajustement final selon profil + scénario
   ↓
7. Application de l'intensité calculée
   ↓
8. Enregistrement pour apprentissage futur
```

**Performance globale :**
- Temps total d'inférence : < 300ms
- Précision globale : > 80% de satisfaction utilisateur
- Apprentissage continu activé

#### F9 : Adaptation Dynamique à la Luminosité (Smart Dimming) - **Véritable Intelligence**

**Objectif :**
Ajuster automatiquement et dynamiquement l'intensité lumineuse des lampes en fonction de la luminosité naturelle mesurée en temps réel, du scénario actif et des préférences utilisateur.

**C'est ici que réside la véritable intelligence adaptative du système.**

**Principe de fonctionnement :**

Le système combine trois sources d'information pour calculer l'intensité optimale :

1. **Mesure physique :** Luminosité ambiante mesurée par le capteur (en lux)
2. **Contexte IA :** Scénario actif détecté par le Decision Tree
3. **Règles métier :** Plages de luminosité et seuils prédéfinis par scénario

**Algorithme d'ajustement :**

L'intensité cible est calculée par interpolation linéaire entre des points de référence :

- Si luminosité naturelle > 70%, réduire l'intensité artificielle à 30%
- Si luminosité < 20%, augmenter à 80% (voire 100% en mode nuit)
- Entre les deux, interpolation progressive

**Paramètres par scénario :**

**Mode Jour :**
- Seuil haut : 500 lux → intensité cible 20%
- Seuil bas : 200 lux → intensité cible 70%
- Interpolation linéaire entre les deux
- Réactivité : ajustement immédiat (< 1 seconde)

**Mode Soirée :**
- Seuil haut : 150 lux → intensité cible 50%
- Seuil bas : 50 lux → intensité cible 80%
- Interpolation douce avec fade progressif (2 secondes)
- Effet graduel à mesure que la luminosité extérieure baisse

**Mode Nuit :**
- Smart dimming désactivé par défaut
- Intensité fixe 30% pour confort nocturne
- Pas de variation automatique (éviter réveil)

**Mode Absence :**
- Smart dimming désactivé
- Lampes éteintes (sauf simulation de présence)

**Exemples concrets :**

**Exemple 1 : Journée ensoleillée**
- Luminosité mesurée : 800 lux
- Scénario IA : Day
- Présence détectée : Oui
- Action : Réduire intensité lampe bureau à 25%
- Justification : Lumière naturelle suffisante

**Exemple 2 : Crépuscule en soirée**
- Luminosité mesurée : 100 lux
- Scénario IA : Evening
- Présence détectée : Oui
- Action : Augmenter progressivement intensité salon de 50% à 75%
- Justification : Compensation de la baisse de lumière naturelle

**Exemple 3 : Ciel couvert en journée**
- Luminosité mesurée : 250 lux
- Scénario IA : Day
- Présence détectée : Oui
- Action : Ajuster intensité à 55% (interpolation)
- Justification : Complément de lumière nécessaire

**Avantages du smart dimming :**
- **Confort visuel :** Luminosité constante perçue par l'utilisateur
- **Économie d'énergie :** Réduction automatique quand la lumière naturelle est suffisante
- **Adaptation contextuelle :** Comportement différent selon le moment de la journée
- **Progressivité :** Transitions douces sans changements brusques

**Intégration temps réel :**

Le capteur de luminosité envoie des mesures toutes les 10 secondes au serveur backend. Le service smart dimming :

1. Récupère la luminosité actuelle
2. Interroge le service IA pour obtenir le scénario
3. Calcule l'intensité cible selon l'algorithme
4. Compare avec l'intensité actuelle des lampes allumées
5. Si écart > 10%, envoie une commande d'ajustement au Raspberry Pi
6. Applique un fade progressif (2 secondes en mode soirée, immédiat en jour)

**Possibilité d'apprentissage avancé (extension future) :**

Le système peut enregistrer les ajustements manuels effectués par l'utilisateur :
- Si l'utilisateur augmente souvent la lumière à 18h malgré le smart dimming, le système peut apprendre cette préférence
- Un modèle de régression linéaire peut être entraîné sur les données historiques (luminosité, heure, ajustement manuel)
- Le système prédit alors l'intensité préférée et l'applique automatiquement

**Cette fonctionnalité transforme le système d'un automate rigide en un assistant adaptatif apprenant les habitudes.**

**Contraintes techniques :**

- Précision du capteur : ±20 lux (suffisant pour l'algorithme)
- Latence capteur → ajustement : < 3 secondes
- Fréquence de mise à jour : 10 secondes (compromis réactivité/charge réseau)
- Protection contre les oscillations : hysteresis de 10% (éviter ajustements constants)

**Interface utilisateur :**

L'application mobile affiche :
- Indicateur visuel de luminosité ambiante (jauge colorée)
- Statut du smart dimming (actif/inactif/pause)
- Intensité cible calculée vs intensité actuelle
- Bouton pour désactiver temporairement (1 heure)
- Historique des ajustements automatiques

### 3.6 Visualisation

#### F10 : Graphique de Présence

**Fonctionnalité :**
- Graphique en barres des détections de présence sur les dernières 24 heures
- Intervalle : par heure
- Segmentation par pièce
- Code couleur par scénario actif

#### F11 : Graphique de Luminosité

**Fonctionnalité :**
- Graphique en courbe de l'évolution de la luminosité ambiante
- Période : 24 heures avec zoom ajustable
- Superposition avec l'intensité des lampes
- Visualisation de l'impact du smart dimming

**Intérêt pédagogique :**
Permet de visualiser la corrélation entre luminosité naturelle et ajustements automatiques, démontrant l'efficacité de l'algorithme adaptatif.

---

## 4. Base de Données

### 4.1 Choix Technologique

**SGBD :** PostgreSQL 14+

**Justification :**
- Fiabilité éprouvée
- Support natif du type JSONB pour les règles flexibles
- Performance des requêtes d'agrégation (historiques, statistiques)
- Licence open source
- Compatibilité avec SQLAlchemy

### 4.2 Schéma de Données Complet

#### Table : users
Gestion des utilisateurs du système.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- username : Nom d'utilisateur unique (50 caractères max)
- email : Adresse email unique (optionnelle)
- password_hash : Hash bcrypt du mot de passe
- created_at : Timestamp de création du compte

#### Table : raspberry_pis
Inventaire des Raspberry Pi connectés.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- name : Nom descriptif (ex: "RPi Salon")
- ip_address : Adresse IP unique (format IPv4)
- location : Pièce associée (ex: "Salon", "Chambre")
- is_online : Booléen indiquant la connectivité
- api_key : Clé API unique de 64 caractères pour authentification
- created_at : Timestamp d'ajout

#### Table : devices
Référentiel des appareils connectés. Chaque appareil appartient à un utilisateur.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- user_id : Clé étrangère vers users (propriétaire de l'appareil)
- name : Nom descriptif (ex: "Lampe bureau")
- type : Type d'appareil ('light', 'dimmer', 'socket')
- raspberry_pi_id : Clé étrangère vers raspberry_pis
- gpio_pin : Numéro du GPIO utilisé
- state : État actuel (ON/OFF)
- brightness : Intensité lumineuse (0-100, toujours défini)
- created_at : Timestamp de création

**Contraintes :**
- Combinaison (raspberry_pi_id, gpio_pin) unique
- Chaque utilisateur voit uniquement ses propres appareils

#### Table : presence
Historique des détections de présence via Bluetooth.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- raspberry_pi_id : Clé étrangère vers raspberry_pis
- detected_at : Timestamp de la détection
- device_mac_address : Adresse MAC du device Bluetooth détecté (format: AA:BB:CC:DD:EE:FF, optionnel)
- signal_strength : Force du signal RSSI en dBm (optionnel)
- user_id : ID de l'utilisateur associé (optionnel, si MAC mappée dans bluetooth_devices)

**Index :**
- Index sur detected_at pour requêtes temporelles rapides
- Index sur device_mac_address pour recherche par MAC
- Index sur user_id pour recherche par utilisateur

#### Table : light_readings
**Nouvelle table pour le smart dimming**

Historique des mesures de luminosité ambiante.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- raspberry_pi_id : Clé étrangère vers raspberry_pis
- lux_value : Valeur en lux mesurée (entier 0-65535)
- percentage : Pourcentage relatif (0-100, calculé)
- measured_at : Timestamp de la mesure

**Index :**
- Index sur (raspberry_pi_id, measured_at) pour requêtes temporelles par capteur

#### Table : events
Journal des événements système.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- device_id : Clé étrangère vers devices (nullable)
- event_type : Type d'événement (ex: 'light_on', 'dimming_adjusted')
- value : Valeur associée (format texte flexible)
- source : Source de l'événement ('manual', 'automatic', 'ai', 'smart_dimming')
- timestamp : Timestamp de l'événement

**Index :**
- Index sur (device_id, timestamp)

#### Table : rules
Définition des règles d'automatisation.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- name : Nom descriptif de la règle
- enabled : Booléen pour activer/désactiver
- condition : Conditions au format JSONB
- action : Actions au format JSONB
- created_at : Timestamp de création

**Format JSONB exemple :**

**Condition :**
```json
{
  "type": "AND",
  "clauses": [
    {"field": "light_level", "operator": "<", "value": 100},
    {"field": "presence", "operator": "==", "value": true}
  ]
}
```

**Action :**
```json
{
  "type": "set_brightness",
  "device_id": 3,
  "brightness": 80,
  "transition": "fade"
}
```

#### Table : training_data
Données d'entraînement pour l'algorithme d'IA.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- hour : Heure (0-23)
- day_of_week : Jour de la semaine (0-6)
- presence_detected : Booléen
- light_on : Booléen
- scenario : Label du scénario (0-3)
- created_at : Timestamp de génération

**Contraintes :**
- CHECK hour BETWEEN 0 AND 23
- CHECK day_of_week BETWEEN 0 AND 6
- CHECK scenario BETWEEN 0 AND 3

#### Table : dimming_adjustments
**Nouvelle table pour l'historique du smart dimming**

Enregistrement des ajustements automatiques d'intensité.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- device_id : Clé étrangère vers devices
- light_reading_id : Clé étrangère vers light_readings
- scenario : Scénario actif au moment de l'ajustement (0-3)
- previous_brightness : Intensité avant ajustement
- target_brightness : Intensité calculée par l'algorithme
- applied_brightness : Intensité réellement appliquée
- reason : Justification textuelle (ex: "High natural light")
- adjusted_at : Timestamp de l'ajustement

**Intérêt :**
Permet d'analyser l'efficacité du smart dimming et de détecter les patterns pour l'apprentissage futur.

#### Table : bluetooth_devices
**Nouvelle table pour l'identification des utilisateurs via Bluetooth**

Association entre adresses MAC Bluetooth et utilisateurs pour identification personnalisée.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- user_id : Clé étrangère vers users
- mac_address : Adresse MAC du device (format: AA:BB:CC:DD:EE:FF, unique)
- device_name : Nom descriptif (ex: "iPhone de Jean", "Montre de Marie")
- device_type : Type de device ('phone', 'watch', 'headphones', etc.)
- is_active : Booléen indiquant si le device est actif
- created_at : Timestamp de création
- updated_at : Timestamp de mise à jour

**Utilisation :**
Lorsqu'une détection Bluetooth est enregistrée, le système tente de mapper l'adresse MAC à un utilisateur via cette table. Si une correspondance est trouvée, le champ `user_id` de la table `presence` est automatiquement rempli, permettant une identification personnalisée.

#### Table : user_preferences
**Nouvelle table pour l'apprentissage des préférences**

Enregistrement des ajustements manuels effectués après un smart dimming.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- user_id : Clé étrangère vers users
- device_id : Clé étrangère vers devices
- light_level : Niveau de luminosité ambiante au moment de l'ajustement
- scenario : Scénario actif
- auto_brightness : Intensité proposée par le système
- manual_brightness : Intensité choisie par l'utilisateur
- time_of_day : Heure (0-23)
- recorded_at : Timestamp

**Utilisation future :**
Ces données peuvent alimenter un modèle de régression pour personnaliser le smart dimming par utilisateur.

### 4.3 Relations entre Tables

```
users (1) ----< (N) devices
    |
    +-------< (N) user_preferences
    |
    +-------< (N) bluetooth_devices

raspberry_pis (1) ----< (N) devices
    |
    +-------< (N) presence
    |           |
    |           +-----> (N) users (via user_id, optionnel)
    |
    +-------< (N) light_readings

devices (1) ----< (N) events
    |
    +-------< (N) dimming_adjustments

light_readings (1) ----< (N) dimming_adjustments

presence (N) ----< (1) bluetooth_devices (via device_mac_address, optionnel)

rules (standalone, références JSONB vers devices)
training_data (standalone, apprentissage automatique)
```

### 4.4 Volumétrie Estimée

**Échelle temporelle : 1 mois**

| Table | Fréquence | Nombre d'entrées |
|-------|-----------|-----------------|
| presence | 20 détections/jour/capteur | ~600/mois |
| light_readings | 1 mesure/10s/capteur | ~260 000/mois |
| events | Variable selon activité | ~1000/mois |
| dimming_adjustments | ~10 ajustements/jour/lampe | ~300/mois |
| user_preferences | ~5 ajustements manuels/jour | ~150/mois |

**Stratégies d'optimisation :**
- Archivage des données > 3 mois
- Agrégation des mesures de luminosité (moyenne horaire après 1 semaine)
- Purge des événements non critiques après 6 mois

---

## 5. Technologies et Stack Technique

### 5.1 Backend (Serveur)

**Langage et framework :**
- Python 3.9+
- FastAPI 0.104+
- Uvicorn (serveur ASGI)
- Gunicorn (production, optionnel)

**Base de données :**
- SQLAlchemy 2.0+ (ORM)
- psycopg2-binary (driver PostgreSQL)
- Alembic (migrations)
- TimescaleDB (extension PostgreSQL pour time-series)

**Sécurité :**
- Pydantic (validation de données)
- python-jose (gestion JWT)
- passlib avec bcrypt (hachage mots de passe)

**Intelligence artificielle :**
- scikit-learn 1.3+ (Decision Tree, Random Forest, K-Means)
- pandas 2.1+ (manipulation données)
- numpy 1.26+ (calculs)
- joblib (sérialisation modèles)
- scikit-optimize (optimisation hyperparamètres, optionnel)

**Communication HTTP :**
- httpx (client HTTP asynchrone)
- requests (client HTTP synchrone)

**Structure du projet :**

```
backend/
├── app/
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── config.py                  # Configuration centralisée
│   ├── database.py                # Connexion PostgreSQL
│   ├── dependencies.py            # Dépendances FastAPI (auth, DB)
│   │
│   ├── models/                    # Modèles SQLAlchemy
│   │   ├── user.py                # Utilisateurs
│   │   ├── device.py              # Appareils
│   │   ├── raspberry_pi.py        # Raspberry Pi
│   │   ├── presence.py            # Détections de présence
│   │   ├── light_reading.py       # Mesures de luminosité
│   │   ├── rule.py                # Règles d'automatisation
│   │   ├── event.py               # Événements système
│   │   ├── smart_dimming_adjustment.py  # Historique smart dimming
│   │   ├── training_data.py       # Données d'entraînement IA
│   │   └── user_preference.py     # Préférences utilisateur
│   │
│   ├── routes/                    # Endpoints API
│   │   ├── auth.py                # Authentification
│   │   ├── devices.py             # Gestion appareils
│   │   ├── raspberry_pis.py       # Gestion Raspberry Pi
│   │   ├── presence.py            # Détections de présence
│   │   ├── light_readings.py      # Mesures de luminosité
│   │   ├── rules.py               # Règles d'automatisation
│   │   ├── ai.py                  # Intelligence artificielle
│   │   ├── smart_dimming.py      # Smart dimming
│   │   └── events.py              # Historique événements
│   │
│   ├── schemas/                   # Schémas Pydantic
│   │   ├── auth.py                # Authentification
│   │   ├── device.py              # Appareils
│   │   ├── raspberry_pi.py        # Raspberry Pi
│   │   ├── rule.py                # Règles
│   │   └── smart_dimming.py       # Smart dimming
│   │
│   ├── services/                  # Logique métier
│   │   ├── ai_service.py          # Service IA
│   │   ├── device_service.py      # Contrôle appareils
│   │   ├── rule_engine.py         # Moteur de règles
│   │   └── smart_dimming_service.py  # Service smart dimming
│   │
│   └── utils/                     # Utilitaires
│       ├── auth.py                # Fonctions JWT
│       └── validators.py          # Validateurs personnalisés
│
├── ml/                            # Machine Learning
│   ├── generate_data.py           # Génération données synthétiques (classification)
│   ├── train_model.py             # Entraînement Decision Tree
│   ├── generate_regression_data.py # Données régression (intensité)
│   ├── train_regression_model.py   # Entraînement Random Forest (régression)
│   └── models/                    # Modèles sauvegardés (.pkl, métriques)
│
├── requirements.txt               # Dépendances Python
├── .env.example                   # Exemple de configuration
└── README.md                      # Documentation
```

### 5.2 Raspberry Pi (Contrôleur)

**Système d'exploitation :**
- Raspberry Pi OS Lite (Debian)

**Option Z-Wave (implémentation actuelle dans `raspberry/`) :**
- API Flask (`api_flask_zwave.py`) sur le port 5000, conforme au contrat backend SmartHome Lite
- Communication avec Z-Wave JS UI (Socket.IO / WebSocket) pour piloter ampoules et prises Z-Wave
- `gpio_pin` côté backend = `node_id` Z-Wave ; détection de présence via MultiSensor 7 (optionnel)
- Voir `raspberry/README.md` et `zwave-js/` pour Z-Wave JS UI

**Structure du projet (Z-Wave) :**
```
raspberry/
├── api_flask_zwave.py         # API Flask (état, luminosité, présence)
├── zwave_client.py            # Client Z-Wave JS (Socket.IO / WebSocket)
├── zwave_cache.py             # Cache nœuds Z-Wave
├── zwave_constants.py         # Constantes Z-Wave
├── config.py                  # Configuration (URLs, API Key)
└── requirements.txt
```

**Option GPIO / Bluetooth (référence) :**
- Flask 2.3+, Flask-CORS ; RPi.GPIO (LED, relais), pybluez ou bleak (présence), smbus2 (BH1750), spidev (LDR + MCP3008)
- Structure alternative : `sensors/` (bluetooth, light_sensor_*), `actuators/` (led_light, relay), `api/local_api.py`, `services/` (server_client, device_manager, event_reporter, light_monitor)

**Service light_monitor.py :**
Ce service lit périodiquement le capteur de luminosité et envoie les valeurs au backend :
- Fréquence : toutes les 10 secondes
- Format : JSON avec lux_value et timestamp
- Endpoint backend : POST /api/light_readings
- Gestion des erreurs de connexion avec retry

### 5.3 Application Mobile (Android)

**Langage :**
- Kotlin 1.9+

**UI :**
- Jetpack Compose (dernière version stable)
- Material Design 3

**Architecture :**
- Pattern MVVM (Model-View-ViewModel)
- StateFlow et Coroutines pour gestion asynchrone
- Hilt pour injection de dépendances

**Réseau :**
- Retrofit 2.9+ (client REST)
- OkHttp 4.11+ (gestion HTTP)
- Gson (sérialisation JSON)

**Persistance locale :**
- DataStore Preferences (stockage JWT)
- Room (cache local optionnel)

**Structure du projet :**

```
mobile/SmartHome/app/src/main/java/com/example/smarthome/
├── data/
│   ├── model/                  # Modèles de données (Device, Rule, etc.)
│   ├── remote/                 # Couche réseau (Retrofit)
│   │   ├── ApiService.kt
│   │   ├── AuthInterceptor.kt
│   │   └── dto/               # Data Transfer Objects
│   └── repository/             # Pattern Repository
│       ├── DeviceRepository.kt
│       ├── RuleRepository.kt
│       └── SmartDimmingRepository.kt
├── ui/
│   ├── screens/                # Écrans principaux
│   │   ├── DashboardScreen.kt
│   │   ├── DevicesScreen.kt
│   │   ├── RulesScreen.kt
│   │   ├── HistoryScreen.kt
│   │   └── SmartDimmingScreen.kt
│   ├── components/             # Composants réutilisables
│   │   ├── DeviceCard.kt
│   │   ├── BrightnessSlider.kt
│   │   ├── LightIndicator.kt
│   │   └── ScenarioChip.kt
│   └── theme/                  # Thème Material 3
├── viewmodel/                  # ViewModels
│   ├── DashboardViewModel.kt
│   ├── DeviceViewModel.kt
│   ├── RuleViewModel.kt
│   └── SmartDimmingViewModel.kt
├── di/                         # Modules Hilt
└── MainActivity.kt
```

**SmartDimmingScreen.kt :**
Écran dédié à la visualisation et au contrôle du smart dimming :
- Jauge de luminosité ambiante en temps réel
- Graphique d'évolution luminosité/intensité lampes (24h)
- Toggle pour activer/désactiver temporairement
- Liste des derniers ajustements automatiques avec justifications
- Indicateur du scénario actif

### 5.4 Application Web (Next.js)

**Framework :** Next.js 16+ (App Router), React 19, TypeScript. **UI :** Tailwind CSS 4, Radix UI, Recharts. **Fonctionnalités :** Authentification (login, JWT), tableau de bord (appareils, règles), pages admin (présence), graphiques présence/luminosité. **Structure :** `web/app/(protected)/`, `web/app/login/`, `web/lib/` (services API).

---

## 6. Communication entre Composants

### 6.1 Protocoles

**Mobile → Backend**
- Protocole : HTTP/REST
- Format : JSON
- Authentification : Bearer Token (JWT)
- Port : 8000

**Backend → Raspberry Pi**
- Protocole : HTTP/REST
- Format : JSON
- Authentification : API Key (header X-API-Key)
- Port : 5000

**Raspberry Pi → Backend**
- Protocole : HTTP/REST
- Format : JSON
- Authentification : API Key
- Types : Heartbeat, événements de détection, mesures de luminosité, changements d'état

### 6.2 Flux de Données : Allumage d'une Lampe (Contrôle Manuel)

1. **Utilisateur** clique sur le bouton ON dans l'application mobile
2. **ViewModel** met à jour l'état local optimiste et appelle le Repository
3. **Repository** envoie une requête POST au backend via Retrofit
4. **Backend** valide le JWT et les paramètres (device_id, brightness)
5. **Backend** envoie une requête HTTP POST au Raspberry Pi avec l'API Key
6. **Raspberry Pi** valide la clé API et configure le signal PWM sur le GPIO
7. **Lampe physique** s'allume à l'intensité demandée
8. **Raspberry Pi** retourne une confirmation avec l'état réel
9. **Backend** enregistre l'événement dans la table events (source: 'manual')
10. **Backend** retourne le nouvel état à l'application mobile
11. **UI mobile** se met à jour pour refléter le changement

**Temps total estimé :** < 2 secondes

### 6.3 Flux de Données : Détection de Présence avec Règle

1. **Module Bluetooth** scanne périodiquement les devices à proximité (toutes les 30s)
2. **BluetoothSensor** détecte un nouveau device (adresse MAC + RSSI)
3. **Filtrage anti-rebond** vérifie qu'aucune détection récente pour cette MAC (< 5s)
4. **BackendClient** envoie immédiatement un POST au backend avec MAC et RSSI
5. **Backend** tente de mapper la MAC à un utilisateur via la table `bluetooth_devices`
6. **Backend** enregistre la détection dans la table `presence` (avec MAC, RSSI, user_id si mappé)
7. **RuleEngine** est déclenché et évalue toutes les règles actives
8. Si une règle est satisfaite, **DeviceService** exécute l'action définie
9. **Backend** envoie la commande au Raspberry Pi concerné
10. **Appareil** change d'état selon l'action (ex: allumage lampe à 70%)
11. **Backend** enregistre l'événement avec source 'automatic'

**Temps total estimé :** < 3 secondes

### 6.4 Flux de Données : Smart Dimming (Adaptation Dynamique)

**Cas : Luminosité naturelle augmente, système réduit intensité artificielle**

1. **Capteur BH1750** mesure la luminosité ambiante (I²C)
2. **LightMonitor service** lit la valeur toutes les 10 secondes
3. **LightMonitor** envoie POST /api/light_readings au backend avec valeur en lux
4. **Backend** enregistre la mesure dans light_readings
5. **SmartDimmingService** est déclenché (hook post-insertion)
6. **SmartDimmingService** récupère :
   - Luminosité actuelle (ex: 600 lux)
   - Scénario actif via AIService (ex: "Day")
   - Liste des lampes allumées dans la pièce
7. **Algorithme de calcul** détermine intensité cible selon le scénario :
   - Mode Day, 600 lux → intensité cible = 25% (luminosité élevée)
8. **SmartDimmingService** compare avec intensité actuelle (ex: 70%)
9. Écart significatif (45%) → commande d'ajustement nécessaire
10. **Backend** envoie POST /api/devices/{id}/brightness au Raspberry Pi
11. **Raspberry Pi** applique le PWM progressivement (fade immédiat en mode Day)
12. **Backend** enregistre l'ajustement dans dimming_adjustments avec :
    - previous_brightness: 70
    - target_brightness: 25
    - reason: "High natural light detected (600 lux)"
    - source: 'smart_dimming'
13. **Backend** enregistre également l'événement dans events
14. **Application mobile** reçoit la notification de changement (via polling ou WebSocket)
15. **UI** met à jour l'affichage avec la nouvelle intensité et le motif

**Temps total estimé :** < 3 secondes

**Protection contre oscillations :**
Si l'utilisateur ajuste manuellement la lampe dans les 2 minutes suivant un smart dimming, le système :
- Enregistre la préférence dans user_preferences
- Désactive temporairement le smart dimming pour cette lampe (30 minutes)
- Affiche une notification "Smart dimming pausé selon votre préférence"

### 6.5 API Endpoints Principaux

**Authentification :**
- POST /api/auth/login → JWT token
- POST /api/auth/register → Création utilisateur

**Appareils :**
- GET /api/devices → Liste des appareils
- GET /api/devices/{id} → Détails d'un appareil
- PUT /api/devices/{id}/state → Changer état (ON/OFF)
- PUT /api/devices/{id}/brightness → Changer intensité

**Règles :**
- GET /api/rules → Liste des règles
- POST /api/rules → Créer une règle
- PUT /api/rules/{id} → Modifier une règle
- DELETE /api/rules/{id} → Supprimer une règle

**IA et Scénarios :**
- GET /api/ai/current_scenario → Scénario actif actuel
- POST /api/ai/classify → Classification manuelle

**Smart Dimming :**
- GET /api/smart_dimming/status → État global du système
- GET /api/smart_dimming/adjustments → Historique des ajustements
- PUT /api/smart_dimming/enable → Activer/désactiver globalement
- PUT /api/smart_dimming/pause/{device_id} → Pause temporaire pour un appareil

**Capteurs :**
- POST /api/light_readings → Enregistrer mesure luminosité (utilisé par RPi)
- GET /api/light_readings → Historique des mesures

**Événements :**
- GET /api/events → Historique des événements
- GET /api/events/device/{id} → Événements d'un appareil

---

## 7. Sécurité

### 7.1 Authentification

**JWT (JSON Web Tokens) pour l'application mobile :**
- Algorithme : HS256 (HMAC SHA-256)
- Payload : user_id, username, exp (expiration), iat (émission)
- Durée de validité : 24 heures
- Stockage mobile : DataStore Preferences (Android)
- Refresh token : Non implémenté (simplification pour projet académique)

**Cycle de vie JWT :**
1. Utilisateur fournit username/password via écran de connexion
2. Backend vérifie le hash bcrypt stocké en base
3. Token JWT généré avec payload et signature HMAC
4. Token retourné à l'application mobile
5. Token stocké dans DataStore de manière sécurisée
6. Token envoyé dans header Authorization: Bearer {token} pour chaque requête
7. Backend valide signature et expiration à chaque requête protégée

**API Key pour Raspberry Pi :**
- Longueur : 64 caractères hexadécimaux
- Génération : cryptographiquement sécurisée (secrets.token_hex)
- Unique par Raspberry Pi
- Header : X-API-Key
- Stockage : table raspberry_pis
- Rotation : Manuelle via interface admin

**Validation API Key :**
Le backend vérifie la présence et la validité de la clé API pour toutes les requêtes provenant des Raspberry Pi. Si invalide, retour HTTP 401 Unauthorized.

### 7.2 Hachage des Mots de Passe

- Algorithme : bcrypt
- Cost factor : 12 rounds minimum (compromis sécurité/performance)
- Salt : généré automatiquement par bcrypt
- Stockage : hash uniquement, jamais en clair
- Librairie : passlib avec CryptContext

### 7.3 Validation des Entrées

**Validation côté serveur (Pydantic) :**
Tous les endpoints utilisent des schémas Pydantic pour valider :
- Type de données strict (int, str, bool, float)
- Plage de valeurs (ex: brightness entre 0 et 100)
- Format (ex: regex pour email, pattern pour GPIO pin)
- Cohérence métier (ex: gpio_pin unique par raspberry_pi)

**Protection contre injections SQL :**
- Utilisation exclusive de requêtes préparées via SQLAlchemy ORM
- Paramètres bindés automatiquement
- Pas de concaténation de chaînes SQL

**Protection XSS :**
- Échappement automatique dans les réponses JSON
- Validation stricte des champs JSONB (règles)

**Rate Limiting :**
Non implémenté dans la version académique, mais recommandé pour production :
- Limiter à 100 requêtes/minute par IP pour les endpoints publics
- Limiter à 10 tentatives de connexion/minute

### 7.4 HTTPS / TLS

**Environnement de développement :**
- HTTP non chiffré (acceptable pour réseau local IUT)

**Recommandation production :**
- Utiliser HTTPS avec certificat Let's Encrypt
- Redirection automatique HTTP → HTTPS
- Configuration Uvicorn avec SSL context

### 7.5 Sécurité Raspberry Pi

**Accès SSH :**
- Désactiver authentification par mot de passe
- Utiliser uniquement clés SSH
- Changer port par défaut (22 → port personnalisé)

**Firewall :**
- Autoriser uniquement port 5000 (Flask API)
- Bloquer tout autre trafic entrant

**Mise à jour :**
- Automatiser les mises à jour de sécurité du système

---

## 8. Déploiement

### 8.1 Environnement de Déploiement

**Option retenue : Serveur IUT + Raspberry Pi local**

**Avantages :**
- Infrastructure fournie et maintenue
- Pas de coûts d'hébergement
- Accès au serveur Ollama IUT (si besoin IA avancée future)
- Réseau local rapide

**Prérequis serveur :**
- Python 3.9+
- PostgreSQL 14+
- Accès SSH
- Droits d'installation de packages

**Prérequis Raspberry Pi :**
- Raspberry Pi OS Lite (dernière version)
- Connexion réseau stable (Ethernet recommandé pour fiabilité)
- Carte SD de qualité classe 10 minimum (32 Go recommandé)
- Alimentation 5V 3A officielle

### 8.2 Installation Backend

**Étapes détaillées :**

**1. Clonage du repository**
```bash
git clone https://github.com/votre-equipe/smarthome-backend.git
cd smarthome-backend
```

**2. Création environnement virtuel**
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Installation dépendances**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Configuration variables d'environnement**
Créer un fichier .env à la racine avec :
```
DATABASE_URL=postgresql://user:password@localhost:5432/smarthome
SECRET_KEY=your_secret_key_here_minimum_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

**5. Initialisation base de données**
```bash
# Créer la base PostgreSQL
createdb smarthome

# Activer TimescaleDB (optionnel, pour time-series)
psql -d smarthome -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Exécuter le script d'initialisation
psql -d smarthome -f db/init_database.sql
```

**6. Génération données d'entraînement IA**
```bash
# Générer 1000 échantillons de données synthétiques
python ml/generate_data.py --samples 1000

# Entraîner le modèle Decision Tree
python ml/train_model.py --max-depth 7

# Vérifier que le modèle a été créé
ls -lh ml/models/scenario_classifier.pkl
```

**7. Lancement du serveur**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**8. Vérification**
Accéder à http://localhost:8000/docs pour la documentation Swagger de l'API.

**9. Service systemd (optionnel, pour production)**
Créer /etc/systemd/system/smarthome-backend.service pour démarrage automatique.

### 8.3 Installation Raspberry Pi

**Étapes détaillées :**

**1. Configuration système de base**
```bash
# Mise à jour complète
sudo apt update && sudo apt upgrade -y

# Installation Python et outils
sudo apt install python3-pip python3-venv git i2c-tools -y

# Activer I2C pour BH1750
sudo raspi-config
# Sélectionner Interfacing Options → I2C → Enable
```

**2. Clonage et installation**
```bash
git clone https://github.com/votre-equipe/smarthome-rpi.git
cd smarthome-rpi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Configuration**
Éditer config.py avec :
- URL du serveur backend (ex: http://serveur-iut:8000)
- API Key unique (récupérée depuis l'interface admin backend)
- Numéros de pins GPIO selon câblage physique
- Type de capteur de luminosité (BH1750 ou LDR)

**4. Vérification capteur I2C**
```bash
i2cdetect -y 1
# Doit afficher l'adresse 0x23 si BH1750 connecté
```

**5. Vérification de connexion au backend**
```bash
python main.py --test-connection
# Doit afficher "Connection successful" + informations du serveur
```

**6. Lancement du service**
```bash
python main.py
# Vérifier les logs :
# - Initialisation capteurs
# - Connexion backend réussie
# - Heartbeat toutes les 60 secondes
```

**7. Service systemd**
Créer /etc/systemd/system/smarthome-rpi.service pour démarrage automatique au boot.

### 8.4 Application Web (Next.js)

**Développement :**
```bash
cd web
npm install
npm run dev
```
Accès : http://localhost:3000

**Build de production :**
```bash
cd web
npm run build
npm run start
```

**Configuration :** Définir l’URL de l’API backend (variable d’environnement ou fichier de config) pour que le frontend appelle le bon serveur.

### 8.5 Déploiement Application Mobile

**Build de l'APK :**

**1. Configuration**
Éditer app/src/main/res/values/config.xml avec :
- URL du serveur backend (ex: http://serveur-iut:8000)
- Timeout réseau
- Fréquence de rafraîchissement

**2. Génération APK de release**
```bash
./gradlew assembleRelease
```

**3. Signature APK (optionnel, pour distribution)**
Utiliser Android Studio ou jarsigner pour signer l'APK avec un keystore.

**4. Fichier généré**
- Emplacement : app/build/outputs/apk/release/app-release.apk
- Taille attendue : 15-20 Mo

**Installation sur appareil Android :**

1. Transférer l'APK sur le téléphone (USB, email, cloud)
2. Activer "Sources inconnues" dans Paramètres → Sécurité
3. Ouvrir l'APK et installer
4. Lancer l'application
5. Écran de connexion : entrer username/password
6. Vérifier la connexion au serveur (indicateur réseau)

**Dépannage :**
- Si erreur de connexion : vérifier URL backend dans config.xml
- Si lenteur : vérifier que le serveur est accessible depuis le réseau mobile
- Si crash : consulter les logs via Android Studio (adb logcat)

### 8.6 Scripts de Déploiement Automatisé

**Création de scripts bash pour automatiser :**

**deploy_backend.sh :**
- Clone repo
- Installe dépendances
- Configure .env
- Lance migrations
- Entraîne modèle IA
- Démarre serveur

**deploy_rpi.sh :**
- Clone repo
- Installe dépendances
- Configure GPIO
- Teste capteurs
- Lance service

**Ces scripts réduisent les erreurs humaines et accélèrent le déploiement.**

---

## 9. Livrables

### 9.1 Code Source

**Repository Git incluant :**
- Code backend (FastAPI) avec tous les services
- Code Raspberry Pi (Flask + Z-Wave ou GPIO/capteurs)
- Code application web (Next.js)
- Code application mobile (Kotlin + Compose)
- Scripts de migration base de données (Alembic)
- Scripts d'entraînement IA (génération + training)
- Fichiers de configuration d'exemple (.env.example, config.example.py)
- README.md détaillé avec instructions d'installation
- .gitignore complet (exclusion .env, venv, .pkl)

**Organisation branches Git :**
- main : version stable
- develop : développement en cours
- feature/* : fonctionnalités spécifiques
- hotfix/* : corrections urgentes

### 9.2 Documentation

**Documentation technique (ce document) :**
- Architecture système complète
- Schéma base de données avec relations
- Description détaillée des fonctionnalités
- Guide d'installation pas à pas
- Stack technique justifié
- Diagrammes de flux

**Documentation API :**
- Swagger/OpenAPI auto-générée par FastAPI
- Accessible à /docs sur le serveur
- Liste complète des endpoints avec paramètres
- Exemples de requêtes/réponses
- Codes d'erreur détaillés

**Guide utilisateur :**
- Manuel d'utilisation de l'application mobile
- Captures d'écran annotées de chaque écran
- Tutoriel pas à pas pour créer une règle
- Tutoriel configuration smart dimming
- FAQ des problèmes courants

**Schémas et diagrammes :**
- Architecture globale (présenté dans ce document)
- Diagramme de séquence pour chaque flux majeur
- Schéma de câblage Raspberry Pi (Fritzing)
- Diagramme entité-relation de la base de données

### 9.3 Application Mobile

**Package APK :**
- Fichier app-release.apk signé
- Fichier d'information (version, date, taille, checksums)
- Instructions d'installation détaillées

**Captures d'écran :**
- Tableau de bord principal
- Écran de contrôle des appareils
- Écran de création de règles
- Écran smart dimming
- Écran historique

### 9.4 Vidéo de Démonstration

**Durée : 2-3 minutes**

**Structure détaillée :**

1. **Introduction (15 secondes)**
   - Présentation du projet SmartHome Lite
   - Présentation rapide de l'équipe
   - Contexte SAE BUT3 FA 2025

2. **Architecture (30 secondes)**
   - Schéma animé du système (3 couches)
   - Highlight du Raspberry Pi avec capteurs
   - Highlight du backend avec IA
   - Highlight de l'application mobile

3. **Démonstration fonctionnelle (90 secondes)**

   **Partie 1 : Contrôle manuel (20s)**
   - Vue du tableau de bord avec appareils
   - Allumage d'une lampe via toggle
   - Ajustement d'intensité via slider
   - Confirmation visuelle sur lampe physique

   **Partie 2 : Détection et automatisation (30s)**
   - Détection de présence via scan Bluetooth
   - Identification de l'utilisateur via adresse MAC
   - Déclenchement automatique d'une règle
   - Lampe s'allume automatiquement
   - Affichage événement dans historique

   **Partie 3 : Smart dimming (40s)**
   - Écran smart dimming avec jauge luminosité
   - Simulation augmentation lumière naturelle (lampe vers fenêtre)
   - Système réduit automatiquement intensité lampe
   - Graphique montrant corrélation luminosité/intensité
   - Affichage du scénario IA actif ("Day")
   - Justification textuelle de l'ajustement

4. **Technologies et métriques (20 secondes)**
   - Stack technique résumé
   - Métriques clés :
     - Temps de réponse < 2s
     - Accuracy IA > 70%
     - Smart dimming : économie d'énergie estimée
   - Logos des technologies (Python, Kotlin, PostgreSQL, scikit-learn)

5. **Conclusion (15 secondes)**
   - Bilan des fonctionnalités réalisées
   - Conformité aux contraintes SAE
   - Perspectives d'amélioration (apprentissage personnalisé)
   - Remerciements

**Qualité technique :**
- Résolution : 1080p minimum
- Audio clair avec voix-off professionnelle
- Sous-titres français pour accessibilité
- Montage fluide avec transitions simples
- Musique de fond discrète

**Outils recommandés :**
- OBS Studio pour capture d'écran
- DaVinci Resolve pour montage
- Audacity pour voix-off

### 9.5 Présentation Orale

**Support PowerPoint/PDF (15-20 slides) :**

1. Page de titre
2. Contexte et problématique
3. Architecture globale
4. Matériel utilisé (Raspberry Pi + capteurs)
5. Fonctionnalités principales
6. Smart dimming (cœur de l'innovation)
7. Intelligence artificielle (classification)
8. Base de données et modélisation
9. Stack technique
10. Démo vidéo
## Table des Matières

- [1. Contexte et Objectifs](#1-contexte-et-objectifs)
  - [1.1 Contexte du Projet](#11-contexte-du-projet)
  - [1.2 Contraintes du Projet](#12-contraintes-du-projet)
  - [1.3 Objectifs Prioritaires](#13-objectifs-prioritaires)
- [2. Architecture Globale](#2-architecture-globale)
  - [2.1 Vue d'Ensemble](#21-vue-densemble)
  - [2.2 Architecture Modulaire](#22-architecture-modulaire)
  - [2.3 Composants Principaux](#23-composants-principaux)
  - [2.4 Base de Données avec TimescaleDB](#24-base-de-données-avec-timescaledb)
  - [2.5 Configuration Matérielle Raspberry Pi](#25-configuration-matérielle-raspberry-pi)
- [3. Fonctionnalités Principales](#3-fonctionnalités-principales)
  - [3.1 Vision d'Ensemble du Système](#31-vision-densemble-du-système)
  - [3.2 Contrôle Manuel des Appareils](#32-contrôle-manuel-des-appareils)
    - [F1 : Gestion des Lampes](#f1--gestion-des-lampes)
    - [F2 : Gestion des Prises](#f2--gestion-des-prises)
    - [F3 : Tableau de Bord Centralisé](#f3--tableau-de-bord-centralisé)
  - [3.3 Détection de Présence](#33-détection-de-présence)
    - [F4 : Système de Détection](#f4--système-de-détection)
    - [F5 : Historique de Présence](#f5--historique-de-présence)
  - [3.4 Automatisation Intelligente](#34-automatisation-intelligente)
    - [F6 : Moteur de Règles IF-THEN](#f6--moteur-de-règles-if-then)
    - [F7 : Scénarios Prédéfinis](#f7--scénarios-prédéfinis)
  - [3.5 Intelligence Artificielle et Adaptation Contextuelle](#35-intelligence-artificielle-et-adaptation-contextuelle)
    - [F8 : Intelligence Artificielle Multi-Modèles](#f8--intelligence-artificielle-multi-modèles)
      - [F8.1 : Classification de Scénarios (Améliorée)](#f81--classification-de-scénarios-améliorée)
      - [F8.2 : Régression pour Prédiction d'Intensité (Nouveau)](#f82--régression-pour-prédiction-dintensité-nouveau)
      - [F8.3 : Clustering des Habitudes Utilisateur (Nouveau)](#f83--clustering-des-habitudes-utilisateur-nouveau)
      - [F8.4 : Pipeline d'Inférence](#f84--pipeline-dinférence)
    - [F9 : Adaptation Dynamique à la Luminosité (Smart Dimming)](#f9-adaptation-dynamique-à-la-luminosité-smart-dimming)
  - [3.6 Visualisation](#36-visualisation)
    - [F10 : Graphique de Présence](#f10--graphique-de-présence)
    - [F11 : Graphique de Luminosité](#f11--graphique-de-luminosité)
- [4. Base de Données](#4-base-de-données)
  - [4.1 Choix Technologique](#41-choix-technologique)
  - [4.2 Schéma de Données Complet](#42-schéma-de-données-complet)
  - [4.3 Relations entre Tables](#43-relations-entre-tables)
  - [4.4 Volumétrie Estimée](#44-volumétrie-estimée)
- [5. Technologies et Stack Technique](#5-technologies-et-stack-technique)
  - [5.1 Backend (Serveur)](#51-backend-serveur)
  - [5.2 Raspberry Pi (Contrôleur)](#52-raspberry-pi-contrôleur)
  - [5.3 Application Mobile (Android)](#53-application-mobile-android)
  - [5.4 Application Web (Next.js)](#54-application-web-nextjs)
- [6. Communication entre Composants](#6-communication-entre-composants)
  - [6.1 Protocoles](#61-protocoles)
  - [6.2 Flux de Données : Allumage d'une Lampe (Contrôle Manuel)](#62-flux-de-données--allumage-dune-lampe-contrôle-manuel)
  - [6.3 Flux de Données : Détection de Présence avec Règle](#63-flux-de-données--détection-de-présence-avec-règle)
  - [6.4 Flux de Données : Smart Dimming (Adaptation Dynamique)](#64-flux-de-données--smart-dimming-adaptation-dynamique)
  - [6.5 API Endpoints Principaux](#65-api-endpoints-principaux)
- [7. Sécurité](#7-sécurité)
  - [7.1 Authentification](#71-authentification)
  - [7.2 Hachage des Mots de Passe](#72-hachage-des-mots-de-passe)
  - [7.3 Validation des Entrées](#73-validation-des-entrées)
  - [7.4 HTTPS / TLS](#74-https--tls)
  - [7.5 Sécurité Raspberry Pi](#75-sécurité-raspberry-pi)
- [8. Déploiement](#8-déploiement)
  - [8.1 Environnement de Déploiement](#81-environnement-de-déploiement)
  - [8.2 Installation Backend](#82-installation-backend)
  - [8.3 Installation Raspberry Pi](#83-installation-raspberry-pi)
  - [8.4 Application Web (Next.js)](#84-application-web-nextjs)
  - [8.5 Déploiement Application Mobile](#85-déploiement-application-mobile)
  - [8.6 Scripts de Déploiement Automatisé](#86-scripts-de-déploiement-automatisé)
- [9. Livrables](#9-livrables)
  - [9.1 Code Source](#91-code-source)
  - [9.2 Documentation](#92-documentation)
  - [9.3 Application Mobile](#93-application-mobile)
  - [9.4 Vidéo de Démonstration](#94-vidéo-de-démonstration)
  - [9.5 Présentation Orale](#95-présentation-orale)

---

## 1. Contexte et Objectifs

### 1.1 Contexte du Projet

**Cadre académique :** Projet de développement distribué et embarqué - SAE BUT3 FA 2025

**Problématique :** Développement d'un système de gestion intelligente d'éclairage et d'appareils électriques pour l'habitat, avec détection de présence, adaptation à la luminosité ambiante et automatisation basée sur l'intelligence artificielle.

### 1.2 Contraintes du Projet

- **Durée :** 50 heures
- **Équipe :** 4 étudiants
- **Matériel disponible :** 
  - Un Raspberry Pi par étudiant
  - Actionneurs : ampoules dimmables, prises connectées
  - Capteurs PIR pour détection de présence
  - Capteurs de luminosité (LDR ou BH1750)

### 1.3 Objectifs Prioritaires

1. Développement d'un **service distribué** déployé sur serveur
2. Intégration d'au moins un **Raspberry Pi** dans l'architecture
3. Hébergement d'une **base de données** sur le système
4. Développement d'une **application mobile** (Kotlin + Jetpack Compose)
5. Intégration d'un **algorithme d'IA** pour classification de scénarios et adaptation contextuelle
6. Contrôle à distance des appareils électriques
7. Détection automatique de présence
8. **Adaptation dynamique à la luminosité ambiante** (smart dimming)
9. Automatisation intelligente par règles

---

## 2. Architecture Globale

### 2.1 Vue d'Ensemble

Le système SmartHome Lite est organisé en **architecture modulaire monolithique** avec séparation claire des responsabilités. Cette architecture permet un développement efficace tout en maintenant une structure claire et maintenable.

**Principes architecturaux :**
- **Modularité** : Séparation des responsabilités en modules indépendants
- **Services** : Logique métier isolée et testable
- **ORM** : SQLAlchemy pour l'accès aux données
- **Validation** : Pydantic pour la validation des données
- **IA multi-modèles** : Classification, régression et clustering
- **Temps réel** : WebSockets pour synchronisation instantanée (optionnel)

### 2.2 Architecture Modulaire

```
┌──────────────────────────────────────────────────────────────────┐
│     APPLICATION MOBILE (Kotlin + Compose)   │  APPLICATION WEB   │
│  • HTTP/REST Client, Optimistic UI         │  (Next.js + React)  │
│                                            │  • Dashboard, Admin │
└──────────────────────┬─────────────────────┴──────────┬───────────┘
                       │                                │
                       │ HTTP/REST, JWT                 │ HTTP/REST, JWT
                       └────────────────┬───────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                         │
│              Architecture Modulaire Monolithique                 │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Routes     │  │   Services   │  │   Models     │            │
│  │              │  │              │  │              │            │
│  │ • auth       │  │ • ai_service │  │ • User       │            │
│  │ • devices    │  │ • device_    │  │ • Device     │            │
│  │ • rules      │  │   service    │  │ • Rule       │            │
│  │ • ai         │  │ • rule_      │  │ • Presence   │            │
│  │ • presence   │  │   engine     │  │ • LightRead  │            │
│  │ • smart_     │  │ • smart_     │  │              │            │
│  │   dimming    │  │   dimming    │  │              │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                              │ 
│  │   Schemas    │  │    Utils     │                              │
│  │  (Pydantic)  │  │              │                              │
│  │              │  │ • auth (JWT) │                              │
│  │ • Validation │  │ • validators │                              │
│  └──────────────┘  └──────────────┘                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Machine Learning (ML)                         │  │
│  │  • generate_data.py                                        │  │
│  │  • train_model.py                                          │  │
│  │  • models/scenario_classifier.pkl                          │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            │ SQLAlchemy ORM
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DATABASE                                      │
│              (PostgreSQL + TimescaleDB)                          │
│  • Tables relationnelles (users, devices, rules)                 │
│  • Hypertables pour time-series (light_readings)                 │
│  • Partitioning automatique                                      │
└──────────────────────────────────────────────────────────────────┘
                       ▲
                       │
                       │ HTTP/REST + API Key
                       │
┌──────────────────────────────────────────────────────────────────┐
│              RASPBERRY PI (Multiples)                            │
│  • Flask API locale                                              │
│  • Capteurs (PIR, luminosité)                                    │
│  • Actionneurs (LED, relais)                                     │
│  • Envoie événements au backend                                  │
│  • Reçoit commandes du backend                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 Composants Principaux

Le backend est organisé en modules fonctionnels clairement séparés :

#### Module Authentification
- Gestion des utilisateurs (CRUD)
- Authentification JWT
- Hachage des mots de passe (bcrypt)

#### Module Gestion des Appareils
- CRUD appareils
- Contrôle des états (ON/OFF, brightness)
- Communication avec Raspberry Pi
- Gestion des mesures de luminosité
- Gestion de la présence

#### Module Intelligence Artificielle
- Classification de scénarios (Decision Tree)
- Régression pour prédiction d'intensité (Random Forest)
- Clustering des habitudes (K-Means) - À implémenter
- Gestion des modèles ML

#### Module Règles d'Automatisation
- CRUD règles
- Moteur IF-THEN pour évaluation des règles
- Déclenchement automatique d'actions

#### Module Smart Dimming
- Ajustement intelligent de l'éclairage
- Adaptation à la luminosité ambiante
- Historique des ajustements

### 2.4 Base de Données avec TimescaleDB

**PostgreSQL standard :**
- Tables relationnelles (users, devices, rules, etc.)
- Relations et contraintes d'intégrité
- Index optimisés

**TimescaleDB (extension) :**
- Hypertables pour données time-series (sensor_readings)
- Partitioning automatique par temps
- Agrégations optimisées (moyennes horaires, etc.)
- Rétention automatique des données anciennes

**Optimisations :**
- Index composites sur (raspberry_pi_id, time DESC)
- Vues matérialisées pour statistiques
- Partitioning des tables d'historique (par mois)

### 2.5 Configuration Matérielle Raspberry Pi

#### Capteur PIR HC-SR501
- **Fonction :** Détection de mouvement infrarouge
- **Portée :** 3 à 7 mètres
- **Angle :** 120 degrés
- **Branchement :**
  - Alimentation : 5V (Pin 2)
  - Masse : GND (Pin 6)
  - Signal : GPIO 4 (Pin 7)

#### Capteur de Luminosité BH1750 (I²C)
- **Fonction :** Mesure de l'intensité lumineuse ambiante
- **Plage :** 1 à 65535 lux
- **Précision :** ±20 lux
- **Interface :** I²C
- **Branchement :**
  - Alimentation : 3.3V (Pin 1)
  - Masse : GND (Pin 9)
  - SDA : GPIO 2 (Pin 3)
  - SCL : GPIO 3 (Pin 5)

#### Alternative : Capteur LDR (Photorésistance)
- **Fonction :** Mesure de la luminosité par variation de résistance
- **Composants associés :** Convertisseur ADC (MCP3008)
- **Interface :** SPI
- **Plage relative :** 0-100% (conversion analogique-numérique)

#### Ampoule LED Dimmable
- **Contrôle :** PWM (Modulation de largeur d'impulsion)
- **Intensité :** Variable 0-100%
- **Fréquence PWM :** 1000 Hz
- **GPIO utilisé :** GPIO 18 (Pin 12)
- **Composants :** Transistor NPN (BC547), résistance 220 ohms

#### Prise Connectée
- **Contrôle :** Module relais 5V
- **Type :** ON/OFF binaire
- **Charge max :** 250V AC / 10A
- **GPIO utilisé :** GPIO 23 (Pin 16)

---

## 3. Fonctionnalités Principales

### 3.1 Vision d'Ensemble du Système

**Le système SmartHome Lite opère sur trois niveaux d'intelligence :**

1. **Contrôle manuel :** L'utilisateur pilote directement les appareils via l'application mobile (allumer, éteindre, régler l'intensité).

2. **Automatisations déterministes :** Des règles IF-THEN prédéfinies déclenchent automatiquement des actions selon des conditions fixes (présence, heure, jour, luminosité).

3. **Adaptation contextuelle intelligente :** Un module d'IA classifie le contexte d'utilisation (jour, nuit, soirée, absence) et un système de **smart dimming** ajuste dynamiquement l'intensité lumineuse en fonction de la luminosité naturelle mesurée en temps réel.

**Cette architecture progressive permet au système de passer d'un simple automate à un assistant domotique véritablement adaptatif.**

**Note importante :** L'IA de classification ne "décide" pas de manière autonome : elle reconnaît un contexte parmi quatre scénarios prédéfinis et applique les comportements statiques associés. Le véritable caractère "intelligent" du système réside dans le **smart dimming**, qui adapte dynamiquement l'intensité lumineuse en combinant mesures physiques, règles et préférences apprises.

### 3.2 Contrôle Manuel des Appareils

#### F1 : Gestion des Lampes
**Fonctionnalités :**
- Allumage et extinction individuels
- Ajustement de l'intensité lumineuse (slider 0-100%)
- Affichage en temps réel de l'état
- Temps de réponse garanti < 2 secondes

**Interface mobile :**
- Carte par lampe avec icône et nom
- Toggle switch ON/OFF
- Slider d'intensité (si lampe dimmable)
- Indicateur visuel de l'intensité actuelle

#### F2 : Gestion des Prises
**Fonctionnalités :**
- Activation et désactivation ON/OFF
- Affichage de l'état actuel (actif/inactif)
- Confirmation visuelle immédiate

**Interface mobile :**
- Carte par prise avec icône et nom
- Toggle switch ON/OFF
- Indicateur d'état coloré

#### F3 : Tableau de Bord Centralisé
**Fonctionnalités :**
- Vue d'ensemble de tous les appareils connectés
- Indicateurs visuels d'état (actif/inactif/erreur)
- Rafraîchissement automatique périodique (toutes les 5 secondes)
- Organisation par pièce
- Affichage du scénario actif (jour, nuit, soirée, absence)
- Indicateur de luminosité ambiante en temps réel
- Statut du mode smart dimming (actif/inactif)

### 3.3 Détection de Présence

#### F4 : Système de Détection
**Fonctionnalités :**
- Détection en temps réel par capteur PIR
- Enregistrement horodaté des événements
- Filtrage anti-rebond (ignorer détections < 5 secondes)
- Association avec la localisation (pièce)

**Implémentation technique :**
Le capteur PIR détecte les variations de rayonnement infrarouge. Un système anti-rebond empêche les détections multiples rapprochées. Chaque détection validée génère un événement envoyé immédiatement au serveur backend.

#### F5 : Historique de Présence
**Fonctionnalités :**
- Liste chronologique des dernières détections
- Filtrage par date et localisation
- Statistiques de base par appareil
- Graphique des détections sur 24 heures

### 3.4 Automatisation Intelligente

#### F6 : Moteur de Règles IF-THEN

Le moteur de règles permet de définir des automatisations déterministes simples mais puissantes.

**Conditions disponibles :**
- Détection de présence (booléen + localisation)
- Plage horaire (format 24h)
- Jour de la semaine (lundi à dimanche)
- État d'un appareil spécifique
- **Niveau de luminosité ambiante** (seuil en lux ou pourcentage)

**Actions disponibles :**
- Allumer ou éteindre un appareil
- Définir une intensité lumineuse spécifique
- Activer un scénario prédéfini
- **Activer/désactiver le mode smart dimming**

**Exemples de règles :**

1. **Règle présence soirée :**
   - **Condition :** Présence détectée dans le salon ET heure entre 18h et 23h
   - **Action :** Allumer lampe salon à 70%

2. **Règle économie d'énergie :**
   - **Condition :** Aucune présence pendant 10 minutes
   - **Action :** Éteindre toutes les lampes

3. **Règle luminosité naturelle élevée :**
   - **Condition :** Luminosité ambiante > 500 lux ET heure entre 9h et 17h
   - **Action :** Réduire intensité lampe bureau à 20%

4. **Règle crépuscule :**
   - **Condition :** Luminosité < 100 lux ET présence détectée
   - **Action :** Activer smart dimming à 80%

**Format JSON des règles :**
Les règles sont stockées en base de données au format JSONB, permettant une flexibilité maximale dans la définition des conditions et actions.

#### F7 : Scénarios Prédéfinis

Les scénarios définissent des comportements globaux adaptés au contexte. **L'IA identifie automatiquement le scénario actuel**, et le système applique les paramètres correspondants.

**Mode Jour (6h - 18h)**
- Désactivation automatique des lampes si absence détectée
- Intensité maximale (100%) si allumage manuel
- Smart dimming actif : réduction si luminosité naturelle élevée
- Seuil de luminosité basse : 300 lux
- Priorité à l'économie d'énergie

**Mode Soirée (18h - 23h)**
- Intensité modérée (60-80%) pour le confort visuel
- Activation automatique sur détection de présence
- Smart dimming actif avec adaptation progressive
- Seuil de luminosité basse : 150 lux
- Transition douce entre intensités (fade de 2 secondes)

**Mode Nuit (23h - 6h)**
- Intensité minimale (20-30%) pour les déplacements nocturnes
- Réduction du temps d'activation automatique (délai réduit à 1 minute)
- Smart dimming désactivé (priorité confort nocturne)
- Extinction automatique après 2 minutes sans détection

**Mode Absence**
- Extinction de tous les appareils non essentiels
- Enregistrement des détections sans action automatique
- Smart dimming désactivé
- Possibilité de simulation de présence (allumages aléatoires)

### 3.5 Intelligence Artificielle et Adaptation Contextuelle

#### F8 : Intelligence Artificielle Multi-Modèles

**Objectif :**
Le système utilise **trois modèles d'IA complémentaires** pour offrir une intelligence adaptative avancée : classification de contexte, prédiction d'intensité optimale, et détection automatique de profils utilisateur.

**Architecture IA :**
- **Classification** : Reconnaissance du scénario contextuel (Decision Tree amélioré)
- **Régression** : Prédiction de l'intensité lumineuse optimale (Random Forest)
- **Clustering** : Détection automatique des habitudes utilisateur (K-Means)

##### F8.1 : Classification de Scénarios (Améliorée)

**Algorithme :** Decision Tree Classifier (scikit-learn) avec features enrichies

**Variables d'entrée (Features améliorées) :**

| Variable | Type | Plage | Description |
|----------|------|-------|-------------|
| hour | Entier | 0-23 | Heure actuelle de la journée |
| day_of_week | Entier | 0-6 | Jour de la semaine (0=Lundi, 6=Dimanche) |
| presence_detected | Booléen | 0/1 | Mouvement détecté dans les 5 dernières minutes |
| light_on | Booléen | 0/1 | Au moins une lampe est allumée actuellement |
| ambient_light_level | Entier | 0-100 | Niveau de luminosité ambiante (pourcentage) |
| temperature | Float | 15-30 | Température ambiante en °C (optionnel) |
| last_motion_time | Entier | 0-1440 | Minutes depuis dernière détection |

**Scénarios (Labels) :**

| Scénario | Valeur | Description |
|----------|--------|-------------|
| Day | 0 | Journée normale, lumière naturelle suffisante |
| Night | 1 | Période nocturne, éclairage minimal nécessaire |
| Away | 2 | Absence prolongée, économie d'énergie prioritaire |
| Evening | 3 | Soirée détente, ambiance lumineuse |

**Objectifs de performance :**
- Accuracy minimale : **75%** (amélioré de 70%)
- Temps d'inférence : < 100 millisecondes
- Rafraîchissement : toutes les 2 minutes
- F1-score par classe : > 0.70

**Méthodologie d'entraînement :**
1. Génération de données synthétiques cohérentes (1000 échantillons minimum)
2. Division train/test/validation : 70/15/15
3. Entraînement avec Decision Tree (max_depth=7, min_samples_split=10)
4. Optimisation hyperparamètres (GridSearchCV)
5. Évaluation avec matrice de confusion et classification report
6. Sauvegarde du modèle au format joblib
7. Rechargement automatique au démarrage du service IA

##### F8.2 : Régression pour Prédiction d'Intensité (Nouveau)

**Algorithme :** Random Forest Regressor (scikit-learn)

**Objectif :**
Prédire l'intensité lumineuse optimale (0-100%) selon le contexte et les préférences historiques de l'utilisateur.

**Variables d'entrée (Features) :**

| Variable | Type | Plage | Description |
|----------|------|-------|-------------|
| ambient_light_lux | Entier | 0-65535 | Luminosité ambiante mesurée (lux) |
| hour | Entier | 0-23 | Heure actuelle |
| day_of_week | Entier | 0-6 | Jour de la semaine |
| user_preference_avg | Float | 0-100 | Intensité moyenne préférée par l'utilisateur (historique) |
| room_type | Catégoriel | salon/chambre/bureau | Type de pièce |
| scenario | Entier | 0-3 | Scénario actif (de la classification) |
| weather_condition | Catégoriel | ensoleillé/nuageux/sombre | Condition météo (API externe optionnel) |

**Variable cible :**
- `target_brightness` : Intensité lumineuse optimale (0-100%)

**Objectifs de performance :**
- R² score : > 0.80
- MAE (Mean Absolute Error) : < 10%
- Temps d'inférence : < 150 millisecondes

**Méthodologie d'entraînement :**
1. Collecte de données historiques (user_preferences, dimming_adjustments)
2. Feature engineering (normalisation, encodage catégoriel)
3. Division train/validation : 80/20
4. Entraînement Random Forest (n_estimators=100, max_depth=15)
5. Validation croisée (5-fold)
6. Évaluation avec métriques de régression
7. Sauvegarde du modèle

**Apprentissage continu :**
- Le modèle peut être réentraîné périodiquement avec de nouvelles données
- Feedback utilisateur : si l'utilisateur ajuste manuellement après une prédiction, c'est enregistré
- Réentraînement automatique tous les 7 jours (optionnel)

##### F8.3 : Clustering des Habitudes Utilisateur (Nouveau)

**Algorithme :** K-Means Clustering (scikit-learn)

**Objectif :**
Détecter automatiquement les profils d'utilisation pour personnaliser le comportement du système.

**Variables d'entrée (Features) :**

| Variable | Type | Description |
|----------|------|-------------|
| avg_hour_on | Float | Heure moyenne d'allumage des lampes |
| avg_hour_off | Float | Heure moyenne d'extinction |
| avg_brightness | Float | Intensité moyenne préférée |
| usage_frequency | Float | Nombre d'utilisations par jour |
| weekend_vs_weekday | Float | Ratio d'utilisation weekend/semaine |
| presence_duration_avg | Float | Durée moyenne de présence détectée |

**Profils détectés (K=4) :**
- **Early Bird** : Lever tôt, coucher tôt, intensité élevée le matin
- **Night Owl** : Lever tard, coucher tard, intensité faible le matin
- **Regular** : Horaires réguliers, intensité modérée
- **Minimal** : Utilisation minimale, intensité faible

**Utilisation :**
- Le système adapte les recommandations selon le profil détecté
- Les règles par défaut peuvent être ajustées selon le profil
- Visualisation dans l'application mobile

**Méthodologie :**
1. Collecte de données d'utilisation sur 2 semaines minimum
2. Normalisation des features
3. Clustering K-Means (K=4, init='k-means++', n_init=10)
4. Évaluation avec silhouette score
5. Attribution du profil à l'utilisateur
6. Mise à jour périodique (tous les 14 jours)

##### F8.4 : Pipeline d'Inférence

**Flux d'exécution :**

```
1. Nouvelle mesure de luminosité reçue
   ↓
2. Classification : Déterminer le scénario actif
   ↓
3. Récupération des préférences utilisateur (historique)
   ↓
4. Régression : Prédire l'intensité optimale
   ↓
5. Clustering : Vérifier le profil utilisateur (si disponible)
   ↓
6. Ajustement final selon profil + scénario
   ↓
7. Application de l'intensité calculée
   ↓
8. Enregistrement pour apprentissage futur
```

**Performance globale :**
- Temps total d'inférence : < 300ms
- Précision globale : > 80% de satisfaction utilisateur
- Apprentissage continu activé

#### F9 : Adaptation Dynamique à la Luminosité (Smart Dimming) - **Véritable Intelligence**

**Objectif :**
Ajuster automatiquement et dynamiquement l'intensité lumineuse des lampes en fonction de la luminosité naturelle mesurée en temps réel, du scénario actif et des préférences utilisateur.

**C'est ici que réside la véritable intelligence adaptative du système.**

**Principe de fonctionnement :**

Le système combine trois sources d'information pour calculer l'intensité optimale :

1. **Mesure physique :** Luminosité ambiante mesurée par le capteur (en lux)
2. **Contexte IA :** Scénario actif détecté par le Decision Tree
3. **Règles métier :** Plages de luminosité et seuils prédéfinis par scénario

**Algorithme d'ajustement :**

L'intensité cible est calculée par interpolation linéaire entre des points de référence :

- Si luminosité naturelle > 70%, réduire l'intensité artificielle à 30%
- Si luminosité < 20%, augmenter à 80% (voire 100% en mode nuit)
- Entre les deux, interpolation progressive

**Paramètres par scénario :**

**Mode Jour :**
- Seuil haut : 500 lux → intensité cible 20%
- Seuil bas : 200 lux → intensité cible 70%
- Interpolation linéaire entre les deux
- Réactivité : ajustement immédiat (< 1 seconde)

**Mode Soirée :**
- Seuil haut : 150 lux → intensité cible 50%
- Seuil bas : 50 lux → intensité cible 80%
- Interpolation douce avec fade progressif (2 secondes)
- Effet graduel à mesure que la luminosité extérieure baisse

**Mode Nuit :**
- Smart dimming désactivé par défaut
- Intensité fixe 30% pour confort nocturne
- Pas de variation automatique (éviter réveil)

**Mode Absence :**
- Smart dimming désactivé
- Lampes éteintes (sauf simulation de présence)

**Exemples concrets :**

**Exemple 1 : Journée ensoleillée**
- Luminosité mesurée : 800 lux
- Scénario IA : Day
- Présence détectée : Oui
- Action : Réduire intensité lampe bureau à 25%
- Justification : Lumière naturelle suffisante

**Exemple 2 : Crépuscule en soirée**
- Luminosité mesurée : 100 lux
- Scénario IA : Evening
- Présence détectée : Oui
- Action : Augmenter progressivement intensité salon de 50% à 75%
- Justification : Compensation de la baisse de lumière naturelle

**Exemple 3 : Ciel couvert en journée**
- Luminosité mesurée : 250 lux
- Scénario IA : Day
- Présence détectée : Oui
- Action : Ajuster intensité à 55% (interpolation)
- Justification : Complément de lumière nécessaire

**Avantages du smart dimming :**
- **Confort visuel :** Luminosité constante perçue par l'utilisateur
- **Économie d'énergie :** Réduction automatique quand la lumière naturelle est suffisante
- **Adaptation contextuelle :** Comportement différent selon le moment de la journée
- **Progressivité :** Transitions douces sans changements brusques

**Intégration temps réel :**

Le capteur de luminosité envoie des mesures toutes les 10 secondes au serveur backend. Le service smart dimming :

1. Récupère la luminosité actuelle
2. Interroge le service IA pour obtenir le scénario
3. Calcule l'intensité cible selon l'algorithme
4. Compare avec l'intensité actuelle des lampes allumées
5. Si écart > 10%, envoie une commande d'ajustement au Raspberry Pi
6. Applique un fade progressif (2 secondes en mode soirée, immédiat en jour)

**Possibilité d'apprentissage avancé (extension future) :**

Le système peut enregistrer les ajustements manuels effectués par l'utilisateur :
- Si l'utilisateur augmente souvent la lumière à 18h malgré le smart dimming, le système peut apprendre cette préférence
- Un modèle de régression linéaire peut être entraîné sur les données historiques (luminosité, heure, ajustement manuel)
- Le système prédit alors l'intensité préférée et l'applique automatiquement

**Cette fonctionnalité transforme le système d'un automate rigide en un assistant adaptatif apprenant les habitudes.**

**Contraintes techniques :**

- Précision du capteur : ±20 lux (suffisant pour l'algorithme)
- Latence capteur → ajustement : < 3 secondes
- Fréquence de mise à jour : 10 secondes (compromis réactivité/charge réseau)
- Protection contre les oscillations : hysteresis de 10% (éviter ajustements constants)

**Interface utilisateur :**

L'application mobile affiche :
- Indicateur visuel de luminosité ambiante (jauge colorée)
- Statut du smart dimming (actif/inactif/pause)
- Intensité cible calculée vs intensité actuelle
- Bouton pour désactiver temporairement (1 heure)
- Historique des ajustements automatiques

### 3.6 Visualisation

#### F10 : Graphique de Présence

**Fonctionnalité :**
- Graphique en barres des détections de présence sur les dernières 24 heures
- Intervalle : par heure
- Segmentation par pièce
- Code couleur par scénario actif

#### F11 : Graphique de Luminosité

**Fonctionnalité :**
- Graphique en courbe de l'évolution de la luminosité ambiante
- Période : 24 heures avec zoom ajustable
- Superposition avec l'intensité des lampes
- Visualisation de l'impact du smart dimming

**Intérêt pédagogique :**
Permet de visualiser la corrélation entre luminosité naturelle et ajustements automatiques, démontrant l'efficacité de l'algorithme adaptatif.

---

## 4. Base de Données

### 4.1 Choix Technologique

**SGBD :** PostgreSQL 14+

**Justification :**
- Fiabilité éprouvée
- Support natif du type JSONB pour les règles flexibles
- Performance des requêtes d'agrégation (historiques, statistiques)
- Licence open source
- Compatibilité avec SQLAlchemy

### 4.2 Schéma de Données Complet

#### Table : users
Gestion des utilisateurs du système.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- username : Nom d'utilisateur unique (50 caractères max)
- email : Adresse email unique (optionnelle)
- password_hash : Hash bcrypt du mot de passe
- created_at : Timestamp de création du compte

#### Table : raspberry_pis
Inventaire des Raspberry Pi connectés.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- name : Nom descriptif (ex: "RPi Salon")
- ip_address : Adresse IP unique (format IPv4)
- location : Pièce associée (ex: "Salon", "Chambre")
- is_online : Booléen indiquant la connectivité
- api_key : Clé API unique de 64 caractères pour authentification
- created_at : Timestamp d'ajout

#### Table : devices
Référentiel des appareils connectés.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- name : Nom descriptif (ex: "Lampe bureau")
- type : Type d'appareil ('light', 'outlet', 'sensor')
- raspberry_pi_id : Clé étrangère vers raspberry_pis
- gpio_pin : Numéro du GPIO utilisé
- state : État actuel (ON/OFF)
- brightness : Intensité lumineuse (0-100, NULL pour outlets)
- created_at : Timestamp de création

**Contraintes :**
- Combinaison (raspberry_pi_id, gpio_pin) unique

#### Table : presence
Historique des détections de mouvement.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- raspberry_pi_id : Clé étrangère vers raspberry_pis
- detected_at : Timestamp de la détection

**Index :**
- Index sur detected_at pour requêtes temporelles rapides

#### Table : light_readings
**Nouvelle table pour le smart dimming**

Historique des mesures de luminosité ambiante.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- raspberry_pi_id : Clé étrangère vers raspberry_pis
- lux_value : Valeur en lux mesurée (entier 0-65535)
- percentage : Pourcentage relatif (0-100, calculé)
- measured_at : Timestamp de la mesure

**Index :**
- Index sur (raspberry_pi_id, measured_at) pour requêtes temporelles par capteur

#### Table : events
Journal des événements système.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- device_id : Clé étrangère vers devices (nullable)
- event_type : Type d'événement (ex: 'light_on', 'dimming_adjusted')
- value : Valeur associée (format texte flexible)
- source : Source de l'événement ('manual', 'automatic', 'ai', 'smart_dimming')
- timestamp : Timestamp de l'événement

**Index :**
- Index sur (device_id, timestamp)

#### Table : rules
Définition des règles d'automatisation.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- name : Nom descriptif de la règle
- enabled : Booléen pour activer/désactiver
- condition : Conditions au format JSONB
- action : Actions au format JSONB
- created_at : Timestamp de création

**Format JSONB exemple :**

**Condition :**
```json
{
  "type": "AND",
  "clauses": [
    {"field": "light_level", "operator": "<", "value": 100},
    {"field": "presence", "operator": "==", "value": true}
  ]
}
```

**Action :**
```json
{
  "type": "set_brightness",
  "device_id": 3,
  "brightness": 80,
  "transition": "fade"
}
```

#### Table : training_data
Données d'entraînement pour l'algorithme d'IA.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- hour : Heure (0-23)
- day_of_week : Jour de la semaine (0-6)
- presence_detected : Booléen
- light_on : Booléen
- scenario : Label du scénario (0-3)
- created_at : Timestamp de génération

**Contraintes :**
- CHECK hour BETWEEN 0 AND 23
- CHECK day_of_week BETWEEN 0 AND 6
- CHECK scenario BETWEEN 0 AND 3

#### Table : dimming_adjustments
**Nouvelle table pour l'historique du smart dimming**

Enregistrement des ajustements automatiques d'intensité.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- device_id : Clé étrangère vers devices
- light_reading_id : Clé étrangère vers light_readings
- scenario : Scénario actif au moment de l'ajustement (0-3)
- previous_brightness : Intensité avant ajustement
- target_brightness : Intensité calculée par l'algorithme
- applied_brightness : Intensité réellement appliquée
- reason : Justification textuelle (ex: "High natural light")
- adjusted_at : Timestamp de l'ajustement

**Intérêt :**
Permet d'analyser l'efficacité du smart dimming et de détecter les patterns pour l'apprentissage futur.

#### Table : user_preferences
**Nouvelle table pour l'apprentissage des préférences**

Enregistrement des ajustements manuels effectués après un smart dimming.

**Colonnes :**
- id : Clé primaire auto-incrémentée
- user_id : Clé étrangère vers users
- device_id : Clé étrangère vers devices
- light_level : Niveau de luminosité ambiante au moment de l'ajustement
- scenario : Scénario actif
- auto_brightness : Intensité proposée par le système
- manual_brightness : Intensité choisie par l'utilisateur
- time_of_day : Heure (0-23)
- recorded_at : Timestamp

**Utilisation future :**
Ces données peuvent alimenter un modèle de régression pour personnaliser le smart dimming par utilisateur.

### 4.3 Relations entre Tables

```
users (1) ----< (N) user_preferences

raspberry_pis (1) ----< (N) devices
    |
    +-------< (N) presence
    |
    +-------< (N) light_readings

devices (1) ----< (N) events
    |
    +-------< (N) dimming_adjustments

light_readings (1) ----< (N) dimming_adjustments

rules (standalone, références JSONB vers devices)
training_data (standalone, apprentissage automatique)
```

### 4.4 Volumétrie Estimée

**Échelle temporelle : 1 mois**

| Table | Fréquence | Nombre d'entrées |
|-------|-----------|-----------------|
| presence | 20 détections/jour/capteur | ~600/mois |
| light_readings | 1 mesure/10s/capteur | ~260 000/mois |
| events | Variable selon activité | ~1000/mois |
| dimming_adjustments | ~10 ajustements/jour/lampe | ~300/mois |
| user_preferences | ~5 ajustements manuels/jour | ~150/mois |

**Stratégies d'optimisation :**
- Archivage des données > 3 mois
- Agrégation des mesures de luminosité (moyenne horaire après 1 semaine)
- Purge des événements non critiques après 6 mois

---

## 5. Technologies et Stack Technique

### 5.1 Backend (Serveur)

**Langage et framework :**
- Python 3.9+
- FastAPI 0.104+
- Uvicorn (serveur ASGI)
- Gunicorn (production, optionnel)

**Base de données :**
- SQLAlchemy 2.0+ (ORM)
- psycopg2-binary (driver PostgreSQL)
- Alembic (migrations)
- TimescaleDB (extension PostgreSQL pour time-series)

**Sécurité :**
- Pydantic (validation de données)
- python-jose (gestion JWT)
- passlib avec bcrypt (hachage mots de passe)

**Intelligence artificielle :**
- scikit-learn 1.3+ (Decision Tree, Random Forest, K-Means)
- pandas 2.1+ (manipulation données)
- numpy 1.26+ (calculs)
- joblib (sérialisation modèles)
- scikit-optimize (optimisation hyperparamètres, optionnel)

**Communication HTTP :**
- httpx (client HTTP asynchrone)
- requests (client HTTP synchrone)

**Structure du projet :**

```
backend/
├── app/
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── config.py                  # Configuration centralisée
│   ├── database.py                # Connexion PostgreSQL
│   ├── dependencies.py            # Dépendances FastAPI (auth, DB)
│   │
│   ├── models/                    # Modèles SQLAlchemy
│   │   ├── user.py                # Utilisateurs
│   │   ├── device.py              # Appareils
│   │   ├── raspberry_pi.py        # Raspberry Pi
│   │   ├── presence.py            # Détections de présence
│   │   ├── light_reading.py       # Mesures de luminosité
│   │   ├── rule.py                # Règles d'automatisation
│   │   ├── event.py               # Événements système
│   │   ├── smart_dimming_adjustment.py  # Historique smart dimming
│   │   ├── training_data.py       # Données d'entraînement IA
│   │   └── user_preference.py     # Préférences utilisateur
│   │
│   ├── routes/                    # Endpoints API
│   │   ├── auth.py                # Authentification
│   │   ├── devices.py             # Gestion appareils
│   │   ├── raspberry_pis.py       # Gestion Raspberry Pi
│   │   ├── presence.py            # Détections de présence
│   │   ├── light_readings.py      # Mesures de luminosité
│   │   ├── rules.py               # Règles d'automatisation
│   │   ├── ai.py                  # Intelligence artificielle
│   │   ├── smart_dimming.py      # Smart dimming
│   │   └── events.py              # Historique événements
│   │
│   ├── schemas/                   # Schémas Pydantic
│   │   ├── auth.py                # Authentification
│   │   ├── device.py              # Appareils
│   │   ├── raspberry_pi.py        # Raspberry Pi
│   │   ├── rule.py                # Règles
│   │   └── smart_dimming.py       # Smart dimming
│   │
│   ├── services/                  # Logique métier
│   │   ├── ai_service.py          # Service IA
│   │   ├── device_service.py      # Contrôle appareils
│   │   ├── rule_engine.py         # Moteur de règles
│   │   └── smart_dimming_service.py  # Service smart dimming
│   │
│   └── utils/                     # Utilitaires
│       ├── auth.py                # Fonctions JWT
│       └── validators.py          # Validateurs personnalisés
│
├── ml/                            # Machine Learning
│   ├── generate_data.py           # Génération données synthétiques (classification)
│   ├── train_model.py             # Entraînement Decision Tree
│   ├── generate_regression_data.py # Données régression (intensité)
│   ├── train_regression_model.py   # Entraînement Random Forest (régression)
│   └── models/                    # Modèles sauvegardés (.pkl, métriques)
│
├── requirements.txt               # Dépendances Python
├── .env.example                   # Exemple de configuration
└── README.md                      # Documentation
```

### 5.2 Raspberry Pi (Contrôleur)

**Système d'exploitation :**
- Raspberry Pi OS Lite (Debian)

**Framework web :**
- Flask 2.3+
- Flask-CORS 4.0+

**Option Z-Wave (implémentation actuelle dans `raspberry/`) :** API Flask + Z-Wave JS (voir section 5.2 ci-dessus). **Option GPIO / PIR :** RPi.GPIO (capteur PIR, LED, relais), smbus2 (BH1750), spidev (LDR). Structure alternative : `raspberry-pi/sensors/` (pir_sensor, light_sensor_*), `actuators/`, `api/local_api.py`, `services/` (server_client, device_manager, event_reporter, light_monitor).

**Service light_monitor.py (option GPIO) :**
Ce service lit périodiquement le capteur de luminosité et envoie les valeurs au backend :
- Fréquence : toutes les 10 secondes
- Format : JSON avec lux_value et timestamp
- Endpoint backend : POST /api/light_readings
- Gestion des erreurs de connexion avec retry

### 5.3 Application Mobile (Android)

**Langage :**
- Kotlin 1.9+

**UI :**
- Jetpack Compose (dernière version stable)
- Material Design 3

**Architecture :**
- Pattern MVVM (Model-View-ViewModel)
- StateFlow et Coroutines pour gestion asynchrone
- Hilt pour injection de dépendances

**Réseau :**
- Retrofit 2.9+ (client REST)
- OkHttp 4.11+ (gestion HTTP)
- Gson (sérialisation JSON)

**Persistance locale :**
- DataStore Preferences (stockage JWT)
- Room (cache local optionnel)

**Structure du projet :**

```
mobile/SmartHome/app/src/main/java/com/example/smarthome/
├── data/
│   ├── model/                  # Modèles de données (Device, Rule, etc.)
│   ├── remote/                 # Couche réseau (Retrofit)
│   │   ├── ApiService.kt
│   │   ├── AuthInterceptor.kt
│   │   └── dto/               # Data Transfer Objects
│   └── repository/             # Pattern Repository
│       ├── DeviceRepository.kt
│       ├── RuleRepository.kt
│       └── SmartDimmingRepository.kt
├── ui/
│   ├── screens/                # Écrans principaux
│   │   ├── DashboardScreen.kt
│   │   ├── DevicesScreen.kt
│   │   ├── RulesScreen.kt
│   │   ├── HistoryScreen.kt
│   │   └── SmartDimmingScreen.kt
│   ├── components/             # Composants réutilisables
│   │   ├── DeviceCard.kt
│   │   ├── BrightnessSlider.kt
│   │   ├── LightIndicator.kt
│   │   └── ScenarioChip.kt
│   └── theme/                  # Thème Material 3
├── viewmodel/                  # ViewModels
│   ├── DashboardViewModel.kt
│   ├── DeviceViewModel.kt
│   ├── RuleViewModel.kt
│   └── SmartDimmingViewModel.kt
├── di/                         # Modules Hilt
└── MainActivity.kt
```

**SmartDimmingScreen.kt :**
Écran dédié à la visualisation et au contrôle du smart dimming :
- Jauge de luminosité ambiante en temps réel
- Graphique d'évolution luminosité/intensité lampes (24h)
- Toggle pour activer/désactiver temporairement
- Liste des derniers ajustements automatiques avec justifications
- Indicateur du scénario actif

### 5.4 Application Web (Next.js)

**Framework :** Next.js 16+ (App Router), React 19, TypeScript. **UI :** Tailwind CSS 4, Radix UI, Recharts. **Fonctionnalités :** Authentification (login, JWT), tableau de bord (appareils, règles), pages admin (présence), graphiques présence/luminosité. **Structure :** `web/app/(protected)/`, `web/app/login/`, `web/lib/` (services API).

---

## 6. Communication entre Composants

### 6.1 Protocoles

**Mobile → Backend**
- Protocole : HTTP/REST
- Format : JSON
- Authentification : Bearer Token (JWT)
- Port : 8000

**Backend → Raspberry Pi**
- Protocole : HTTP/REST
- Format : JSON
- Authentification : API Key (header X-API-Key)
- Port : 5000

**Raspberry Pi → Backend**
- Protocole : HTTP/REST
- Format : JSON
- Authentification : API Key
- Types : Heartbeat, événements de détection, mesures de luminosité, changements d'état

### 6.2 Flux de Données : Allumage d'une Lampe (Contrôle Manuel)

1. **Utilisateur** clique sur le bouton ON dans l'application mobile
2. **ViewModel** met à jour l'état local optimiste et appelle le Repository
3. **Repository** envoie une requête POST au backend via Retrofit
4. **Backend** valide le JWT et les paramètres (device_id, brightness)
5. **Backend** envoie une requête HTTP POST au Raspberry Pi avec l'API Key
6. **Raspberry Pi** valide la clé API et configure le signal PWM sur le GPIO
7. **Lampe physique** s'allume à l'intensité demandée
8. **Raspberry Pi** retourne une confirmation avec l'état réel
9. **Backend** enregistre l'événement dans la table events (source: 'manual')
10. **Backend** retourne le nouvel état à l'application mobile
11. **UI mobile** se met à jour pour refléter le changement

**Temps total estimé :** < 2 secondes

### 6.3 Flux de Données : Détection de Présence avec Règle

1. **Capteur PIR** détecte un mouvement (changement GPIO HIGH)
2. **Module pir_sensor.py** lit le changement d'état GPIO
3. **Filtrage anti-rebond** vérifie qu'aucune détection récente (< 5s)
4. **EventReporter** envoie immédiatement un POST au backend
5. **Backend** enregistre la détection dans la table presence
6. **RuleEngine** est déclenché et évalue toutes les règles actives
7. Si une règle est satisfaite, **DeviceService** exécute l'action définie
8. **Backend** envoie la commande au Raspberry Pi concerné
9. **Appareil** change d'état selon l'action (ex: allumage lampe à 70%)
10. **Backend** enregistre l'événement avec source 'automatic'

**Temps total estimé :** < 3 secondes

### 6.4 Flux de Données : Smart Dimming (Adaptation Dynamique)

**Cas : Luminosité naturelle augmente, système réduit intensité artificielle**

1. **Capteur BH1750** mesure la luminosité ambiante (I²C)
2. **LightMonitor service** lit la valeur toutes les 10 secondes
3. **LightMonitor** envoie POST /api/light_readings au backend avec valeur en lux
4. **Backend** enregistre la mesure dans light_readings
5. **SmartDimmingService** est déclenché (hook post-insertion)
6. **SmartDimmingService** récupère :
   - Luminosité actuelle (ex: 600 lux)
   - Scénario actif via AIService (ex: "Day")
   - Liste des lampes allumées dans la pièce
7. **Algorithme de calcul** détermine intensité cible selon le scénario :
   - Mode Day, 600 lux → intensité cible = 25% (luminosité élevée)
8. **SmartDimmingService** compare avec intensité actuelle (ex: 70%)
9. Écart significatif (45%) → commande d'ajustement nécessaire
10. **Backend** envoie POST /api/devices/{id}/brightness au Raspberry Pi
11. **Raspberry Pi** applique le PWM progressivement (fade immédiat en mode Day)
12. **Backend** enregistre l'ajustement dans dimming_adjustments avec :
    - previous_brightness: 70
    - target_brightness: 25
    - reason: "High natural light detected (600 lux)"
    - source: 'smart_dimming'
13. **Backend** enregistre également l'événement dans events
14. **Application mobile** reçoit la notification de changement (via polling ou WebSocket)
15. **UI** met à jour l'affichage avec la nouvelle intensité et le motif

**Temps total estimé :** < 3 secondes

**Protection contre oscillations :**
Si l'utilisateur ajuste manuellement la lampe dans les 2 minutes suivant un smart dimming, le système :
- Enregistre la préférence dans user_preferences
- Désactive temporairement le smart dimming pour cette lampe (30 minutes)
- Affiche une notification "Smart dimming pausé selon votre préférence"

### 6.5 API Endpoints Principaux

**Authentification :**
- POST /api/auth/login → JWT token
- POST /api/auth/register → Création utilisateur

**Appareils :**
- GET /api/devices → Liste des appareils
- GET /api/devices/{id} → Détails d'un appareil
- PUT /api/devices/{id}/state → Changer état (ON/OFF)
- PUT /api/devices/{id}/brightness → Changer intensité

**Règles :**
- GET /api/rules → Liste des règles
- POST /api/rules → Créer une règle
- PUT /api/rules/{id} → Modifier une règle
- DELETE /api/rules/{id} → Supprimer une règle

**IA et Scénarios :**
- GET /api/ai/current_scenario → Scénario actif actuel
- POST /api/ai/classify → Classification manuelle

**Smart Dimming :**
- GET /api/smart_dimming/status → État global du système
- GET /api/smart_dimming/adjustments → Historique des ajustements
- PUT /api/smart_dimming/enable → Activer/désactiver globalement
- PUT /api/smart_dimming/pause/{device_id} → Pause temporaire pour un appareil

**Capteurs :**
- POST /api/light_readings → Enregistrer mesure luminosité (utilisé par RPi)
- GET /api/light_readings → Historique des mesures

**Événements :**
- GET /api/events → Historique des événements
- GET /api/events/device/{id} → Événements d'un appareil

---

## 7. Sécurité

### 7.1 Authentification

**JWT (JSON Web Tokens) pour l'application mobile :**
- Algorithme : HS256 (HMAC SHA-256)
- Payload : user_id, username, exp (expiration), iat (émission)
- Durée de validité : 24 heures
- Stockage mobile : DataStore Preferences (Android)
- Refresh token : Non implémenté (simplification pour projet académique)

**Cycle de vie JWT :**
1. Utilisateur fournit username/password via écran de connexion
2. Backend vérifie le hash bcrypt stocké en base
3. Token JWT généré avec payload et signature HMAC
4. Token retourné à l'application mobile
5. Token stocké dans DataStore de manière sécurisée
6. Token envoyé dans header Authorization: Bearer {token} pour chaque requête
7. Backend valide signature et expiration à chaque requête protégée

**API Key pour Raspberry Pi :**
- Longueur : 64 caractères hexadécimaux
- Génération : cryptographiquement sécurisée (secrets.token_hex)
- Unique par Raspberry Pi
- Header : X-API-Key
- Stockage : table raspberry_pis
- Rotation : Manuelle via interface admin

**Validation API Key :**
Le backend vérifie la présence et la validité de la clé API pour toutes les requêtes provenant des Raspberry Pi. Si invalide, retour HTTP 401 Unauthorized.

### 7.2 Hachage des Mots de Passe

- Algorithme : bcrypt
- Cost factor : 12 rounds minimum (compromis sécurité/performance)
- Salt : généré automatiquement par bcrypt
- Stockage : hash uniquement, jamais en clair
- Librairie : passlib avec CryptContext

### 7.3 Validation des Entrées

**Validation côté serveur (Pydantic) :**
Tous les endpoints utilisent des schémas Pydantic pour valider :
- Type de données strict (int, str, bool, float)
- Plage de valeurs (ex: brightness entre 0 et 100)
- Format (ex: regex pour email, pattern pour GPIO pin)
- Cohérence métier (ex: gpio_pin unique par raspberry_pi)

**Protection contre injections SQL :**
- Utilisation exclusive de requêtes préparées via SQLAlchemy ORM
- Paramètres bindés automatiquement
- Pas de concaténation de chaînes SQL

**Protection XSS :**
- Échappement automatique dans les réponses JSON
- Validation stricte des champs JSONB (règles)

**Rate Limiting :**
Non implémenté dans la version académique, mais recommandé pour production :
- Limiter à 100 requêtes/minute par IP pour les endpoints publics
- Limiter à 10 tentatives de connexion/minute

### 7.4 HTTPS / TLS

**Environnement de développement :**
- HTTP non chiffré (acceptable pour réseau local IUT)

**Recommandation production :**
- Utiliser HTTPS avec certificat Let's Encrypt
- Redirection automatique HTTP → HTTPS
- Configuration Uvicorn avec SSL context

### 7.5 Sécurité Raspberry Pi

**Accès SSH :**
- Désactiver authentification par mot de passe
- Utiliser uniquement clés SSH
- Changer port par défaut (22 → port personnalisé)

**Firewall :**
- Autoriser uniquement port 5000 (Flask API)
- Bloquer tout autre trafic entrant

**Mise à jour :**
- Automatiser les mises à jour de sécurité du système

---

## 8. Déploiement

### 8.1 Environnement de Déploiement

**Option retenue : Serveur IUT + Raspberry Pi local**

**Avantages :**
- Infrastructure fournie et maintenue
- Pas de coûts d'hébergement
- Accès au serveur Ollama IUT (si besoin IA avancée future)
- Réseau local rapide

**Prérequis serveur :**
- Python 3.9+
- PostgreSQL 14+
- Accès SSH
- Droits d'installation de packages

**Prérequis Raspberry Pi :**
- Raspberry Pi OS Lite (dernière version)
- Connexion réseau stable (Ethernet recommandé pour fiabilité)
- Carte SD de qualité classe 10 minimum (32 Go recommandé)
- Alimentation 5V 3A officielle

### 8.2 Installation Backend

**Étapes détaillées :**

**1. Clonage du repository**
```bash
git clone https://github.com/votre-equipe/smarthome-backend.git
cd smarthome-backend
```

**2. Création environnement virtuel**
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Installation dépendances**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Configuration variables d'environnement**
Créer un fichier .env à la racine avec :
```
DATABASE_URL=postgresql://user:password@localhost:5432/smarthome
SECRET_KEY=your_secret_key_here_minimum_32_chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

**5. Initialisation base de données**
```bash
# Créer la base PostgreSQL
createdb smarthome

# Activer TimescaleDB (optionnel, pour time-series)
psql -d smarthome -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Exécuter le script d'initialisation
psql -d smarthome -f db/init_database.sql
```

**6. Génération données d'entraînement IA**
```bash
# Générer 1000 échantillons de données synthétiques
python ml/generate_data.py --samples 1000

# Entraîner le modèle Decision Tree
python ml/train_model.py --max-depth 7

# Vérifier que le modèle a été créé
ls -lh ml/models/scenario_classifier.pkl
```

**7. Lancement du serveur**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**8. Vérification**
Accéder à http://localhost:8000/docs pour la documentation Swagger de l'API.

**9. Service systemd (optionnel, pour production)**
Créer /etc/systemd/system/smarthome-backend.service pour démarrage automatique.

### 8.3 Installation Raspberry Pi

**Étapes détaillées :**

**1. Configuration système de base**
```bash
# Mise à jour complète
sudo apt update && sudo apt upgrade -y

# Installation Python et outils
sudo apt install python3-pip python3-venv git i2c-tools -y

# Activer I2C pour BH1750
sudo raspi-config
# Sélectionner Interfacing Options → I2C → Enable
```

**2. Clonage et installation**
```bash
git clone https://github.com/votre-equipe/smarthome-rpi.git
cd smarthome-rpi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Configuration**
Éditer config.py avec :
- URL du serveur backend (ex: http://serveur-iut:8000)
- API Key unique (récupérée depuis l'interface admin backend)
- Numéros de pins GPIO selon câblage physique
- Type de capteur de luminosité (BH1750 ou LDR)

**4. Vérification capteur I2C**
```bash
i2cdetect -y 1
# Doit afficher l'adresse 0x23 si BH1750 connecté
```

**5. Vérification de connexion au backend**
```bash
python main.py --test-connection
# Doit afficher "Connection successful" + informations du serveur
```

**6. Lancement du service**
```bash
python main.py
# Vérifier les logs :
# - Initialisation capteurs
# - Connexion backend réussie
# - Heartbeat toutes les 60 secondes
```

**7. Service systemd**
Créer /etc/systemd/system/smarthome-rpi.service pour démarrage automatique au boot.

### 8.4 Application Web (Next.js)

**Développement :**
```bash
cd web
npm install
npm run dev
```
Accès : http://localhost:3000

**Build de production :**
```bash
cd web
npm run build
npm run start
```

**Configuration :** Définir l’URL de l’API backend (variable d’environnement ou fichier de config) pour que le frontend appelle le bon serveur.

### 8.5 Déploiement Application Mobile

**Build de l'APK :**

**1. Configuration**
Éditer app/src/main/res/values/config.xml avec :
- URL du serveur backend (ex: http://serveur-iut:8000)
- Timeout réseau
- Fréquence de rafraîchissement

**2. Génération APK de release**
```bash
./gradlew assembleRelease
```

**3. Signature APK (optionnel, pour distribution)**
Utiliser Android Studio ou jarsigner pour signer l'APK avec un keystore.

**4. Fichier généré**
- Emplacement : app/build/outputs/apk/release/app-release.apk
- Taille attendue : 15-20 Mo

**Installation sur appareil Android :**

1. Transférer l'APK sur le téléphone (USB, email, cloud)
2. Activer "Sources inconnues" dans Paramètres → Sécurité
3. Ouvrir l'APK et installer
4. Lancer l'application
5. Écran de connexion : entrer username/password
6. Vérifier la connexion au serveur (indicateur réseau)

**Dépannage :**
- Si erreur de connexion : vérifier URL backend dans config.xml
- Si lenteur : vérifier que le serveur est accessible depuis le réseau mobile
- Si crash : consulter les logs via Android Studio (adb logcat)

### 8.6 Scripts de Déploiement Automatisé

**Création de scripts bash pour automatiser :**

**deploy_backend.sh :**
- Clone repo
- Installe dépendances
- Configure .env
- Lance migrations
- Entraîne modèle IA
- Démarre serveur

**deploy_rpi.sh :**
- Clone repo
- Installe dépendances
- Configure GPIO
- Teste capteurs
- Lance service

**Ces scripts réduisent les erreurs humaines et accélèrent le déploiement.**

---

## 9. Livrables

### 9.1 Code Source

**Repository Git incluant :**
- Code backend (FastAPI) avec tous les services
- Code Raspberry Pi (Flask + Z-Wave ou GPIO/capteurs)
- Code application web (Next.js)
- Code application mobile (Kotlin + Compose)
- Scripts de migration base de données (Alembic)
- Scripts d'entraînement IA (génération + training)
- Fichiers de configuration d'exemple (.env.example, config.example.py)
- README.md détaillé avec instructions d'installation
- .gitignore complet (exclusion .env, venv, .pkl)

**Organisation branches Git :**
- main : version stable
- develop : développement en cours
- feature/* : fonctionnalités spécifiques
- hotfix/* : corrections urgentes

### 9.2 Documentation

**Documentation technique (ce document) :**
- Architecture système complète
- Schéma base de données avec relations
- Description détaillée des fonctionnalités
- Guide d'installation pas à pas
- Stack technique justifié
- Diagrammes de flux

**Documentation API :**
- Swagger/OpenAPI auto-générée par FastAPI
- Accessible à /docs sur le serveur
- Liste complète des endpoints avec paramètres
- Exemples de requêtes/réponses
- Codes d'erreur détaillés

**Guide utilisateur :**
- Manuel d'utilisation de l'application mobile
- Captures d'écran annotées de chaque écran
- Tutoriel pas à pas pour créer une règle
- Tutoriel configuration smart dimming
- FAQ des problèmes courants

**Schémas et diagrammes :**
- Architecture globale (présenté dans ce document)
- Diagramme de séquence pour chaque flux majeur
- Schéma de câblage Raspberry Pi (Fritzing)
- Diagramme entité-relation de la base de données

### 9.3 Application Mobile

**Package APK :**
- Fichier app-release.apk signé
- Fichier d'information (version, date, taille, checksums)
- Instructions d'installation détaillées

**Captures d'écran :**
- Tableau de bord principal
- Écran de contrôle des appareils
- Écran de création de règles
- Écran smart dimming
- Écran historique

### 9.4 Vidéo de Démonstration

**Durée : 2-3 minutes**

**Structure détaillée :**

1. **Introduction (15 secondes)**
   - Présentation du projet SmartHome Lite
   - Présentation rapide de l'équipe
   - Contexte SAE BUT3 FA 2025

2. **Architecture (30 secondes)**
   - Schéma animé du système (3 couches)
   - Highlight du Raspberry Pi avec capteurs
   - Highlight du backend avec IA
   - Highlight de l'application mobile

3. **Démonstration fonctionnelle (90 secondes)**

   **Partie 1 : Contrôle manuel (20s)**
   - Vue du tableau de bord avec appareils
   - Allumage d'une lampe via toggle
   - Ajustement d'intensité via slider
   - Confirmation visuelle sur lampe physique

   **Partie 2 : Détection et automatisation (30s)**
   - Détection de présence par capteur PIR
   - Déclenchement automatique d'une règle
   - Lampe s'allume automatiquement
   - Affichage événement dans historique

   **Partie 3 : Smart dimming (40s)**
   - Écran smart dimming avec jauge luminosité
   - Simulation augmentation lumière naturelle (lampe vers fenêtre)
   - Système réduit automatiquement intensité lampe
   - Graphique montrant corrélation luminosité/intensité
   - Affichage du scénario IA actif ("Day")
   - Justification textuelle de l'ajustement

4. **Technologies et métriques (20 secondes)**
   - Stack technique résumé
   - Métriques clés :
     - Temps de réponse < 2s
     - Accuracy IA > 70%
     - Smart dimming : économie d'énergie estimée
   - Logos des technologies (Python, Kotlin, PostgreSQL, scikit-learn)

5. **Conclusion (15 secondes)**
   - Bilan des fonctionnalités réalisées
   - Conformité aux contraintes SAE
   - Perspectives d'amélioration (apprentissage personnalisé)
   - Remerciements

**Qualité technique :**
- Résolution : 1080p minimum
- Audio clair avec voix-off professionnelle
- Sous-titres français pour accessibilité
- Montage fluide avec transitions simples
- Musique de fond discrète

**Outils recommandés :**
- OBS Studio pour capture d'écran
- DaVinci Resolve pour montage
- Audacity pour voix-off

### 9.5 Présentation Orale

**Support PowerPoint/PDF (15-20 slides) :**

1. Page de titre
2. Contexte et problématique
3. Architecture globale
4. Matériel utilisé (Raspberry Pi + capteurs)
5. Fonctionnalités principales
6. Smart dimming (cœur de l'innovation)
7. Intelligence artificielle (classification)
8. Base de données et modélisation
9. Stack technique
10. Démo vidéo