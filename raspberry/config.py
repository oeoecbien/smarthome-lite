"""
Configuration de l'API Raspberry Z-Wave (serveur Flask sur le RPi).

Lit les variables depuis os.environ (chargé depuis sae_s5/.env à la racine).
Ne pas utiliser API_HOST / API_PORT du .env : ce sont les variables du backend (FastAPI).
Sur le RPi on utilise uniquement : ZWAVE_API_HOST, ZWAVE_API_PORT, ZWAVE_JS_*,
BACKEND_URL, RASPBERRY_API_KEY, BACKEND_HEARTBEAT_INTERVAL, ZWAVE_DEBUG.
"""
import os

# Z-Wave JS UI (zwave-js/docker-compose.yml : SOCKET_PORT=8091, interface web Socket.IO)
ZWAVE_JS_UI_URL = os.environ.get("ZWAVE_JS_UI_URL", "http://localhost:8091").rstrip("/")

def _default_ws_url(http_url: str) -> str:
    """Dérive ws://host:3000 depuis http://host:8091 (même host, port 3000)."""
    from urllib.parse import urlparse
    p = urlparse(http_url if "://" in http_url else "http://" + http_url)
    host = p.hostname or "localhost"
    scheme = "wss" if p.scheme == "https" else "ws"
    return f"{scheme}://{host}:3000"

# Z-Wave JS Server WebSocket (port 3000, protocole zwave-js-server) — prioritaire pour setValue
ZWAVE_JS_WS_URL = os.environ.get("ZWAVE_JS_WS_URL", "").strip() or _default_ws_url(ZWAVE_JS_UI_URL)

# API Flask Raspberry (backend appelle http://<rpi.ip>:5000)
ZWAVE_API_HOST = os.environ.get("ZWAVE_API_HOST", "0.0.0.0")
ZWAVE_API_PORT = int(os.environ.get("ZWAVE_API_PORT", "5000"))

# Alias utilisés par api_flask_zwave.py : app.run(host=API_HOST, port=API_PORT)
API_HOST = ZWAVE_API_HOST
API_PORT = ZWAVE_API_PORT

# Optionnel : clé API pour /api/devices/* (header X-API-Key)
API_KEY = os.environ.get("RASPBERRY_API_KEY") or None

# Backend SmartHome Lite : URL pour le heartbeat (RPi s'annonce en ligne). Ex: http://10.109.150.75:8000
BACKEND_URL = (os.environ.get("BACKEND_URL") or os.environ.get("SMARTHOME_BACKEND_URL") or "").rstrip("/")
# Intervalle en secondes entre chaque appel GET /api/raspberry-pis/heartbeat
BACKEND_HEARTBEAT_INTERVAL = int(os.environ.get("BACKEND_HEARTBEAT_INTERVAL", "30"))

# Debug (évite conflit avec DEBUG du backend)
DEBUG = os.environ.get("ZWAVE_DEBUG", os.environ.get("FLASK_DEBUG", "true")).lower() in ("1", "true", "yes")

# Détecteur de mouvement Z-Wave (MultiSense / MultiSensor 7) : node_id. 0 = désactivé.
# Pour que la lampe réagisse : enregistrer ce capteur côté backend (POST /api/raspberry-pis/{id}/register-sensor)
# puis lier la lampe au capteur (controlled_by_sensor_id + sensor_rules).
MULTISENSOR7_NODE_ID = int(os.environ.get("MULTISENSOR7_NODE_ID", "0"))
