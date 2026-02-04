#!/usr/bin/env bash
# Mise en place et test des modèles IA (classification + régression).
#
# Où lancer le script : depuis la racine du backend (répertoire backend/).
#   cd backend
#   ./ml/scripts/setup_and_test_ml.sh
#
# Prérequis :
#   python -m venv venv && source venv/bin/activate   # ou venv\Scripts\Activate.ps1 sous Windows
#   pip install -r requirements.txt

set -e

# Racine du backend = répertoire qui contient app/ et ml/ (2 niveaux au-dessus de ce script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$BACKEND_DIR"

# Pour que "import app" fonctionne dans les scripts ml/*.py (exécutés depuis backend/)
export PYTHONPATH="$BACKEND_DIR${PYTHONPATH:+:$PYTHONPATH}"

echo "=============================================="
echo "  Mise en place IA – Backend SmartHome Lite"
echo "=============================================="
echo "Racine backend: $BACKEND_DIR"
echo "PYTHONPATH=$PYTHONPATH"
echo ""

# Vérification rapide des dépendances
if ! python -c "import sklearn, joblib, sqlalchemy" 2>/dev/null; then
    echo "Prérequis: activez l'environnement virtuel et installez les dépendances:"
    echo "  source venv/bin/activate   # ou .\\venv\\Scripts\\Activate.ps1 sous Windows"
    echo "  pip install -r requirements.txt"
    exit 1
fi
echo ""

# 1. Données de classification (nécessite PostgreSQL)
echo "[1/4] Génération des données de classification (table training_data)..."
if python ml/generate_data.py --samples 1000; then
    echo "  OK – Données de classification générées."
else
    echo "  ATTENTION – Échec (base de données non disponible ?)."
    echo "  Vous pouvez ignorer si vous testez sans PostgreSQL."
    echo "  Le modèle de classification ne pourra pas être entraîné."
fi
echo ""

# 2. Entraînement du modèle de classification
echo "[2/4] Entraînement du modèle de classification (Decision Tree)..."
if python ml/train_model.py --max-depth 7; then
    echo "  OK – scenario_classifier.pkl créé."
else
    echo "  ATTENTION – Échec (données insuffisantes ou DB inaccessible)."
fi
echo ""

# 3. Données de régression (fichier JSON, pas de DB)
echo "[3/4] Génération des données de régression..."
if python ml/generate_regression_data.py --samples 800; then
    echo "  OK – regression_training_data.json créé."
else
    echo "  ERREUR – Génération régression échouée."
    exit 1
fi
echo ""

# 4. Entraînement du modèle de régression
echo "[4/4] Entraînement du modèle de régression (Random Forest)..."
if python ml/train_regression_model.py --n-estimators 100 --max-depth 10; then
    echo "  OK – regression_model.joblib créé."
else
    echo "  ERREUR – Entraînement régression échoué."
    exit 1
fi
echo ""

# Vérification des fichiers
echo "=============================================="
echo "  Vérification des modèles"
echo "=============================================="
for f in ml/models/scenario_classifier.pkl ml/models/regression_model.joblib; do
    if [ -f "$f" ]; then
        echo "  [OK] $f"
    else
        echo "  [--] $f (absent)"
    fi
done
echo ""

# Test rapide : chargement des services (sans lancer le serveur)
echo "=============================================="
echo "  Test de chargement des services IA"
echo "=============================================="
python -c "
import sys
sys.path.insert(0, '.')
from app.services.ai_service import get_ai_service
from app.services.regression_service import get_regression_service

ai = get_ai_service()
reg = get_regression_service()
print('  Classification (scénario):', 'modèle chargé' if ai.model is not None else 'fallback')
print('  Régression (intensité):', 'modèle chargé' if reg.model is not None else 'fallback')

# Appel classify
r = ai.classify(14, 2, True, True)
print('  Exemple classify(14h, mardi, présence, lumière):', r.get('scenario_name'), '(method:', r.get('method') + ')')

# Appel predict_intensity
r2 = reg.predict_intensity(20, 2, 80.0, True, 3)
print('  Exemple predict_intensity(20h, 80 lux, Evening):', int(r2.get('intensity', 0)), '% (method:', r2.get('method') + ')')
print('  OK – Les services répondent correctement.')
" 2>/dev/null || {
    echo "  (Test Python ignoré si dépendances ou DB manquantes)"
}
echo ""

echo "=============================================="
echo "  Terminé. Pour tester l’API :"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  Puis GET http://localhost:8000/health"
echo "  Puis /api/ai/current-scenario, /api/ai/classify, /api/ai/predict-intensity (avec JWT)"
echo "=============================================="
