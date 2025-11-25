
# Backend - SmartHome Lite API

Backend FastAPI avec **architecture modulaire monolithique** et fonctionnalités avancées d'intelligence artificielle et d'automatisation.

## Table des Matières

- [Architecture](#architecture)
- [Fonctionnalités](#fonctionnalités)
  - [Implémentées](#implémentées)
  - [À implémenter](#à-implémenter)
- [Structure du Projet](#structure-du-projet)
- [Installation](#installation)
  - [Prérequis](#prérequis)
  - [Étapes d'Installation](#étapes-dinstallation)
- [Configuration](#configuration)
  - [Variables d'Environnement](#variables-denvironnement)
  - [Configuration Smart Dimming](#configuration-smart-dimming)
- [API Documentation](#api-documentation)
- [Endpoints Principaux](#endpoints-principaux)
  - [Authentification](#authentification)
  - [Appareils](#appareils)
  - [Raspberry Pi](#raspberry-pi)
  - [Présence](#présence)
  - [Mesures de Luminosité](#mesures-de-luminosité)
  - [Règles d'Automatisation](#règles-dautomatisation)
  - [Intelligence Artificielle](#intelligence-artificielle)
  - [Smart Dimming](#smart-dimming)
  - [Événements](#événements)
- [Intelligence Artificielle](#intelligence-artificielle-1)
  - [Classification de Scénarios (Implémenté)](#classification-de-scénarios-implémenté)
  - [Régression pour Prédiction d'Intensité (À implémenter)](#régression-pour-prédiction-dintensité-à-implémenter)
  - [Clustering des Habitudes (À implémenter)](#clustering-des-habitudes-à-implémenter)
- [Smart Dimming](#smart-dimming-1)
  - [Principe de Fonctionnement](#principe-de-fonctionnement)
  - [Algorithme d'Ajustement](#algorithme-dajustement)
  - [Protection contre Oscillations](#protection-contre-oscillations)
- [Moteur de Règles](#moteur-de-règles)
  - [Conditions Disponibles](#conditions-disponibles)
  - [Actions Disponibles](#actions-disponibles)
  - [Format JSON des Règles](#format-json-des-règles)
  - [Exécution](#exécution)
- [Base de Données](#base-de-données)
  - [Schéma Principal](#schéma-principal)
  - [TimescaleDB (Optionnel)](#timescaledb-optionnel)
- [Communication avec Raspberry Pi](#communication-avec-raspberry-pi)
  - [Protocole](#protocole)
  - [Commandes Envoyées](#commandes-envoyées)
  - [Événements Reçus](#événements-reçus)
- [Sécurité](#sécurité)
  - [Authentification JWT](#authentification-jwt)
  - [API Key pour Raspberry Pi](#api-key-pour-raspberry-pi)
  - [Hachage des Mots de Passe](#hachage-des-mots-de-passe)
  - [Validation des Entrées](#validation-des-entrées)
- [Déploiement](#déploiement)
  - [Développement](#développement)
  - [Production](#production)
  - [Service systemd (Linux)](#service-systemd-linux)
- [Dépannage](#dépannage)
  - [Problèmes Courants](#problèmes-courants)
- [Contribution](#contribution)
- [Licence](#licence)

## Architecture

Le backend utilise une **architecture modulaire monolithique** avec séparation claire des responsabilités. Cette architecture permet un développement efficace tout en maintenant une structure claire et maintenable.

**Principes architecturaux :**
- **Modularité** : Séparation des responsabilités en modules indépendants
- **Services** : Logique métier isolée et testable
- **ORM** : SQLAlchemy pour l'accès aux données
- **Validation** : Pydantic pour la validation des données
- **IA multi-modèles** : Classification, régression et clustering (partiellement implémenté)

**Composants principaux :**
- **Routes** : Endpoints API REST organisés par domaine
- **Services** : Logique métier isolée et testable
- **Models** : Modèles SQLAlchemy (ORM)
- **Schemas** : Validation Pydantic
- **ML** : Module d'intelligence artificielle

## Fonctionnalités

### Implémentées

- **Authentification** : JWT avec tokens d'accès (HS256, expiration 24h) - routes `/api/auth/login`, `/api/auth/register`, `/api/auth/me`
- **Gestion d'appareils** : CRUD complet et contrôle en temps réel - routes `/api/devices` avec contrôle d'état (`PUT /api/devices/{id}/state`) et intensité (`PUT /api/devices/{id}/brightness`)
- **Moteur de règles** : Automatisation IF-THEN avec évaluation conditionnelle - routes `/api/rules` (CRUD complet) avec évaluation automatique lors des événements
- **Smart Dimming** : Ajustement intelligent de l'éclairage basé sur la luminosité ambiante - routes `/api/smart-dimming/status`, `/api/smart-dimming/adjustments`, `/api/smart-dimming/enable`, `/api/smart-dimming/pause/{device_id}`
- **Intelligence Artificielle** : Classification de scénarios (Decision Tree Classifier) - routes `/api/ai/current-scenario`, `/api/ai/classify`, `/api/ai/model-metrics` avec modèle entraîné
- **Gestion Raspberry Pi** : Enregistrement et suivi des Raspberry Pi connectés - routes `/api/raspberry-pis` (CRUD) avec authentification par API Key pour les endpoints appelés par RPi
- **Détection de présence** : Enregistrement et historique des détections - routes `POST /api/presence` (appelé par RPi) et `GET /api/presence` (historique) avec déclenchement automatique des règles
- **Mesures de luminosité** : Stockage des lectures de capteurs (BH1750/LDR) - routes `POST /api/light-readings` (appelé par RPi) et `GET /api/light-readings` (historique) avec déclenchement automatique du smart dimming
- **Événements système** : Journalisation des événements (changements d'état, ajustements, etc.) - routes `GET /api/events` et `GET /api/events/device/{id}` avec filtres
- **Historique Smart Dimming** : Suivi des ajustements automatiques - route `GET /api/smart-dimming/adjustments` avec filtres par `device_id` et `limit`
- **Pause Smart Dimming** : Mise en pause temporaire par appareil - route `PUT /api/smart-dimming/pause/{device_id}` (pause de 30 minutes)
- **Évaluation de règles** : Évaluation manuelle des règles d'automatisation - route `POST /api/rules/{id}/test` pour tester une règle dans le contexte actuel
- **Métriques IA** : Informations sur le modèle chargé - route `GET /api/ai/model-metrics` retourne l'état du modèle, l'accuracy (si disponible), et les scénarios détectables
- **Modèle préférences utilisateur** : Table `user_preferences` créée en base de données pour apprentissage futur (pas encore de route dédiée)

### À implémenter

- **Régression IA** : Prédiction d'intensité lumineuse optimale (Random Forest Regressor)
- **Clustering** : Détection automatique de profils utilisateur (K-Means)
- **WebSockets** : Synchronisation temps réel pour l'application mobile (optionnel)

## Structure du Projet

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
│   │   ├── device.py              # Appareils (lampes, prises)
│   │   ├── raspberry_pi.py        # Raspberry Pi
│   │   ├── presence.py            # Détections de présence
│   │   ├── light_reading.py       # Mesures de luminosité
│   │   ├── rule.py                # Règles d'automatisation
│   │   ├── event.py               # Événements système
│   │   ├── smart_dimming_adjustment.py  # Historique smart dimming
│   │   ├── training_data.py       # Données d'entraînement IA
│   │   └── user_preference.py     # Préférences utilisateur
│   │
│   ├── schemas/                   # Schémas Pydantic
│   │   ├── auth.py                # Authentification
│   │   ├── device.py              # Appareils
│   │   ├── raspberry_pi.py        # Raspberry Pi
│   │   ├── rule.py                # Règles
│   │   └── smart_dimming.py       # Smart Dimming
│   │
│   ├── routes/                    # Endpoints API
│   │   ├── auth.py                # POST /api/auth/login, /register
│   │   ├── devices.py             # CRUD appareils
│   │   ├── raspberry_pis.py       # Gestion Raspberry Pi
│   │   ├── presence.py            # Détections de présence
│   │   ├── light_readings.py      # Mesures de luminosité
│   │   ├── rules.py               # CRUD règles
│   │   ├── ai.py                  # Endpoints IA
│   │   ├── smart_dimming.py      # Contrôle smart dimming
│   │   └── events.py              # Historique événements
│   │
│   ├── services/                  # Logique métier
│   │   ├── ai_service.py          # Service IA (classification)
│   │   ├── device_service.py      # Contrôle appareils
│   │   ├── rule_engine.py         # Moteur de règles
│   │   └── smart_dimming_service.py  # Service smart dimming
│   │
│   └── utils/                     # Utilitaires
│       ├── auth.py                # Fonctions JWT
│       └── validators.py          # Validateurs personnalisés
│
├── ml/                            # Machine Learning
│   ├── generate_data.py           # Génération données synthétiques
│   ├── train_model.py             # Entraînement Decision Tree
│   └── models/                    # Modèles sauvegardés (.pkl)
│       ├── .gitkeep               # Dossier pour modèles ML
│       └── scenario_classifier.pkl # Modèle entraîné (généré après training)
│
├── requirements.txt               # Dépendances Python
├── .env.example                   # Exemple de configuration
└── README.md                      # Ce fichier
```

## Démarrage Rapide

Pour lancer rapidement le backend (Windows PowerShell) :

```powershell
# 1. Aller dans le dossier backend
cd backend

# 2. Créer et activer l'environnement virtuel
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 4. Lancer le serveur (la configuration par défaut est dans app/config.py)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note** : Le backend peut démarrer sans base de données (avec des warnings), mais certaines fonctionnalités nécessiteront PostgreSQL. Le modèle IA est optionnel et l'application utilisera un mode fallback s'il n'est pas disponible.

## Installation

### Prérequis

- **Python** : 3.10 ou supérieur
- **PostgreSQL** : 14+ (avec extension TimescaleDB optionnelle pour time-series)
  - **Note** : Le backend peut démarrer sans PostgreSQL, mais les fonctionnalités nécessitant la base de données ne fonctionneront pas.

### Étapes d'Installation

#### 1. Naviguer vers le dossier backend

**Windows (PowerShell) :**
```powershell
cd backend
```

**Linux/Mac :**
```bash
cd backend
```

#### 2. Créer l'environnement virtuel

**Windows (PowerShell) :**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac :**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Note Windows** : Si vous obtenez une erreur d'exécution de script, exécutez d'abord :
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. Installer les dépendances

```powershell
# Windows / Linux / Mac
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configurer les variables d'environnement (Optionnel)

Le backend utilise des valeurs par défaut définies dans `app/config.py`. Si vous souhaitez personnaliser la configuration :

**Windows (PowerShell) :**
```powershell
# Créer le fichier .env (si .env.example existe)
Copy-Item .env.example .env
# Éditer .env avec votre éditeur de texte
```

**Linux/Mac :**
```bash
cp .env.example .env
# Éditer .env avec votre éditeur de texte
```

Variables minimales requises dans `.env` (si vous créez le fichier) :
```env
DATABASE_URL=postgresql://user:password@localhost:5432/smarthome
SECRET_KEY=your-secret-key-minimum-32-characters-long
```

**Configuration par défaut** (dans `app/config.py`) :
- Base de données : `postgresql://postgres:smarthome2025@10.109.150.75:5432/smarthome`
- Port API : `8000`
- Host API : `0.0.0.0`

#### 5. Initialiser la base de données (Optionnel mais recommandé)

Si vous avez PostgreSQL installé :

**Windows (PowerShell) :**
```powershell
# Créer la base PostgreSQL (si psql est dans votre PATH)
createdb smarthome

# Activer TimescaleDB (optionnel)
psql -d smarthome -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Exécuter le script d'initialisation (si disponible)
# psql -d smarthome -f ..\db\init_database.sql
```

**Linux/Mac :**
```bash
createdb smarthome
psql -d smarthome -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
psql -d smarthome -f ../db/init_database.sql
```

**Note** : Si la base de données n'est pas accessible, le backend démarrera quand même avec des warnings. Les tables seront créées automatiquement au premier démarrage si la connexion fonctionne.

#### 6. Générer et entraîner le modèle IA (Optionnel)

Le modèle IA est optionnel. L'application utilisera un mode fallback s'il n'est pas disponible.

**Windows (PowerShell) :**
```powershell
# Générer 1000 échantillons de données synthétiques
python ml\generate_data.py --samples 1000

# Entraîner le modèle Decision Tree
python ml\train_model.py --max-depth 7

# Vérifier que le modèle a été créé
Get-ChildItem ml\models\scenario_classifier.pkl
```

**Linux/Mac :**
```bash
python ml/generate_data.py --samples 1000
python ml/train_model.py --max-depth 7
ls -lh ml/models/scenario_classifier.pkl
```

#### 7. Lancer le serveur

**Windows (PowerShell) :**
```powershell
# Assurez-vous que l'environnement virtuel est activé
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Linux/Mac :**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 8. Vérification

Une fois le serveur lancé :

- **Documentation Swagger** : http://localhost:8000/docs
- **Documentation ReDoc** : http://localhost:8000/redoc
- **Health Check** : http://localhost:8000/health
- **API Root** : http://localhost:8000/

Le endpoint `/health` vous indiquera l'état de la connexion à la base de données.

## Configuration

### Variables d'Environnement

Fichier `.env` (voir `.env.example` pour la liste complète) :

```env
# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/smarthome
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=smarthome
DATABASE_USER=postgres
DATABASE_PASSWORD=password

# Sécurité
SECRET_KEY=your-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Serveur
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
ENVIRONMENT=development

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Raspberry Pi
RASPBERRY_PI_PROTOCOL=http
RASPBERRY_PI_PORT=5000
RASPBERRY_PI_TIMEOUT=5

# Machine Learning
ML_MODEL_PATH=ml/models/scenario_classifier.pkl

# Smart Dimming
SMART_DIMMING_ENABLED=True
SMART_DIMMING_THRESHOLD=10

# Logging
LOG_LEVEL=INFO
```

### Configuration Smart Dimming

Les paramètres de smart dimming sont définis dans `app/config.py` via la propriété `dimming_params`. Ils varient selon le scénario détecté :

- **Mode Day (0)** : Seuil haut 500 lux → intensité 20%, seuil bas 200 lux → intensité 70%
- **Mode Evening (3)** : Seuil haut 200 lux → intensité 30%, seuil bas 50 lux → intensité 75%
- **Mode Night (1)** : Smart dimming désactivé, intensité fixe 20-30%
- **Mode Away (2)** : Smart dimming désactivé, lampes éteintes

## API Documentation

Une fois le serveur lancé :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **OpenAPI JSON** : http://localhost:8000/openapi.json

## Endpoints Principaux

### Authentification

- `POST /api/auth/register` - Création de compte utilisateur
- `POST /api/auth/login` - Authentification (retourne JWT)
- `GET /api/auth/me` - Informations utilisateur actuel (requiert JWT)

### Appareils

- `GET /api/devices` - Liste des appareils (filtres: location, type)
- `GET /api/devices/{id}` - Détails d'un appareil
- `POST /api/devices` - Créer un appareil
- `PUT /api/devices/{id}/state` - Changer état (ON/OFF)
- `PUT /api/devices/{id}/brightness` - Ajuster intensité (0-100%)
- `DELETE /api/devices/{id}` - Supprimer un appareil

### Raspberry Pi

- `GET /api/raspberry-pis` - Liste des Raspberry Pi
- `POST /api/raspberry-pis` - Enregistrer un Raspberry Pi
- `GET /api/raspberry-pis/{id}` - Détails d'un Raspberry Pi
- `PUT /api/raspberry-pis/{id}` - Mettre à jour un Raspberry Pi

### Présence

- `POST /api/presence` - Enregistrer une détection (appelé par RPi)
- `GET /api/presence` - Historique des détections

### Mesures de Luminosité

- `POST /api/light-readings` - Enregistrer une mesure (appelé par RPi)
- `GET /api/light-readings` - Historique des mesures

### Règles d'Automatisation

- `GET /api/rules` - Liste des règles (filtre optionnel: `enabled`)
- `GET /api/rules/{id}` - Détails d'une règle
- `POST /api/rules` - Créer une règle (avec validation condition/action)
- `PUT /api/rules/{id}` - Modifier une règle
- `DELETE /api/rules/{id}` - Supprimer une règle
- `POST /api/rules/{id}/test` - Évaluer une règle manuellement

### Intelligence Artificielle

- `GET /api/ai/current-scenario` - Scénario actuel détecté (avec option `raspberry_pi_id`)
- `POST /api/ai/classify` - Classification manuelle avec paramètres spécifiques
- `GET /api/ai/model-metrics` - Métriques du modèle (accuracy, état du modèle, features, scénarios)

### Smart Dimming

- `GET /api/smart-dimming/status` - État global du smart dimming (statistiques, ajustements aujourd'hui)
- `PUT /api/smart-dimming/enable` - Activer/désactiver globalement (body: `{"enabled": true/false}`)
- `PUT /api/smart-dimming/pause/{device_id}` - Pause temporaire pour un appareil (30 minutes)
- `GET /api/smart-dimming/adjustments` - Historique des ajustements (filtre optionnel: `device_id`, `limit`)

### Événements

- `GET /api/events` - Historique des événements système
- `GET /api/events/device/{id}` - Événements d'un appareil spécifique

## Intelligence Artificielle

### Classification de Scénarios (Implémenté)

**Algorithme** : Decision Tree Classifier (scikit-learn)

**Features utilisées :**
- `hour` : Heure actuelle (0-23)
- `day_of_week` : Jour de la semaine (0=Lundi, 6=Dimanche)
- `presence_detected` : Présence détectée dans les 5 dernières minutes (booléen)
- `light_on` : Au moins une lampe allumée (booléen)
- `ambient_light_level` : Niveau de luminosité ambiante (0-100) - **Amélioration future**
- `temperature` : Température ambiante en °C - **Amélioration future**
- `last_motion_time` : Minutes depuis dernière détection - **Amélioration future**

**Scénarios détectés :**
- **Day (0)** : Journée normale, lumière naturelle suffisante
- **Night (1)** : Période nocturne, éclairage minimal
- **Away (2)** : Absence prolongée, économie d'énergie
- **Evening (3)** : Soirée détente, ambiance lumineuse

**Performance cible :**
- Accuracy minimale : **75%**
- Temps d'inférence : < 100ms
- Rafraîchissement : toutes les 2 minutes

**Entraînement :**
```bash
# Générer données synthétiques
python ml/generate_data.py --samples 1000

# Entraîner le modèle
python ml/train_model.py --max-depth 7

# Le modèle sera sauvegardé dans ml/models/scenario_classifier.pkl
# Les métriques peuvent être sauvegardées dans ml/models/metrics.json (optionnel)
```

**Métriques du modèle :**
L'endpoint `GET /api/ai/model-metrics` retourne :
- État du modèle (chargé ou non)
- Chemin du modèle
- Accuracy (si disponible depuis `ml/models/metrics.json`)
- Méthode utilisée (ML ou fallback)
- Nombre de features (4)
- Liste des scénarios détectables

### Régression pour Prédiction d'Intensité (À implémenter)

**Algorithme prévu** : Random Forest Regressor

**Objectif** : Prédire l'intensité lumineuse optimale (0-100%) selon :
- Luminosité ambiante (lux)
- Heure et jour de la semaine
- Préférences historiques utilisateur
- Type de pièce
- Scénario actif

**Performance cible :**
- R² score : > 0.80
- MAE : < 10%

### Clustering des Habitudes (À implémenter)

**Algorithme prévu** : K-Means Clustering

**Objectif** : Détecter automatiquement les profils utilisateur :
- **Early Bird** : Lever tôt, coucher tôt
- **Night Owl** : Lever tard, coucher tard
- **Regular** : Horaires réguliers
- **Minimal** : Utilisation minimale

## Smart Dimming

Le **Smart Dimming** est la fonctionnalité d'adaptation dynamique de l'intensité lumineuse en fonction de la luminosité naturelle mesurée en temps réel.

### Principe de Fonctionnement

1. **Mesure** : Le capteur de luminosité (BH1750 ou LDR) envoie des mesures toutes les 10 secondes
2. **Classification** : Le service IA détermine le scénario actif (Day, Evening, Night, Away)
3. **Calcul** : L'algorithme calcule l'intensité cible selon :
   - Luminosité ambiante mesurée (lux)
   - Paramètres du scénario (seuils haut/bas)
   - Interpolation linéaire entre les seuils
4. **Application** : Si l'écart avec l'intensité actuelle > 10%, envoi d'une commande au Raspberry Pi
5. **Enregistrement** : L'ajustement est enregistré dans `dimming_adjustments` avec justification

### Algorithme d'Ajustement

**Mode Day :**
- Luminosité > 500 lux → intensité cible 20%
- Luminosité < 200 lux → intensité cible 70%
- Interpolation linéaire entre les deux
- Transition : immédiate

**Mode Evening :**
- Luminosité > 200 lux → intensité cible 30%
- Luminosité < 50 lux → intensité cible 75%
- Interpolation douce
- Transition : fade progressif (2 secondes)

**Mode Night :**
- Smart dimming désactivé par défaut
- Intensité fixe 20-30% pour confort nocturne

**Mode Away :**
- Smart dimming désactivé
- Lampes éteintes

### Protection contre Oscillations

Si l'utilisateur ajuste manuellement une lampe dans les 2 minutes suivant un smart dimming :
- Enregistrement de la préférence dans `user_preferences`
- Pause temporaire du smart dimming pour cette lampe (30 minutes) via `PUT /api/smart-dimming/pause/{device_id}`
- Notification affichée dans l'application mobile

**Pause manuelle :**
L'endpoint `PUT /api/smart-dimming/pause/{device_id}` permet de mettre en pause le smart dimming pour un appareil spécifique pendant 30 minutes. Utile si l'utilisateur veut garder un contrôle manuel temporaire.

## Moteur de Règles

Le moteur de règles permet de définir des automatisations IF-THEN déterministes.

### Conditions Disponibles

- **Détection de présence** : Booléen + localisation (pièce)
- **Plage horaire** : Format 24h (ex: 18:00-23:00)
- **Jour de la semaine** : Lundi à dimanche
- **État d'un appareil** : ON/OFF d'un appareil spécifique
- **Niveau de luminosité** : Seuil en lux ou pourcentage

### Actions Disponibles

- Allumer ou éteindre un appareil
- Définir une intensité lumineuse spécifique
- Activer/désactiver le mode smart dimming

### Format JSON des Règles

Les règles sont stockées en base de données au format JSONB :

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

### Exécution

Les règles sont évaluées automatiquement lors de :
- Détection de présence (via `POST /api/presence`)
- Changement d'état d'appareil
- Réception d'une mesure de luminosité
- Déclenchement manuel via `POST /api/rules/{id}/test`

**Évaluation manuelle d'une règle :**
L'endpoint `POST /api/rules/{id}/test` permet de :
- Évaluer les conditions de la règle dans le contexte actuel
- Exécuter l'action si les conditions sont satisfaites
- Retourner le résultat (condition satisfaite, action exécutée, erreurs éventuelles)

## Base de Données

### Schéma Principal

**Tables relationnelles :**
- `users` : Utilisateurs du système
- `raspberry_pis` : Inventaire des Raspberry Pi
- `devices` : Appareils connectés (lampes, prises)
- `presence` : Historique des détections de mouvement
- `light_readings` : Mesures de luminosité (time-series)
- `rules` : Règles d'automatisation (format JSONB)
- `events` : Journal des événements système
- `smart_dimming_adjustments` : Historique des ajustements
- `training_data` : Données d'entraînement IA
- `user_preferences` : Préférences utilisateur (apprentissage)

Voir le fichier `../db/init_database.sql` pour le schéma complet et les données de test.

### TimescaleDB (Optionnel)

Pour optimiser les requêtes time-series sur `light_readings` :

```sql
-- Convertir la table en hypertable
SELECT create_hypertable('light_readings', 'measured_at');
```

## Communication avec Raspberry Pi

### Protocole

- **Protocole** : HTTP/REST
- **Format** : JSON
- **Authentification** : API Key (header `X-API-Key`)
- **Port** : 5000 (Flask API locale sur RPi)

### Commandes Envoyées

Le backend envoie des commandes HTTP POST au Raspberry Pi :

```python
# Exemple : Changer l'intensité d'une lampe
POST http://<rpi_ip>:5000/api/devices/1/brightness
Headers: X-API-Key: <api_key>
Body: {"brightness": 75}
```

### Événements Reçus

Le Raspberry Pi envoie des événements au backend :

- `POST /api/presence` : Détection de présence
- `POST /api/light-readings` : Mesure de luminosité
- Heartbeat périodique (optionnel)

## Sécurité

### Authentification JWT

- **Algorithme** : HS256 (HMAC SHA-256)
- **Durée de validité** : 24 heures
- **Payload** : `user_id`, `username`, `exp`, `iat`
- **Stockage mobile** : DataStore Preferences (Android)

### API Key pour Raspberry Pi

- **Longueur** : 64 caractères hexadécimaux
- **Génération** : Cryptographiquement sécurisée (`secrets.token_hex`)
- **Header** : `X-API-Key`
- **Validation** : Vérification à chaque requête

### Hachage des Mots de Passe

- **Algorithme** : bcrypt
- **Cost factor** : 12 rounds minimum
- **Salt** : Généré automatiquement

### Validation des Entrées

- **Pydantic** : Validation stricte des schémas
- **SQLAlchemy ORM** : Protection contre injections SQL
- **Plages de valeurs** : Validation des paramètres (ex: brightness 0-100)

## Déploiement

### Développement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Avec Gunicorn (recommandé)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Service systemd (Linux)

Créer `/etc/systemd/system/smarthome-backend.service` :

```ini
[Unit]
Description=SmartHome Lite Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=smarthome
WorkingDirectory=/opt/smarthome/backend
Environment="PATH=/opt/smarthome/backend/venv/bin"
ExecStart=/opt/smarthome/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Dépannage

### Problèmes Courants

**Erreur de connexion à la base de données :**
- Vérifier que PostgreSQL est démarré
- Vérifier les credentials dans `.env`
- Vérifier que la base `smarthome` existe

**Modèle IA non trouvé :**
- Exécuter `python ml/generate_data.py --samples 1000`
- Exécuter `python ml/train_model.py`
- Vérifier que `ml/models/scenario_classifier.pkl` existe

**Erreur CORS :**
- Ajouter l'origine dans `CORS_ORIGINS` dans `.env`
- Vérifier que le frontend utilise la bonne URL

**Raspberry Pi non accessible :**
- Vérifier que le RPi est en ligne (`is_online = True`)
- Vérifier la connectivité réseau
- Vérifier l'API Key dans les headers

## Contribution

Ce projet est développé dans le cadre d'un projet académique (SAE BUT3 FA 2025).

Pour contribuer :
1. Créer une branche feature
2. Implémenter les modifications
3. Vérifier localement
4. Créer une pull request

## Licence

Projet académique - SAE BUT3 FA 2025
