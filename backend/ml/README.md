# Intelligence Artificielle – Backend SmartHome Lite

Ce document décrit **comment fonctionne l’IA** du backend, **où elle est utilisée**, et **comment la mettre en place et la tester**.

---

## Conformité au cahier des charges (SAE BUT3 FA 2025)

Le sujet impose :

- *« Le projet devra intégrer **au moins un** algorithme d'IA permettant d'effectuer une **régression ou une classification**. »*
- *« Un accès au serveur **Ollama** de l'IUT pourra être accordé pour les traitements d'intelligence artificielle. »*

Notre implémentation :

| Exigence | Réponse |
|----------|---------|
| Au moins 1 algorithme (régression **ou** classification) | **Classification** (Decision Tree, scénarios Day/Night/Away/Evening) et **Régression** (Random Forest, intensité lumineuse). Les deux sont utilisés en production (smart dimming, scénario actuel). |
| Ollama (IUT) | **Optionnel** : service `ollama_service.py` et routes `/api/ai/ollama/*`. Configurer `OLLAMA_BASE_URL` (ex. `http://ollama.iut.local:11434`) pour activer descriptions, parsing de règles, recommandations. |

Pour la soutenance, on peut mettre en avant **un** algorithme (ex. la régression pour l'intensité lumineuse) et mentionner la classification comme second algorithme ; ou inversement. Les fallbacks (règles horaires / formules fixes) permettent de faire tourner l'API sans modèles entraînés.

---

## Vue d’ensemble

L’IA du backend comporte **trois parties** :

| Composant | Rôle | Fichiers / Services | État actuel |
|-----------|------|---------------------|-------------|
| **Classification de scénarios** | Détecter le contexte (Day / Night / Away / Evening) | `ml/generate_data.py`, `ml/train_model.py`, `app/services/ai_service.py` | Implémenté, **modèle non entraîné** (pas de `.pkl`) |
| **Régression (prédiction d’intensité)** | Prédire l’intensité lumineuse optimale (0–100 %) | `ml/generate_regression_data.py`, `ml/train_regression_model.py`, `app/services/regression_service.py` | Implémenté, **modèle non entraîné** (pas de `.joblib`) |
| **Ollama (IA générative)** | Descriptions, parsing de règles, recommandations | `app/services/ollama_service.py` | Optionnel, config `OLLAMA_BASE_URL` |

Sans modèles entraînés, l’API fonctionne quand même : elle utilise des **fallbacks** (règles basées sur l’heure et le scénario).

---

## 1. Classification de scénarios (Decision Tree)

### Principe

- **Entrée** : `hour`, `day_of_week`, `presence_detected`, `light_on`.
- **Sortie** : scénario parmi **Day (0), Night (1), Away (2), Evening (3)**.

### Où c’est utilisé

- **`GET /api/ai/current-scenario`** : scénario actuel (contexte DB : présence, lampes).
- **`POST /api/ai/classify`** : classification manuelle avec paramètres fournis.
- **Smart Dimming** : choix des seuils lux / intensité selon le scénario.
- **Moteur de règles** : contexte pour l’évaluation des règles.
- **Health** : `GET /health` indique `ai_service: "loaded"` ou `"fallback"`.

### Données d’entraînement

- Stockées en base dans la table **`training_data`** (colonnes : `hour`, `day_of_week`, `presence_detected`, `light_on`, `scenario`).
- Générées par **`ml/generate_data.py`** (données synthétiques). **Nécessite une base PostgreSQL accessible.**

### Modèle

- **Algorithme** : Decision Tree Classifier (scikit-learn).
- **Fichier** : `ml/models/scenario_classifier.pkl` (chemin configurable via `ML_MODEL_PATH` dans `.env`).
- **Chargement** : au démarrage de l’API, dans `app/services/ai_service.py` (singleton). Si le fichier est absent → mode **fallback** (règles horaires).

---

## 2. Régression (prédiction d’intensité)

### Principe

- **Entrée** : `hour`, `day_of_week`, `lux_value`, `presence_detected`, `scenario`.
- **Sortie** : intensité lumineuse optimale **0–100 %**.

### Où est ce utilisé

- **`POST /api/ai/predict-intensity`** : prédiction manuelle.
- **Smart Dimming** : dans `smart_dimming_service.py`, si le modèle de régression est chargé, il est utilisé pour calculer l’intensité cible ; sinon utilisation des règles fixes (seuils lux → intensité).
- **Health** : `GET /health` indique `regression_service: "loaded"` ou `"fallback"`.

### Données d’entraînement

- **Pas de base de données** : stockées dans **`ml/data/regression_training_data.json`**.
- Générées par **`ml/generate_regression_data.py`** (données synthétiques).

### Modèle

- **Algorithme** : Random Forest Regressor (scikit-learn).
- **Fichier** : `ml/models/regression_model.joblib` (chemin fixe relatif à `app/services/regression_service.py`).
- **Chargement** : au premier appel au service de régression. Si le fichier est absent → **fallback** (formules fixes par scénario).

---

## 3. Ollama (IA générative)

- **Optionnel** : correspond au *« serveur Ollama de l'IUT »* mentionné dans le sujet. Nécessite `OLLAMA_BASE_URL` (ex. `http://ollama.iut.local:11434`).
- **Routes** : `/api/ai/ollama/generate`, `/api/ai/ollama/scenario-description`, `/api/ai/ollama/parse-rule`, `/api/ai/ollama/recommendations`.
- Hors périmètre « ML classique » (régression/classification) mais valorisable pour l’IA dans le projet.

---

## Mise en place et test

### Prérequis

- Python 3.10+, **environnement virtuel activé**, dépendances installées :
  ```bash
  cd backend
  python -m venv venv
  source venv/bin/activate   # Linux/Mac  |  sous Windows: .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- **Classification** : PostgreSQL accessible, table `training_data` créée (création auto au premier `generate_data.py` si `Base.metadata.create_all(engine)` est utilisé).
- **Régression** : aucun prérequis DB (fichier JSON uniquement).

Les commandes ci-dessous sont à exécuter **depuis la racine du backend** (`backend/`). Vous pouvez aussi utiliser le script **`ml/scripts/setup_and_test_ml.sh`** (à lancer depuis `backend/` : `./ml/scripts/setup_and_test_ml.sh`) qui enchaîne les quatre étapes. Le script définit `PYTHONPATH` pour que les scripts `ml/*.py` trouvent le module `app`.

### Étapes

Depuis le répertoire **`backend/`**, les scripts `ml/*.py` ont besoin que la racine du backend soit dans `PYTHONPATH` pour que `import app` fonctionne. Soit vous lancez le script `./ml/scripts/setup_and_test_ml.sh` (qui définit `PYTHONPATH`), soit vous faites :

```bash
cd backend
export PYTHONPATH="$PWD"   # ou sous Windows: set PYTHONPATH=%CD%
```

Puis :

1. **Générer les données de classification** (écrit en base)  
   ```bash
   python ml/generate_data.py --samples 1000
   ```

2. **Entraîner le modèle de classification**  
   ```bash
   python ml/train_model.py --max-depth 7
   ```  
   → Crée `ml/models/scenario_classifier.pkl`.

3. **Générer les données de régression** (fichier JSON)  
   ```bash
   python ml/generate_regression_data.py --samples 800
   ```  
   → Crée `ml/data/regression_training_data.json`.

4. **Entraîner le modèle de régression**  
   ```bash
   python ml/train_regression_model.py --n-estimators 100 --max-depth 10
   ```  
   → Crée `ml/models/regression_model.joblib`.

5. **Démarrer l’API et vérifier le health**  
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```  
   Puis : `GET http://localhost:8000/health`  
   - `ai_service: "loaded"` et `regression_service: "loaded"` si les modèles sont bien présents.

6. **Tester les endpoints IA** (avec un JWT valide)  
   - `GET /api/ai/current-scenario`  
   - `POST /api/ai/classify` avec body : `{"hour": 14, "day_of_week": 2, "presence_detected": true, "light_on": true}`  
   - `GET /api/ai/model-metrics`  
   - `POST /api/ai/predict-intensity` avec body : `{"hour": 20, "day_of_week": 2, "lux_value": 80, "presence_detected": true, "scenario": 3}`  

Un script **`ml/scripts/setup_and_test_ml.sh`** automatise les étapes 1–4 et peut appeler le health check pour vérification.

---

## Résumé des chemins

- **Classification** :  
  - Données : table `training_data` (PostgreSQL).  
  - Modèle : `ml/models/scenario_classifier.pkl` (ou valeur de `ML_MODEL_PATH`).
- **Régression** :  
  - Données : `ml/data/regression_training_data.json`.  
  - Modèle : `ml/models/regression_model.joblib`.

L’IA « marche » partout où ces services sont appelés (routes `/api/ai/*`, smart dimming, moteur de règles, health). Sans modèles entraînés, le comportement reste cohérent grâce aux fallbacks.

---

## Comment cea doit fonctionner (use cases, user stories)

### Structure des dossiers

```
backend/
├── app/                    # API FastAPI
│   ├── routes/ai.py        # Endpoints /api/ai/*
│   ├── services/
│   │   ├── ai_service.py       # Classification (scénario)
│   │   ├── regression_service.py  # Prédiction intensité
│   │   ├── smart_dimming_service.py # Utilise les deux
│   │   └── ...
│   └── config.py           # ML_MODEL_PATH, etc.
├── ml/                     # Données et entraînement (hors API)
│   ├── generate_data.py       # → table training_data (classification)
│   ├── train_model.py         # → ml/models/scenario_classifier.pkl
│   ├── generate_regression_data.py  # → ml/data/regression_training_data.json
│   ├── train_regression_model.py    # → ml/models/regression_model.joblib
│   ├── data/
│   ├── models/             # Fichiers produits (pkl, joblib)
│   └── scripts/
│       └── setup_and_test_ml.sh   # Mise en place + test
└── ...
```

Les scripts dans `ml/` sont exécutés **depuis la racine `backend/`** avec **`PYTHONPATH=backend`** pour que `import app` fonctionne (config, modèles ORM). L’API, elle, tourne depuis `backend/` avec `uvicorn app.main:app` et charge les modèles depuis `ml/models/` (chemins relatifs au CWD).

### Use cases (cas d’usage)

| Use case | Acteur | Objectif | Rôle de l’IA |
|----------|--------|----------|----------------|
| **Adapter la lumière à la luminosité** | Système (Smart Dimming) | Ajuster l’intensité des lampes selon la luminosité ambiante (capteur) | Classification → scénario (Day/Evening/…) ; Régression → intensité cible (ou règles fixes en fallback). |
| **Consulter le scénario actuel** | Utilisateur (web/mobile) | Voir si le système est en mode Jour, Soirée, Nuit, Absence | `GET /api/ai/current-scenario` utilise le classifieur (ou fallback horaire). |
| **Tester une prédiction d’intensité** | Admin / Dev | Vérifier la prédiction pour une heure/lux/scénario donnés | `POST /api/ai/predict-intensity` utilise le modèle de régression (ou fallback). |
| **Évaluer les règles d’automatisation** | Moteur de règles | Décider si une règle doit s’exécuter (ex. « si soirée et présence ») | Contexte scénario fourni par le service de classification. |
| **Vérifier l’état de l’IA** | Admin / Monitoring | Savoir si les modèles sont chargés ou en fallback | `GET /health` (ai_service, regression_service) et `GET /api/ai/model-metrics`. |

### User stories (résumées)

1. **En tant qu’utilisateur**, je veux que la lumière s’adapte toute seule à la luminosité du jour et du soir, **pour** ne pas avoir à régler manuellement.  
   → Smart Dimming utilise classification + régression (ou fallback).

2. **En tant qu’utilisateur**, je veux voir sur l’app le « mode » actuel (jour / soirée / nuit / absence), **pour** comprendre le comportement du système.  
   → `GET /api/ai/current-scenario`.

3. **En tant qu’admin**, je veux (ré)entraîner les modèles et vérifier qu’ils sont bien chargés, **pour** activer l’IA en conditions réelles.  
   → Script `ml/scripts/setup_and_test_ml.sh` + `GET /health` et `GET /api/ai/model-metrics`.

4. **En tant que développeur**, je veux appeler la classification ou la prédiction d’intensité avec des paramètres précis, **pour** tester ou intégrer dans un outil.  
   → `POST /api/ai/classify` et `POST /api/ai/predict-intensity`.

### Enchaînement typique (flux)

1. **Une fois (mise en place)** : depuis `backend/`, lancer `./ml/scripts/setup_and_test_ml.sh` (avec venv activé et PostgreSQL pour la classification).  
   → Génère les données, entraîne les deux modèles, écrit dans `ml/models/` et `ml/data/`.

2. **Au démarrage de l’API** : `uvicorn app.main:app` (depuis `backend/`).  
   → Chargement de `scenario_classifier.pkl` et, au premier appel, de `regression_model.joblib`. Si absents → fallback.

3. **En temps réel** : le RPi envoie des mesures de luminosité → `POST /api/light-readings`.  
   → Smart Dimming appelle le scénario (classification) puis la prédiction d’intensité (régression ou règles), puis envoie la commande au RPi pour ajuster la lampe.
