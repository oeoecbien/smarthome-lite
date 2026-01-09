"""
Routes Flask pour l'API locale du Raspberry Pi.
"""

from flask import Blueprint, request, jsonify
import logging

from actuators.led import LEDController
from actuators.relay import RelayController

logger = logging.getLogger(__name__)

# Créer le blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Contrôleurs (seront initialisés dans main.py)
led_controller = None
relay_controller = None


def init_controllers(led: LEDController, relay: RelayController):
    """Initialise les contrôleurs depuis main.py."""
    global led_controller, relay_controller
    led_controller = led
    relay_controller = relay


@api_bp.route('/devices/<int:device_id>/state', methods=['PUT'])
def set_device_state(device_id: int):
    """
    Change l'état d'un appareil (ON/OFF).
    
    Body JSON:
        {"state": true}  ou  {"state": false}
    """
    try:
        data = request.get_json()
        if not data or 'state' not in data:
            return jsonify({"error": "Champ 'state' requis"}), 400
        
        state = bool(data['state'])
        
        # Pour l'instant, on contrôle directement les actionneurs
        # Dans une version plus avancée, on pourrait mapper device_id vers actionneur
        if device_id == 1:  # Exemple: device_id 1 = LED
            if led_controller:
                if state:
                    led_controller.turn_on()
                else:
                    led_controller.turn_off()
                return jsonify({
                    "success": True,
                    "device_id": device_id,
                    "state": state
                })
            else:
                return jsonify({"error": "LED controller non initialisé"}), 500
        
        elif device_id == 2:  # Exemple: device_id 2 = Relay
            if relay_controller:
                if state:
                    relay_controller.turn_on()
                else:
                    relay_controller.turn_off()
                return jsonify({
                    "success": True,
                    "device_id": device_id,
                    "state": state
                })
            else:
                return jsonify({"error": "Relay controller non initialisé"}), 500
        
        else:
            return jsonify({"error": f"Appareil {device_id} non trouvé"}), 404
            
    except Exception as e:
        logger.error(f"Erreur lors du changement d'état: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/devices/<int:device_id>/brightness', methods=['PUT'])
def set_device_brightness(device_id: int):
    """
    Change l'intensité lumineuse d'un appareil (pour LED dimmable).
    
    Body JSON:
        {"brightness": 75}  # 0-100
    """
    try:
        data = request.get_json()
        if not data or 'brightness' not in data:
            return jsonify({"error": "Champ 'brightness' requis"}), 400
        
        brightness = int(data['brightness'])
        brightness = max(0, min(100, brightness))  # Clamp 0-100
        
        # Pour l'instant, on contrôle directement la LED
        if device_id == 1:  # Exemple: device_id 1 = LED
            if led_controller:
                led_controller.set_brightness(brightness)
                return jsonify({
                    "success": True,
                    "device_id": device_id,
                    "brightness": brightness
                })
            else:
                return jsonify({"error": "LED controller non initialisé"}), 500
        else:
            return jsonify({"error": f"Appareil {device_id} ne supporte pas le dimming"}), 400
            
    except Exception as e:
        logger.error(f"Erreur lors du réglage de l'intensité: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Vérification de santé de l'API locale.
    """
    return jsonify({
        "status": "healthy",
        "service": "raspberry-pi-api"
    })


@api_bp.route('/status', methods=['GET'])
def get_status():
    """
    Retourne le statut des actionneurs.
    """
    status = {
        "led": {
            "brightness": led_controller.get_brightness() if led_controller else None
        },
        "relay": {
            "state": relay_controller.get_state() if relay_controller else None
        }
    }
    return jsonify(status)
