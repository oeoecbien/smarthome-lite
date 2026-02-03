"""
Configuration de l'API Raspberry Z-Wave.
Lit les variables depuis os.environ (chargé depuis sae_s5/.env à la racine du projet).
Noms préfixés ZWAVE_* pour ne pas conflit avec le backend (API_PORT, etc.).
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

# Alias pour compatibilité (config utilisée par api_flask_zwave)
API_HOST = ZWAVE_API_HOST
API_PORT = ZWAVE_API_PORT

# Optionnel : clé API pour /api/devices/* (header X-API-Key)
API_KEY = os.environ.get("RASPBERRY_API_KEY") or None

# Debug (évite conflit avec DEBUG du backend)
DEBUG = os.environ.get("ZWAVE_DEBUG", os.environ.get("FLASK_DEBUG", "true")).lower() in ("1", "true", "yes")
