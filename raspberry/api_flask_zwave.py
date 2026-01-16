"""
API Flask locale pour exposer les commandes Z-Wave
À déployer sur le RPi 10.109.150.133 (optionnel)
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
    """Exécute une coroutine asynchrone"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route('/health', methods=['GET'])
def health():
    """Vérifier l'état de l'API"""
    return jsonify({
        "status": "ok",
        "zwave_js_ui_url": ZWAVE_JS_UI_URL
    })


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
    logger.info(f"Démarrage de l'API Flask Z-Wave sur le port 5000")
    logger.info(f"Z-Wave JS UI URL: {ZWAVE_JS_UI_URL}")
    app.run(host='0.0.0.0', port=5000, debug=True)
