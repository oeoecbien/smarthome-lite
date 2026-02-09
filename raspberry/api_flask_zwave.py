"""
API Flask locale pour exposer les commandes Z-Wave au backend SmartHome Lite.
À déployer sur le RPi qui héberge Z-Wave JS UI (voir zwave-js/docker-compose.yml).

Contrat backend (app/services/device_service.py) :
  - GET/POST http://{rpi.ip_address}:5000/api/devices/{gpio_pin}/state
  - POST     http://{rpi.ip_address}:5000/api/devices/{gpio_pin}/brightness
Sur un RPi Z-Wave, gpio_pin = node_id Z-Wave (ex: 3 pour l'ampoule ABUS).

Configuration : variables dans sae_s5/.env (pas de .env dans raspberry/).
"""

import asyncio
import logging
from pathlib import Path
from functools import wraps

# Charger le .env à la racine du projet (sae_s5/.env) avant tout import de config
_env_path = Path(__file__).resolve().parent.parent / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(_env_path)
except ImportError:
    pass

from flask import Flask, request, jsonify
from flask_cors import CORS

from config import (
    ZWAVE_JS_UI_URL,
    ZWAVE_JS_WS_URL,
    API_HOST,
    API_PORT,
    API_KEY,
    DEBUG,
    BACKEND_URL,
    BACKEND_HEARTBEAT_INTERVAL,
    MULTISENSOR7_NODE_ID,
)
from zwave_client import ZWaveClient

# URL WebSocket Socket.IO (celle utilisée par le client Z-Wave, ex. ws://localhost:8091/socket.io/)
ZWAVE_JS_UI_WS_URL = ZWAVE_JS_UI_URL.replace("http://", "ws://", 1).replace("https://", "wss://", 1) + "/socket.io/"

app = Flask(__name__)
app.config["DEBUG"] = DEBUG
CORS(app)

# Client Z-Wave : WebSocket (port 3000) en priorité, puis Socket.IO (8091)
zwave_client = ZWaveClient(base_url=ZWAVE_JS_UI_URL, ws_url=ZWAVE_JS_WS_URL)

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Exécute une coroutine dans une nouvelle boucle d'événements.
    Déconnecte le client Z-Wave après chaque requête pour éviter "Event loop is closed".
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(zwave_client.close())
        except Exception:
            pass
        loop.close()


def require_api_key(f):
    """Si RASPBERRY_API_KEY est défini, exige le header X-API-Key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not API_KEY:
            return f(*args, **kwargs)
        key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if key != API_KEY:
            return jsonify({"success": False, "error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated


# ---------- Racine et santé ----------

@app.route("/", methods=["GET"])
def root():
    """Point d'entrée racine (évite 404 sur GET /)."""
    return jsonify({
        "message": "API Flask Z-Wave (SmartHome Lite)",
        "status": "running",
        "health": "/health",
        "api_devices": "/api/devices/<node_id>/state|brightness",
        "api_nodes": "/api/nodes",
        "api_sensor": "/api/nodes/<node_id>/sensor",
        "zwave_js_ui_url": ZWAVE_JS_UI_URL,
        "zwave_js_ui_ws_url": ZWAVE_JS_UI_WS_URL,
        "zwave_js_ws_url": ZWAVE_JS_WS_URL,
    })


@app.route("/health", methods=["GET"])
def health():
    """Santé de l’API (backend peut l’utiliser pour heartbeat)."""
    return jsonify({
        "status": "ok",
        "zwave_js_ui_url": ZWAVE_JS_UI_URL,
        "zwave_js_ui_ws_url": ZWAVE_JS_UI_WS_URL,
        "zwave_js_ws_url": ZWAVE_JS_WS_URL,
    })


