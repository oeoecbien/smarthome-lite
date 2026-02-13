# IA – Classification & régression

- **Classification** : scénario Day/Night/Away/Evening (Decision Tree). Fichier `scenario_classifier.pkl`.
- **Régression** : intensité lumineuse 0–99 % (Random Forest). Fichier `regression_model.joblib`.
- **Ollama** : optionnel, `OLLAMA_BASE_URL` en .env. Génération texte, descriptions, recommandations.
- Sans modèles → fallback (règles horaires / formules fixes). Vérifier : `GET /health` → `ai_service`, `regression_service`.

Depuis `backend/` avec venv activé :

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

Test API (JWT requis) : `GET /api/ai/current-scenario`, `POST /api/ai/classify`, `GET /api/ai/model-metrics`, `POST /api/ai/predict-intensity`. Script : `ml/scripts/test_ai_api.sh`.
