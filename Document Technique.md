# SmartHome Lite - Documentation Technique

## 1. Contexte et Objectifs

### 1.1 Contexte du Projet

**Cadre académique :** Projet de développement distribué et embarqué - SAE BUT3 FA 2025

**Problématique :** Développement d'un système de gestion intelligente d'éclairage et d'appareils électriques pour l'habitat, avec détection de présence et automatisation basée sur l'intelligence artificielle.

### 1.2 Contraintes du Projet

- **Durée :** 50 heures
- **Équipe :** 4 étudiants
- **Matériel disponible :** 
  - Un Raspberry Pi par étudiant
  - Actionneurs : ampoules dimmables, prises connectées
  - Capteurs PIR pour détection de présence

### 1.3 Objectifs Prioritaires

1. Développement d'un **service distribué** déployé sur serveur
2. Intégration d'au moins un **Raspberry Pi** dans l'architecture
3. Hébergement d'une **base de données** sur le système
4. Développement d'une **application mobile** (Kotlin + Jetpack Compose)
5. Intégration d'un **algorithme d'IA** pour classification de scénarios
6. Contrôle à distance des appareils électriques
7. Détection automatique de présence
8. Automatisation intelligente par règles

---

## 2. Architecture Globale

### 2.1 Vue d'Ensemble

Le système SmartHome Lite est organisé en **trois couches principales** :

**Couche IoT (Raspberry Pi)**
- Gestion des capteurs PIR et actionneurs physiques
- API locale Flask pour contrôle des GPIO
- Communication avec le serveur central

**Couche Métier (Serveur Backend)**
- API REST avec FastAPI (Python)
- Logique métier centralisée
- Moteur de règles d'automatisation
- Service d'intelligence artificielle
- Base de données PostgreSQL

**Couche Présentation (Application Mobile)**
- Interface utilisateur Android
- Kotlin + Jetpack Compose
- Communication HTTP/REST avec le backend

