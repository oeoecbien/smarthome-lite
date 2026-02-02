"""
API Flask locale pour exposer les commandes Z-Wave
À déployer sur le RPi 10.109.150.133 (Z-Wave JS UI sur le même RPi).
Compatible avec le backend (10.109.150.75:8000) qui appelle /api/devices/{gpio_pin}/state et /brightness.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import logging
from zwave_client import ZWaveClient

app = Flask(__name__)
CORS(app)  # Autoriser les requêtes depuis le backend

# Configuration
ZWAVE_JS_UI_URL = "http://localhost:8091"  # Z-Wave JS UI sur le même RPi
API_KEY = None  # Optionnel : ajouter authentification si nécessaire

# Initialiser le client Z-Wave
zwave_client = ZWaveClient(base_url=ZWAVE_JS_UI_URL)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Exécute une coroutine asynchrone dans une nouvelle boucle d'événements.
    Déconnecte le client Z-Wave après chaque requête pour éviter "Event loop is closed"
    quand une requête suivante réutilise une connexion liée à une boucle déjà fermée.
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


@app.route('/health', methods=['GET'])
def health():
    """Vérifier l'état de l'API"""
    return jsonify({
        "status": "ok",
        "zwave_js_ui_url": ZWAVE_JS_UI_URL
    })


# ========== Routes compatibles Backend (device_service) ==========
# Le backend appelle http://{rpi.ip_address}:5000/api/devices/{gpio_pin}/...
# Sur le RPi Z-Wave, gpio_pin est utilisé comme node_id Z-Wave (ex: 2 pour l'ampoule ABUS).

@app.route('/api/devices/<int:device_id>/state', methods=['GET', 'POST'])
def set_device_state(device_id):
    """
    GET : retourne l'état actuel (state, brightness).
    POST : change l'état ON/OFF. Corps: { "state": true|false }
    """
    node_id = device_id  # gpio_pin du backend = node_id Z-Wave

    if request.method == 'GET':
        try:
            state = run_async(zwave_client.get_state(node_id))
            brightness = run_async(zwave_client.get_brightness(node_id))
            return jsonify({
                "success": True,
                "node_id": node_id,
                "state": state,
                "brightness": brightness
            })
        except Exception as e:
            logger.error(f"Erreur get_device_state node {device_id}: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # POST
    try:
        data = request.get_json() or {}
        state = data.get('state', False)

        if state:
            result = run_async(zwave_client.turn_on(node_id))
        else:
            result = run_async(zwave_client.turn_off(node_id))

        return jsonify({
            "success": True,
            "node_id": node_id,
            "state": state,
            "result": result
        })
    except Exception as e:
        logger.error(f"Erreur set_device_state node {device_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/devices/<int:device_id>/brightness', methods=['POST'])
def set_device_brightness(device_id):
    """
    Changer l'intensité d'un appareil (node_id Z-Wave = device_id).
    Corps: { "brightness": 0-100, "transition": "immediate"|"fade" (optionnel) }
    """
    try:
        data = request.get_json() or {}
        brightness = data.get('brightness', 0)
        transition = data.get('transition', 'immediate')
        node_id = device_id

        if not 0 <= brightness <= 100:
            return jsonify({
                "success": False,
                "error": "Brightness must be between 0 and 100"
            }), 400

        duration = None
        if transition == 'fade':
            duration = '5s'

        result = run_async(zwave_client.set_brightness(node_id, brightness, transition_duration=duration))

        return jsonify({
            "success": True,
            "node_id": node_id,
            "brightness": brightness,
            "result": result
        })
    except Exception as e:
        err_msg = str(e) or f"{type(e).__name__}"
        logger.error(f"Erreur set_device_brightness node {device_id}: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": err_msg
        }), 500


# ========== Routes API Z-Wave (nœuds par node_id) ==========

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Récupérer la liste des nœuds Z-Wave"""
    try:
        nodes = run_async(zwave_client.get_nodes())
        return jsonify({
            "success": True,
            "nodes": nodes
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des nœuds: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/nodes/<int:node_id>', methods=['GET'])
def get_node(node_id):
    """Récupérer les informations d'un nœud"""
    try:
        node = run_async(zwave_client.get_node(node_id))
        return jsonify({
            "success": True,
            "node": node
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du nœud {node_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/nodes/<int:node_id>/state', methods=['POST'])
def set_node_state(node_id):
    """Changer l'état ON/OFF d'un nœud"""
    try:
        data = request.get_json()
        state = data.get('state', False)

        if state:
            result = run_async(zwave_client.turn_on(node_id))
        else:
            result = run_async(zwave_client.turn_off(node_id))

        return jsonify({
            "success": True,
            "node_id": node_id,
            "state": state,
            "result": result
        })
    except Exception as e:
        logger.error(f"Erreur lors du changement d'état du nœud {node_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/nodes/<int:node_id>/brightness', methods=['POST'])
def set_node_brightness(node_id):
    """Changer l'intensité d'un nœud"""
    try:
        data = request.get_json()
        brightness = data.get('brightness', 0)

        if not 0 <= brightness <= 100:
            return jsonify({
                "success": False,
                "error": "Brightness must be between 0 and 100"
            }), 400

        result = run_async(zwave_client.set_brightness(node_id, brightness))

        return jsonify({
            "success": True,
            "node_id": node_id,
            "brightness": brightness,
            "result": result
        })
    except Exception as e:
        logger.error(f"Erreur lors du changement d'intensité du nœud {node_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/nodes/<int:node_id>/current', methods=['GET'])
def get_node_current(node_id):
    """Récupérer l'état actuel d'un nœud"""
    try:
        state = run_async(zwave_client.get_state(node_id))
        brightness = run_async(zwave_client.get_brightness(node_id))

        return jsonify({
            "success": True,
            "node_id": node_id,
            "state": state,
            "brightness": brightness
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'état du nœud {node_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/nodes/<int:node_id>/interview', methods=['POST'])
def interview_node(node_id):
    """Forcer l'interview d'un nœud"""
    try:
        result = run_async(zwave_client.interview_node(node_id))
        return jsonify({
            "success": True,
            "node_id": node_id,
            "result": result
        })
    except Exception as e:
        logger.error(f"Erreur lors de l'interview du nœud {node_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    logger.info("Démarrage de l'API Flask Z-Wave sur le port 5000")
    logger.info(f"Z-Wave JS UI URL: {ZWAVE_JS_UI_URL}")
    app.run(host='0.0.0.0', port=5000, debug=True)
