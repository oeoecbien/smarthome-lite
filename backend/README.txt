# SmartHome Lite API - Documentation

## Description

SmartHome Lite est une API REST développée avec FastAPI pour la gestion d'un système domotique intelligent. L'application permet de contrôler des dispositifs connectés, gérer des règles d'automatisation, ajuster intelligemment l'éclairage (Smart Dimming) et interagir avec des Raspberry Pi.

## Fonctionnalités principales

- **Authentification sécurisée** : JWT avec tokens d'accès
- **Gestion de dispositifs** : Contrôle et suivi des appareils connectés
- **Moteur de règles** : Automatisation basée sur des conditions
- **Smart Dimming** : Ajustement intelligent de l'éclairage selon la luminosité ambiante
- **Intelligence Artificielle** : Classification de scénarios (Day, Night, Away, Evening)
- **Intégration Raspberry Pi** : Communication avec des dispositifs Raspberry Pi
- **Gestion d'événements** : Historique et suivi des événements système
- **Préférences utilisateur** : Personnalisation des paramètres

## Structure du projet

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── config.py                  # Configuration centralisée
│   ├── database.py                # Connexion et initialisation BDD
│   ├── dependencies.py            # Dépendances FastAPI
│   ├── models/                    # Modèles SQLAlchemy (ORM)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── raspberry_pi.py
│   │   ├── device.py
│   │   ├── presence.py
│   │   ├── light_reading.py
│   │   ├── event.py
│   │   ├── rule.py
│   │   ├── training_data.py
│   │   ├── smart_dimming_adjustment.py
│   │   └── user_preference.py
│   ├── schemas/                   # Schémas Pydantic (validation)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── device.py
│   │   ├── rule.py
│   │   ├── smart_dimming.py
│   │   ├── event.py
│   │   └── raspberry_pi.py
│   ├── routes/                    # Routes API (endpoints)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── devices.py
│   │   ├── events.py
│   │   ├── rules.py
│   │   ├── ai.py
│   │   ├── smart_dimming.py
│   │   └── raspberry_pis.py
│   ├── services/                  # Logique métier
│   │   ├── __init__.py
│   │   ├── device_service.py
│   │   ├── rule_engine.py
│   │   ├── ai_service.py
│   │   └── smart_dimming_service.py
│   └── utils/                     # Utilitaires
│       ├── __init__.py
│       ├── auth.py
│       └── validators.py
├── ml/                            # Machine Learning
│   ├── __init__.py
│   ├── train_model.py
│   ├── generate_data.py
│   └── models/
│       └── .gitkeep
├── requirements.txt               # Dépendances Python
├── .env.example                   # Exemple de fichier de configuration
└── README.md                      # Documentation principale
```

## Installation

### Prérequis

- Python 3.10 ou supérieur
- PostgreSQL 12 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner le dépôt** (si applicable)
   ```bash
   git clone <url-du-depot>
   cd backend
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   ```

3. **Activer l'environnement virtuel**
   
   Sur Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   Sur Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

4. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configurer les variables d'environnement**
   
   Créer un fichier `.env` à la racine du dossier `backend/` :
   ```env
   # Base de données
   DATABASE_HOST=10.109.150.75
   DATABASE_PORT=5432
   DATABASE_NAME=smarthome
   DATABASE_USER=postgres
   DATABASE_PASSWORD=smarthome2025
   
   # JWT
   SECRET_KEY=votre_cle_secrete_aleatoire_32_caracteres_minimum
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   
   # Serveur
   API_HOST=0.0.0.0
   API_PORT=8000
   DEBUG=True
   ENVIRONMENT=development
   
   # CORS
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   CORS_ALLOW_CREDENTIALS=True
   
   # Raspberry Pi
   RASPBERRY_PI_PROTOCOL=http
   RASPBERRY_PI_PORT=5000
   RASPBERRY_PI_TIMEOUT=5
   
   # Machine Learning
   ML_MODEL_PATH=ml/models/scenario_classifier.pkl
   ML_RETRAIN_THRESHOLD=100
   
   # Smart Dimming
   SMART_DIMMING_ENABLED=True
   SMART_DIMMING_THRESHOLD=10
   
   # Logs
   LOG_LEVEL=INFO
   ```

6. **Initialiser la base de données**
   
   L'application initialise automatiquement le schéma au démarrage. Assurez-vous que PostgreSQL est démarré et accessible.

## Démarrage

### Mode développement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Mode production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

L'API sera accessible sur :
- **API** : http://localhost:8000
- **Documentation interactive** : http://localhost:8000/docs
- **Documentation ReDoc** : http://localhost:8000/redoc

## Endpoints principaux

### Authentification
- `POST /api/auth/register` - Inscription d'un nouvel utilisateur
- `POST /api/auth/login` - Connexion et obtention d'un token JWT
- `GET /api/auth/me` - Informations sur l'utilisateur connecté

### Dispositifs
- `GET /api/devices` - Liste des dispositifs
- `POST /api/devices` - Créer un dispositif
- `GET /api/devices/{id}` - Détails d'un dispositif
- `PUT /api/devices/{id}` - Mettre à jour un dispositif
- `DELETE /api/devices/{id}` - Supprimer un dispositif

### Règles
- `GET /api/rules` - Liste des règles
- `POST /api/rules` - Créer une règle
- `PUT /api/rules/{id}` - Mettre à jour une règle
- `DELETE /api/rules/{id}` - Supprimer une règle

### Smart Dimming
- `GET /api/smart-dimming/status` - Statut du Smart Dimming
- `POST /api/smart-dimming/adjust` - Ajuster l'éclairage
- `GET /api/smart-dimming/history` - Historique des ajustements

### Intelligence Artificielle
- `POST /api/ai/predict` - Prédire un scénario
- `POST /api/ai/train` - Entraîner le modèle

### Raspberry Pi
- `GET /api/raspberry-pis` - Liste des Raspberry Pi
- `POST /api/raspberry-pis` - Enregistrer un Raspberry Pi
- `GET /api/raspberry-pis/{id}/status` - Statut d'un Raspberry Pi

### Santé
- `GET /health` - Vérification de santé de l'API
- `GET /` - Informations sur l'API

## Configuration

La configuration est centralisée dans `app/config.py` et peut être surchargée via des variables d'environnement dans le fichier `.env`.

### Paramètres importants

- **DATABASE_URL** : URL de connexion PostgreSQL complète
- **SECRET_KEY** : Clé secrète pour JWT (minimum 32 caractères en production)
- **DEBUG** : Mode debug (désactivé en production)
- **CORS_ORIGINS** : Origines autorisées pour CORS

## Logs

Les logs sont configurés via les paramètres `LOG_LEVEL` et `LOG_FORMAT`. Par défaut, les logs sont affichés dans la console avec le format :
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Sécurité

- **JWT** : Authentification basée sur des tokens JWT
- **CORS** : Configuration des origines autorisées
- **Validation** : Validation des données avec Pydantic
- **Hachage de mots de passe** : Utilisation de bcrypt via passlib

## Machine Learning

Le système inclut un modèle de classification de scénarios qui peut être entraîné avec des données historiques. Le modèle est sauvegardé dans `ml/models/scenario_classifier.pkl`.

### Entraînement du modèle

```bash
python ml/train_model.py
```

## Technologies utilisées

- **FastAPI** : Framework web moderne et rapide
- **SQLAlchemy** : ORM pour PostgreSQL
- **Pydantic** : Validation de données
- **JWT** : Authentification par tokens
- **scikit-learn** : Machine Learning
- **Uvicorn** : Serveur ASGI

## Dépannage

### Problème de connexion à la base de données

Vérifiez que :
- PostgreSQL est démarré
- Les identifiants dans `.env` sont corrects
- Le port PostgreSQL (5432) est accessible

### Erreur de module manquant

Réinstallez les dépendances :
```bash
pip install -r requirements.txt
```