### 2.2 Schéma d'Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  APPLICATION MOBILE                     │
│              (Kotlin + Jetpack Compose)                 │
│         Contrôle • Visualisation • Automatisation       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST (JWT)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   SERVEUR BACKEND                       │
│                    (FastAPI + Python)                   │
│  • API REST                  • Moteur de règles         │
│  • Intelligence Artificielle • Gestion événements       │
│  • Base de données PostgreSQL                           │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST (API Key)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   RASPBERRY PI                          │
│                   (Flask + RPi.GPIO)                    │
│  • Capteur PIR (détection présence)                     │
│  • LED dimmable (PWM)                                   │
│  • Relais (prises connectées)                           │
└─────────────────────────────────────────────────────────┘
```

### 2.3 Configuration Matérielle Raspberry Pi

#### Capteur PIR HC-SR501
- **Fonction :** Détection de mouvement infrarouge
- **Portée :** 3 à 7 mètres
- **Angle :** 120 degrés
- **Branchement :**
  - Alimentation : 5V (Pin 2)
  - Masse : GND (Pin 6)
  - Signal : GPIO 4 (Pin 7)

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

### 3.1 Contrôle Manuel des Appareils

#### F1 : Gestion des Lampes
**Fonctionnalités :**
- Allumage et extinction individuels
- Ajustement de l'intensité lumineuse (slider 0-100%)
- Affichage en temps réel de l'état
- Temps de réponse garanti < 2 secondes

#### F2 : Gestion des Prises
**Fonctionnalités :**
- Activation et désactivation ON/OFF
- Affichage de l'état actuel (actif/inactif)
- Confirmation visuelle immédiate

#### F3 : Tableau de Bord Centralisé
**Fonctionnalités :**
- Vue d'ensemble de tous les appareils connectés
- Indicateurs visuels d'état (actif/inactif/erreur)
- Rafraîchissement automatique périodique
- Organisation par pièce

### 3.2 Détection de Présence

#### F4 : Système de Détection
**Fonctionnalités :**
- Détection en temps réel par capteur PIR
- Enregistrement horodaté des événements
- Filtrage anti-rebond (ignorer détections < 5 secondes)
- Association avec la localisation (pièce)

#### F5 : Historique de Présence
**Fonctionnalités :**
- Liste chronologique des dernières détections
- Filtrage par date et localisation
- Statistiques de base par appareil

### 3.3 Automatisation Intelligente

#### F6 : Moteur de Règles IF-THEN

**Conditions disponibles :**
- Détection de présence (booléen + localisation)
- Plage horaire (format 24h)
- Jour de la semaine (lundi à dimanche)
- État d'un appareil spécifique

**Actions disponibles :**
- Allumer ou éteindre un appareil
- Définir une intensité lumineuse spécifique
- Activer un scénario prédéfini

**Exemples de règles :**

1. **Règle présence soirée :**
   - Condition : Présence détectée dans le salon ET heure entre 18h et 23h
   - Action : Allumer lampe salon à 70%

2. **Règle économie d'énergie :**
   - Condition : Aucune présence pendant 10 minutes
   - Action : Éteindre toutes les lampes

#### F7 : Scénarios Prédéfinis

**Mode Jour (6h - 18h)**
- Désactivation automatique des lampes si absence
- Intensité maximale (100%) si allumage manuel

**Mode Soirée (18h - 23h)**
- Intensité modérée (60-80%) pour le confort
- Activation automatique sur détection de présence

**Mode Nuit (23h - 6h)**
- Intensité minimale (20-30%) pour les déplacements nocturnes
- Réduction du temps d'activation

**Mode Absence**
- Extinction de tous les appareils non essentiels
- Enregistrement des détections sans action automatique

### 3.4 Intelligence Artificielle

#### F8 : Classification de Scénarios

**Objectif :**
Classifier automatiquement le contexte d'utilisation en quatre scénarios distincts pour proposer des automatisations adaptées.

**Algorithme sélectionné :** Decision Tree Classifier (scikit-learn)

**Justification :**
- Simplicité d'implémentation
- Performance satisfaisante avec datasets réduits
- Temps d'entraînement rapide
- Interprétabilité des décisions

**Variables d'entrée (Features) :**

| Variable | Type | Plage | Description |
|----------|------|-------|-------------|
| hour | Entier | 0-23 | Heure actuelle de la journée |
| day_of_week | Entier | 0-6 | Jour de la semaine (0=Lundi) |
| presence_detected | Booléen | 0/1 | Mouvement détecté dans les 5 dernières minutes |
| light_on | Booléen | 0/1 | Au moins une lampe est allumée |

**Scénarios (Labels) :**

| Scénario | Valeur | Description |
|----------|--------|-------------|
| Day | 0 | Journée normale, lumière naturelle |
| Night | 1 | Période nocturne, éclairage minimal |
| Away | 2 | Absence prolongée, économie d'énergie |
| Evening | 3 | Soirée détente, ambiance |

**Objectif de performance :**
- Accuracy minimale : 70%
- Temps d'inférence : < 100 millisecondes

**Méthodologie :**
1. Génération de données synthétiques (500 échantillons minimum)
2. Division train/test : 80/20
3. Entraînement avec Decision Tree
4. Évaluation avec matrice de confusion
5. Sauvegarde du modèle (pickle)

### 3.5 Visualisation

#### F9 : Graphique de Présence

**Fonctionnalité :**
- Graphique des détections de présence sur les dernières 24 heures
- Intervalle : par heure
- Segmentation par pièce

---

## 4. Base de Données

### 4.1 Choix Technologique

**SGBD :** PostgreSQL 14+

**Justification :**
- Fiabilité éprouvée
- Support natif du type JSONB pour les règles flexibles
- Performance des requêtes
- Licence open source

### 4.2 Schéma de Données Simplifié

#### Table : users
Gestion des utilisateurs du système.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table : raspberry_pis
Inventaire des Raspberry Pi.

```sql
CREATE TABLE raspberry_pis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    ip_address VARCHAR(15) UNIQUE NOT NULL,
    location VARCHAR(100),
    is_online BOOLEAN DEFAULT FALSE,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table : devices
Référentiel des appareils connectés.

```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'light', 'outlet', 'sensor'
    raspberry_pi_id INTEGER REFERENCES raspberry_pis(id),
    gpio_pin INTEGER NOT NULL,
    state BOOLEAN DEFAULT FALSE,
    brightness INTEGER, -- 0-100, NULL pour outlets
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(raspberry_pi_id, gpio_pin)
);
```

#### Table : presence
Historique des détections de mouvement.

```sql
CREATE TABLE presence (
    id SERIAL PRIMARY KEY,
    raspberry_pi_id INTEGER REFERENCES raspberry_pis(id),
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### Table : events
Journal des événements système.

```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id),
    event_type VARCHAR(50) NOT NULL,
    value VARCHAR(100),
    source VARCHAR(20), -- 'manual', 'automatic', 'ai'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table : rules
