#!/usr/bin/env bash
# Test des endpoints IA via l'API (avec JWT).
#
# Usage (depuis backend/ ou depuis la racine du projet) :
#   export API_BASE_URL="http://localhost:8000"   # optionnel, défaut ci-dessous
#   export API_USER="votre_username"               # optionnel
#   export API_PASS="votre_password"               # optionnel
#   ./backend/ml/scripts/test_ai_api.sh
#   # ou depuis backend/ :
#   ./ml/scripts/test_ai_api.sh
#
# Prérequis : API démarrée (uvicorn app.main:app --reload --host 0.0.0.0 --port 8000)
#             et un utilisateur existant en base pour le login.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Si on est dans backend/ml/scripts, backend = 2 niveaux au-dessus
if [ -d "$SCRIPT_DIR/../../app" ]; then
    BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
else
    BACKEND_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
fi
PROJECT_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

# Charger uniquement BACKEND_URL, API_USER, API_PASS depuis .env (évite erreurs de syntaxe sur d’autres lignes)
if [ -f "$PROJECT_ROOT/.env" ]; then
    while IFS= read -r line; do
        [[ "$line" =~ ^BACKEND_URL= ]] && export BACKEND_URL="${line#BACKEND_URL=}"
        [[ "$line" =~ ^API_USER= ]] && export API_USER="${line#API_USER=}"
        [[ "$line" =~ ^API_PASS= ]] && export API_PASS="${line#API_PASS=}"
    done < <(grep -E '^(BACKEND_URL|API_USER|API_PASS)=' "$PROJECT_ROOT/.env" 2>/dev/null || true)
fi

API_BASE_URL="${BACKEND_URL:-${API_BASE_URL:-http://localhost:8000}}"
API_USER="${API_USER:-}"
API_PASS="${API_PASS:-}"

echo "=============================================="
echo "  Test des endpoints IA (API)"
echo "=============================================="
echo "API_BASE_URL=$API_BASE_URL"
echo ""

# Vérifier que l'API répond
if ! curl -sf "$API_BASE_URL/health" > /dev/null; then
    echo "Erreur: l'API ne répond pas à $API_BASE_URL/health"
    echo "Démarrez l'API avec: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "[Health]"
curl -s "$API_BASE_URL/health" | python3 -m json.tool
echo ""

if [ -z "$API_USER" ] || [ -z "$API_PASS" ]; then
    echo "Variables API_USER et API_PASS non définies."
    echo "Définissez-les pour tester les endpoints protégés :"
    echo "  export API_USER=admin API_PASS=xxx"
    echo "  $0"
    echo "Fin du script (health uniquement)."
    exit 0
fi

# Login et récupération du token
echo "[Login]"
RESP=$(curl -s -X POST "$API_BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$API_USER\",\"password\":\"$API_PASS\"}")
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null || true)

if [ -z "$TOKEN" ]; then
    echo "Erreur: échec du login (vérifiez API_USER / API_PASS)"
    echo "Réponse: $RESP"
    exit 1
fi
echo "  Token obtenu."
echo ""

# Fonction pour appeler un endpoint et afficher le résultat
run() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    echo "[$name]"
    if [ "$method" = "GET" ]; then
        curl -s -H "Authorization: Bearer $TOKEN" "$url"
    else
        curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$data" "$url"
    fi | python3 -m json.tool
    echo ""
}

run "GET /api/ai/current-scenario" GET "$API_BASE_URL/api/ai/current-scenario" ""
run "POST /api/ai/classify" POST "$API_BASE_URL/api/ai/classify" '{"hour":14,"day_of_week":2,"presence_detected":true,"light_on":true}'
run "GET /api/ai/model-metrics" GET "$API_BASE_URL/api/ai/model-metrics" ""
run "POST /api/ai/predict-intensity" POST "$API_BASE_URL/api/ai/predict-intensity" '{"hour":20,"day_of_week":2,"lux_value":80,"presence_detected":true,"scenario":3}'

echo "[GET /api/ai/ollama/recommendations] (optionnel)"
CODE=$(curl -s -o /tmp/ollama_resp.json -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$API_BASE_URL/api/ai/ollama/recommendations")
if [ "$CODE" = "200" ]; then
    python3 -m json.tool < /tmp/ollama_resp.json
else
    echo "  HTTP $CODE (normal si Ollama non configuré)"
    cat /tmp/ollama_resp.json | python3 -m json.tool 2>/dev/null || cat /tmp/ollama_resp.json
fi
echo ""

echo "=============================================="
echo "  Tests API IA terminés"
echo "=============================================="
