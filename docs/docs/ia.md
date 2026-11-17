# Module IA (classification et régression)

Le service de **classification** (`ai_service.py`) utilise un **arbre de décision** (scikit-learn) chargé depuis `scenario_classifier.pkl` pour prédire le scénario (0 Jour, 1 Nuit, 2 Absence, 3 Soirée) à partir de l’heure, du jour de la semaine, de la présence et de l’état des lumières. Ce modèle est chargé au démarrage dans le lifespan de `main.py` et est utilisé par le smart dimming et les règles qui dépendent du scénario. Le service de **régression** (`regression_service.py`) utilise un **Random Forest** (`regression_model.joblib`) pour prédire une intensité (0–99 %) à partir des entrées (heure, lux, etc.) ; il est également chargé au démarrage et peut être intégré au calcul d’intensité du smart dimming. **Ollama** est optionnel (serveur de l’IUT) pour des fonctionnalités texte ou descriptions. Les jeux de données d’entraînement sont générés par les scripts du dossier `ml/` (generate_data, etc.) et les modèles sont entraînés avec `train_model.py` et `train_regression_model.py`. L’endpoint `GET /health` indique si les modèles IA sont chargés ou si le système est en mode fallback.

## Commandes (depuis `backend/` avec venv activé)

```bash
export PYTHONPATH="$PWD"
# classification → table training_data
python ml/generate_data.py --samples 1000
# → ml/models/scenario_classifier.pkl
python ml/train_model.py --max-depth 7
# → ml/data/regression_training_data.json
python ml/generate_regression_data.py --samples 800
# → ml/models/regression_model.joblib
python ml/train_regression_model.py --n-estimators 100 --max-depth 10
```

**Test API** (JWT requis) : `GET /api/ai/current-scenario`, `POST /api/ai/classify`, `GET /api/ai/model-metrics`, `POST /api/ai/predict-intensity`. Script : `ml/scripts/test_ai_api.sh`.