Définition des règles d'automatisation.

```sql
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    condition JSONB NOT NULL,
    action JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table : training_data
Données d'entraînement pour l'algorithme d'IA.

```sql
CREATE TABLE training_data (
    id SERIAL PRIMARY KEY,
    hour INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    presence_detected BOOLEAN NOT NULL,
    light_on BOOLEAN NOT NULL,
    scenario INTEGER NOT NULL CHECK (scenario BETWEEN 0 AND 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 Relations entre Tables

```
raspberry_pis (1) ----< (N) devices
    |
    +-------< (N) presence
    
devices (1) ----< (N) events

users (standalone, authentification)
rules (standalone, références JSONB)
training_data (standalone, apprentissage automatique)
```

---

## 5. Technologies et Stack Technique

### 5.1 Backend (Serveur)

**Langage et framework :**
- Python 3.9+
- FastAPI 0.104+
- Uvicorn (serveur ASGI)

**Base de données :**
- SQLAlchemy 2.0+ (ORM)
- psycopg2-binary (driver PostgreSQL)

**Sécurité :**
- Pydantic (validation de données)
- python-jose (gestion JWT)
- passlib (hachage bcrypt)

**Intelligence artificielle :**
- scikit-learn 1.3+
- pandas 2.1+
- numpy 1.26+
- joblib (sérialisation de modèles)

**Structure du projet :**

```
backend/
├── app/
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── database.py             # Configuration SQLAlchemy
│   ├── models/                 # Modèles ORM
│   ├── schemas/                # Schémas Pydantic
│   ├── routes/                 # Endpoints API
│   │   ├── auth.py
│   │   ├── devices.py
│   │   ├── events.py
│   │   ├── rules.py
│   │   └── ai.py
│   └── services/               # Logique métier
│       ├── device_service.py
│       ├── rule_engine.py
│       └── ai_service.py
├── ml/                         # Module IA
│   ├── train_model.py
│   └── generate_data.py
├── requirements.txt
└── .env
```

### 5.2 Raspberry Pi (Contrôleur)

**Système d'exploitation :**
- Raspberry Pi OS Lite

**Framework web :**
- Flask 2.3+
- Flask-CORS 4.0+

**Contrôle GPIO :**
- RPi.GPIO 0.7+

**Structure du projet :**

```
raspberry-pi/
├── main.py                     # Point d'entrée principal
├── config.py                   # Configuration GPIO et URLs
├── sensors/
│   └── pir_sensor.py          # Capteur PIR
├── actuators/
│   ├── led_light.py           # Contrôle LED (PWM)
│   └── relay.py               # Contrôle relais
├── api/
│   └── local_api.py           # API Flask
├── services/
│   ├── server_client.py       # Client HTTP vers serveur
│   └── device_manager.py      # Gestionnaire d'appareils
└── requirements.txt
```

### 5.3 Application Mobile (Android)

**Langage :**
- Kotlin 1.9+

**UI :**
- Jetpack Compose (dernière version stable)
- Material Design 3

**Architecture :**
- Pattern MVVM
- StateFlow et Coroutines

**Réseau :**
- Retrofit 2.9+
- OkHttp 4.11+
- Gson

**Structure du projet :**

```
mobile/app/src/main/java/com/smarthome/
├── data/
│   ├── model/                  # Modèles de données
│   ├── remote/                 # Couche réseau (Retrofit)
│   └── repository/             # Pattern Repository
├── ui/
│   ├── screens/                # Écrans principaux
│   │   ├── DashboardScreen.kt
│   │   ├── DevicesScreen.kt
│   │   ├── RulesScreen.kt
│   │   └── HistoryScreen.kt
│   ├── components/             # Composants réutilisables
│   └── theme/                  # Thème Material 3
├── viewmodel/                  # ViewModels
└── MainActivity.kt
```

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
- Types : Heartbeat, événements de détection, changements d'état

### 6.2 Flux de Données : Allumage d'une Lampe

1. **Utilisateur** clique sur le bouton ON dans l'application mobile
2. **ViewModel** met à jour l'état local et appelle le Repository
3. **Repository** envoie une requête POST au backend via Retrofit
4. **Backend** valide le JWT et les paramètres
5. **Backend** envoie une requête HTTP POST au Raspberry Pi avec l'API Key
6. **Raspberry Pi** valide la clé API et configure le signal PWM sur le GPIO
7. **Lampe physique** s'allume à l'intensité demandée
8. **Raspberry Pi** retourne une confirmation
9. **Backend** enregistre l'événement dans la base de données
10. **Backend** retourne le nouvel état à l'application mobile
11. **UI mobile** se met à jour pour refléter le changement

**Temps total estimé :** < 2 secondes

### 6.3 Flux de Données : Détection de Présence avec Règle

1. **Capteur PIR** détecte un mouvement
2. **Module pir_sensor.py** lit le changement d'état GPIO
3. **Filtrage anti-rebond** vérifie qu'aucune détection récente (< 5s)
4. **EventReporter** envoie immédiatement un POST au backend
5. **Backend** enregistre la détection dans la table `presence`
6. **RuleEngine** est déclenché et évalue toutes les règles actives
7. Si une règle est satisfaite, **DeviceService** exécute l'action définie
8. **Backend** envoie la commande au Raspberry Pi concerné
9. **Appareil** change d'état selon l'action
10. **Backend** enregistre l'événement avec source 'automatic'

**Temps total estimé :** < 3 secondes

---

## 7. Sécurité

### 7.1 Authentification

**JWT (JSON Web Tokens) pour l'application mobile :**
- Algorithme : HS256 (HMAC SHA-256)
- Payload : user_id, username, exp (expiration), iat (émission)
- Durée de validité : 24 heures
- Stockage mobile : DataStore Preferences (Android)

**Cycle de vie :**
1. Utilisateur fournit username/password
2. Backend vérifie le hash bcrypt
3. Token JWT généré et retourné
4. Token stocké dans DataStore
5. Token envoyé dans header Authorization pour chaque requête
6. Backend valide signature et expiration

**API Key pour Raspberry Pi :**
- Longueur : 64 caractères hexadécimaux
- Génération : cryptographiquement sécurisée
- Unique par Raspberry Pi
- Header : X-API-Key
- Stockage : table `raspberry_pis`

### 7.2 Hachage des Mots de Passe

- Algorithme : bcrypt
- Cost factor : 12 rounds minimum
- Salt : généré automatiquement
- Stockage : hash uniquement, jamais en clair

### 7.3 Validation des Entrées

**Validation côté serveur (Pydantic) :**
- Type de données strict
- Plage de valeurs (ex: brightness 0-100)
- Format (ex: regex pour strings)
- Cohérence métier

**Protection contre injections :**
- Utilisation exclusive de requêtes préparées (SQLAlchemy ORM)
- Validation stricte des champs JSONB
- Échappement automatique dans les réponses JSON

---

## 8. Déploiement

### 8.1 Environnement de Déploiement

**Option retenue : Serveur IUT + Raspberry Pi local**

**Avantages :**
- Infrastructure fournie
- Pas de coûts d'hébergement
- Accès au serveur Ollama IUT (si besoin IA avancée)

**Prérequis serveur :**
- Python 3.9+
- PostgreSQL 14+
- Accès SSH
- Droits d'installation

**Prérequis Raspberry Pi :**
- Raspberry Pi OS Lite
- Connexion réseau (Ethernet recommandé)
- Carte SD de qualité

### 8.2 Installation Backend

**Étapes :**

1. **Clonage du repository**
```bash
git clone [URL_REPOSITORY]
cd smarthome-backend
```

2. **Création environnement virtuel**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Installation dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration variables d'environnement**
```bash
cp .env.example .env
# Éditer .env avec les valeurs appropriées
```

5. **Initialisation base de données**
```bash
# Créer la base PostgreSQL
createdb smarthome

# Exécuter les migrations
alembic upgrade head

# Générer données d'entraînement IA
python ml/generate_data.py
python ml/train_model.py
```

6. **Lancement du serveur**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 8.3 Installation Raspberry Pi

**Étapes :**

1. **Configuration système**
```bash
# Mise à jour
sudo apt update && sudo apt upgrade -y

# Installation Python et dépendances
sudo apt install python3-pip python3-venv git -y
```

2. **Clonage et installation**
```bash
git clone [URL_REPOSITORY]
cd smarthome-rpi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configuration**
```bash
cp config.example.py config.py
# Éditer config.py avec :
# - URL du serveur backend
# - API Key unique
# - Numéros de pins GPIO
```

4. **Test de connexion**
```bash
python main.py
# Vérifier les logs de connexion au serveur
```

5. **Lancement**
```bash
python main.py
```

### 8.4 Déploiement Application Mobile

**Build de l'APK :**

1. **Configuration**
   - Éditer `build.gradle.kts` avec l'URL du serveur
   - Versionner l'application

2. **Génération APK**
```bash
./gradlew assembleRelease
```

3. **Fichier généré**
   - Emplacement : `app/build/outputs/apk/release/app-release.apk`
   - Taille attendue : < 20 Mo

**Installation :**
1. Transférer l'APK sur le téléphone Android
2. Activer "Sources inconnues" dans les paramètres
3. Installer l'APK
4. Configurer l'URL du serveur (si non embarquée)
5. Se connecter avec les identifiants

---

## 9. Livrables

### 9.1 Code Source

**Repository Git incluant :**
- Code backend (FastAPI)
- Code Raspberry Pi (Flask + GPIO)
- Code application mobile (Kotlin + Compose)
- Scripts de migration base de données
- Scripts d'entraînement IA
- Fichiers de configuration d'exemple
- README.md détaillé

### 9.2 Documentation

**Documentation technique (ce document) :**
- Architecture système
- Schéma base de données
- Description des fonctionnalités
- Guide d'installation
- Stack technique

**Documentation API :**
- Swagger/OpenAPI auto-générée
- Accessible à `/docs` sur le serveur
- Liste complète des endpoints
- Exemples de requêtes

**Guide utilisateur :**
- Manuel d'utilisation de l'application mobile
- Captures d'écran annotées
- Tutoriels pour créer des règles
- FAQ

### 9.3 Application Mobile

**Package APK :**
- Version release signée
- Fichier d'information (version, date, taille)
- Instructions d'installation

### 9.4 Vidéo de Démonstration

**Durée : 2-3 minutes**

**Structure :**
1. Introduction (15s) : Présentation du projet et de l'équipe
2. Architecture (30s) : Schéma animé du système
3. Démonstration (90s) :
   - Tableau de bord
   - Contrôle manuel d'une lampe
   - Détection de présence et action automatique
   - Création d'une règle
   - Classification IA
4. Technologies (20s) : Stack technique et métriques
5. Conclusion (15s) : Bilan et perspectives

**Qualité technique :**
- Résolution : 1080p minimum
- Audio clair avec voix-off
- Sous-titres si nécessaire
- Montage fluide

---

## 10. Conformité SAE BUT3 FA 2025

### 10.1 Vérification des Contraintes Techniques

| Contrainte | Détails |
|------------|---------|
| Service distribué sur serveur | Backend FastAPI déployé sur serveur IUT |
| Au moins un Raspberry Pi | RPi avec Flask + GPIO pour contrôle IoT |
| Base de données hébergée | PostgreSQL sur serveur ou RPi |
| Actionneurs (optionnel) | Lampes dimmables + prises connectées |
| Application mobile | Kotlin + Jetpack Compose + Coroutines |
| Visualisation données | Tableau de bord + graphiques + historique |
| Interaction avec serveur | PI REST complète |
| Algorithme d'IA | Classification Decision Tree (4 scénarios) |

### 10.2 Accès au Serveur Ollama (Optionnel)

Si nécessaire pour des traitements IA avancés, l'accès au serveur Ollama de l'IUT peut être intégré pour :
- Génération de descriptions de règles en langage naturel
- Recommandations contextuelles avancées
- Analyse de patterns complexes

**Intégration simple via API REST du serveur Ollama.**

---

## 11. Conclusion

SmartHome Lite est un système de domotique intelligent complet respectant toutes les contraintes de la SAE BUT3 FA 2025. Le projet combine développement distribué, embarqué et mobile avec une intégration d'intelligence artificielle pour offrir une expérience utilisateur intuitive et automatisée.

**Points forts du projet :**
- Architecture claire et modulaire
- Respect strict des contraintes techniques
- Technologies modernes et adaptées
- Fonctionnalités concrètes et démonstrables
- Déploiement réaliste sur infrastructure disponible

**Perspectives d'amélioration :**
- Ajout de nouveaux types de capteurs
- Intégration vocale via Ollama
- Application web en complément du mobile
- Analyse prédictive avancée des habitudes