@app.route("/docs", methods=["GET"])
def docs():
    """Documentation de l'API (liste des endpoints)."""
    endpoints = [
        ("GET", "/", "Infos API (status, health, liens)."),
        ("GET", "/health", "Santé (backend heartbeat)."),
        ("GET", "/docs", "Cette documentation."),
        ("GET", "/api/nodes", "Liste des nœuds Z-Wave."),
        ("GET", "/api/nodes/<node_id>", "Détail d'un nœud."),
        ("GET", "/api/nodes/<node_id>/sensor", "Valeurs capteur (mouvement, température, humidité, etc.). Requiert X-API-Key si RASPBERRY_API_KEY est défini."),
        ("GET", "/api/nodes/<node_id>/current", "État et intensité actuels (lampe)."),
        ("POST", "/api/nodes/<node_id>/state", "ON/OFF. Corps: { \"state\": true|false }."),
        ("POST", "/api/nodes/<node_id>/brightness", "Intensité. Corps: { \"brightness\": 0-100 }."),
        ("POST", "/api/nodes/<node_id>/interview", "Forcer l'interview du nœud."),
        ("GET", "/api/devices/<node_id>/state", "État lampe (state, brightness). Requiert X-API-Key."),
        ("POST", "/api/devices/<node_id>/state", "ON/OFF. Corps: { \"state\": true|false }. Requiert X-API-Key."),
        ("POST", "/api/devices/<node_id>/brightness", "Intensité. Corps: { \"brightness\": 0-100 }. Requiert X-API-Key."),
    ]
    def _esc(s: str) -> str:
        """Échappe < et > pour affichage HTML (évite que <node_id> soit interprété comme balise)."""
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    rows = "".join(
        f'<tr><td><code>{_esc(m)}</code></td><td><code>{_esc(p)}</code></td><td>{_esc(d)}</td></tr>'
        for m, p, d in endpoints
    )
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>API Z-Wave – Documentation</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 800px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }}
    th {{ background: #f5f5f5; }}
    code {{ background: #f0f0f0; padding: 0.1em 0.3em; border-radius: 3px; }}
    h1 {{ margin-top: 0; }}
  </style>
</head>
<body>
  <h1>API Flask Z-Wave – Documentation</h1>
  <p>Base URL : <code>{request.url_root.rstrip("/")}</code></p>
  <p>Authentification : si <code>RASPBERRY_API_KEY</code> est défini, envoyer le header <code>X-API-Key</code> pour les routes <code>/api/devices/*</code> et <code>/api/nodes/*/sensor</code>.</p>
  <table>
    <thead><tr><th>Méthode</th><th>Endpoint</th><th>Description</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""
    return app.response_class(html, mimetype="text/html; charset=utf-8")


# ---------- Routes compatibles backend (device_service) ----------
# device_id dans l’URL = gpio_pin côté backend = node_id Z-Wave sur ce RPi

@app.route("/api/devices/<int:device_id>/state", methods=["GET", "POST"])
@require_api_key
def set_device_state(device_id):
    """
    GET : état actuel (state, brightness).
    POST : ON/OFF. Corps: { "state": true|false }
    """
    node_id = device_id

    if request.method == "GET":
        try:
            # Détecter si ce nœud est un capteur (MultiSensor, etc.) : pas de state/brightness lampe
            is_sensor = run_async(zwave_client.is_sensor_node(node_id))
            if is_sensor:
                return jsonify({
                    "success": True,
                    "node_id": node_id,
                    "sensor": True,
                    "state": None,
                    "brightness": None,
                })
            state, brightness, from_cache, unknown = run_async(
                zwave_client.get_state_and_brightness(node_id)
            )
            payload = {
                "success": True,
                "node_id": node_id,
                "state": state,
                "brightness": brightness,
            }
            if from_cache:
                payload["cached"] = True
            if unknown:
                payload["unknown"] = True  # Lecture impossible, état réel inconnu (ne pas afficher OFF)
            return jsonify(payload)
        except Exception as e:
            logger.error("get_device_state node %s: %s", device_id, e)
            return jsonify({"success": False, "error": str(e)}), 500

    try:
        data = request.get_json(force=True, silent=True) or {}
        state = data.get("state", False)
        if state:
            result = run_async(zwave_client.turn_on(node_id))
        else:
            result = run_async(zwave_client.turn_off(node_id))
        return jsonify({
            "success": True,
            "node_id": node_id,
            "state": state,
            "result": result,
        })
    except Exception as e:
        logger.error("set_device_state node %s: %s", device_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/devices/<int:device_id>/brightness", methods=["POST"])
@require_api_key
def set_device_brightness(device_id):
    """
    Intensité. Corps: { "brightness": 0-100, "transition": "immediate"|"fade" (optionnel) }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        brightness = data.get("brightness", 0)
        transition = data.get("transition", "immediate")
        node_id = device_id

        if not 0 <= brightness <= 100:
            return jsonify({
                "success": False,
                "error": "Brightness must be between 0 and 100",
            }), 400

        duration = "5s" if transition == "fade" else None
        result = run_async(
            zwave_client.set_brightness(node_id, brightness, transition_duration=duration)
        )
        return jsonify({
            "success": True,
            "node_id": node_id,
            "brightness": brightness,
            "result": result,
        })
    except Exception as e:
        logger.error("set_device_brightness node %s: %s", device_id, e, exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- API Z-Wave (nœuds par node_id) ----------

@app.route("/api/nodes", methods=["GET"])
def get_nodes():
    """Liste des nœuds Z-Wave."""
    try:
        nodes = run_async(zwave_client.get_nodes())
        return jsonify({"success": True, "nodes": nodes})
    except Exception as e:
        logger.error("get_nodes: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nodes/<int:node_id>", methods=["GET"])
def get_node(node_id):
    """Détail d’un nœud."""
    try:
        node = run_async(zwave_client.get_node(node_id))
        return jsonify({"success": True, "node": node})
    except Exception as e:
        logger.error("get_node %s: %s", node_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nodes/<int:node_id>/state", methods=["POST"])
def set_node_state(node_id):
    """ON/OFF d’un nœud."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        state = data.get("state", False)
        if state:
            result = run_async(zwave_client.turn_on(node_id))
        else:
            result = run_async(zwave_client.turn_off(node_id))
        return jsonify({
            "success": True,
            "node_id": node_id,
            "state": state,
            "result": result,
        })
    except Exception as e:
        logger.error("set_node_state %s: %s", node_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nodes/<int:node_id>/brightness", methods=["POST"])
def set_node_brightness(node_id):
    """Intensité d’un nœud."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        brightness = data.get("brightness", 0)
        if not 0 <= brightness <= 100:
            return jsonify({
                "success": False,
                "error": "Brightness must be between 0 and 100",
            }), 400
        result = run_async(zwave_client.set_brightness(node_id, brightness))
        return jsonify({
            "success": True,
            "node_id": node_id,
            "brightness": brightness,
            "result": result,
        })
    except Exception as e:
        logger.error("set_node_brightness %s: %s", node_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nodes/<int:node_id>/current", methods=["GET"])
def get_node_current(node_id):
    """État et intensité actuels (une seule lecture)."""
    try:
        state, brightness, from_cache, unknown = run_async(
            zwave_client.get_state_and_brightness(node_id)
        )
        payload = {
            "success": True,
            "node_id": node_id,
            "state": state,
            "brightness": brightness,
        }
        if from_cache:
            payload["cached"] = True
        if unknown:
            payload["unknown"] = True
        return jsonify(payload)
    except Exception as e:
        logger.error("get_node_current %s: %s", node_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nodes/<int:node_id>/sensor", methods=["GET"])
@require_api_key
def get_node_sensor(node_id):
    """
    Valeurs capteur du nœud (mouvement, température, humidité, luminosité, UV, batterie).
    Compatible Aeotec MultiSensor 7 (ZWA024). Retourne device_type si reconnu.
    """
    try:
        data = run_async(zwave_client.get_sensor_data(node_id))
        return jsonify({"success": True, **data})
    except Exception as e:
        logger.error("get_node_sensor %s: %s", node_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/nodes/<int:node_id>/interview", methods=["POST"])
def interview_node(node_id):
    """Forcer l’interview d’un nœud."""
    try:
        result = run_async(zwave_client.interview_node(node_id))
        return jsonify({"success": True, "node_id": node_id, "result": result})
    except Exception as e:
        logger.error("interview_node %s: %s", node_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


def _backend_heartbeat_loop():
    """Appelle périodiquement le backend pour signaler que le RPi est en ligne (is_online = True)."""
    import time
    import urllib.request
    import urllib.error
    if not BACKEND_URL or not API_KEY:
        logger.debug("Backend heartbeat désactivé (BACKEND_URL ou RASPBERRY_API_KEY manquant)")
        return
    url = f"{BACKEND_URL}/api/raspberry-pis/heartbeat"
    interval = max(15, BACKEND_HEARTBEAT_INTERVAL)
    first_run = True
    while True:
        if not first_run:
            time.sleep(interval)
        first_run = False
        try:
            req = urllib.request.Request(url, method="GET", headers={"X-API-Key": API_KEY})
            urllib.request.urlopen(req, timeout=5)
            logger.debug("Backend heartbeat OK")
        except urllib.error.HTTPError as e:
            logger.debug("Backend heartbeat HTTP %s: %s", e.code, e.reason)
        except Exception as e:
            logger.debug("Backend heartbeat: %s", e)


def _motion_to_backend_loop():
    """Envoie POST /api/presence au backend à chaque détection de mouvement (front montant)."""
    import time
    import urllib.request
    import urllib.error
    import json
    if not BACKEND_URL or not API_KEY or not MULTISENSOR7_NODE_ID:
        logger.debug("Motion→backend désactivé (BACKEND_URL, RASPBERRY_API_KEY ou MULTISENSOR7_NODE_ID manquant)")
        return
    url = f"{BACKEND_URL}/api/presence"
    interval = 5  # secondes entre deux lectures
    last_motion = False
    while True:
        time.sleep(interval)
        try:
            motion = run_async(zwave_client.get_motion_state(MULTISENSOR7_NODE_ID))
            if motion and not last_motion:
                # Front montant : envoi au backend
                data = json.dumps({"sensor_node_id": MULTISENSOR7_NODE_ID}).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    method="POST",
                    headers={
                        "X-API-Key": API_KEY,
                        "Content-Type": "application/json",
                    },
                )
                urllib.request.urlopen(req, timeout=10)
                logger.info("Mouvement détecté (node %s) → backend", MULTISENSOR7_NODE_ID)
            last_motion = motion
        except urllib.error.HTTPError as e:
            logger.debug("Motion→backend HTTP %s: %s", e.code, e.reason)
        except Exception as e:
            logger.debug("Motion→backend: %s", e)


if __name__ == "__main__":
    import threading
    if BACKEND_URL and API_KEY:
        _heartbeat = threading.Thread(target=_backend_heartbeat_loop, daemon=True)
        _heartbeat.start()
        logger.info("Heartbeat backend démarré (GET %s toutes les %ss)", f"{BACKEND_URL}/api/raspberry-pis/heartbeat", BACKEND_HEARTBEAT_INTERVAL)
    if BACKEND_URL and API_KEY and MULTISENSOR7_NODE_ID:
        _motion = threading.Thread(target=_motion_to_backend_loop, daemon=True)
        _motion.start()
        logger.info("Détecteur (node %s) → présence backend démarré", MULTISENSOR7_NODE_ID)
    logger.info("Démarrage API Flask Z-Wave sur %s:%s", API_HOST, API_PORT)
    logger.info("Z-Wave JS UI: %s", ZWAVE_JS_UI_URL)
    app.run(host=API_HOST, port=API_PORT, debug=DEBUG)
