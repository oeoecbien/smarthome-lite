"""
Point d'entrée principal du service Flask pour Raspberry Pi.
"""

import logging
import signal
import sys

from flask import Flask
from flask_cors import CORS

import config
from services.backend_client import BackendClient
from services.heartbeat import HeartbeatService
from sensors.bluetooth import BluetoothSensor
from sensors.light import LightSensor
from actuators.led import LEDController
from actuators.relay import RelayController
from api.routes import api_bp, init_controllers

# Import GPIO seulement si nécessaire (pour LED/Relay)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO non disponible (mode test sans matériel)")

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Variables globales pour les services
backend_client = None
heartbeat_service = None
bluetooth_sensor = None
light_sensor = None
led_controller = None
relay_controller = None

# Application Flask
app = Flask(__name__)
CORS(app)  # Permettre les requêtes cross-origin si nécessaire

# Enregistrer le blueprint API
app.register_blueprint(api_bp)


def cleanup():
    """Nettoie les ressources avant l'arrêt."""
    logger.info("Nettoyage des ressources...")
    
    # Arrêter les services
    if heartbeat_service:
        heartbeat_service.stop()
    
    if bluetooth_sensor:
        bluetooth_sensor.stop()
    
    if light_sensor:
        light_sensor.stop()
    
    if backend_client:
        backend_client.stop_queue_processor()
    
    # Nettoyer les actionneurs
    if led_controller:
        led_controller.cleanup()
    
    if relay_controller:
        relay_controller.cleanup()
    
    # Nettoyer GPIO (si nécessaire, pour LED/Relay)
    if GPIO_AVAILABLE:
        try:
            GPIO.cleanup()
        except:
            pass  # Ignorer si GPIO n'a pas été utilisé
    
    logger.info("Nettoyage terminé")


def signal_handler(sig, frame):
    """Gestionnaire de signaux pour arrêt propre."""
    logger.info("Signal d'arrêt reçu")
    cleanup()
    sys.exit(0)


def init_services():
    """Initialise tous les services."""
    global backend_client, heartbeat_service, bluetooth_sensor, light_sensor
    global led_controller, relay_controller
    
    try:
        # Initialiser le client backend
        logger.info("Initialisation du client backend...")
        backend_client = BackendClient()
        backend_client.start_queue_processor()
        
        # Initialiser le service de heartbeat
        logger.info("Initialisation du service de heartbeat...")
        heartbeat_service = HeartbeatService(backend_client)
        heartbeat_service.start()
        
        # Initialiser les capteurs
        logger.info("Initialisation des capteurs...")
        bluetooth_sensor = BluetoothSensor(backend_client)
        bluetooth_sensor.start()
        
        light_sensor = LightSensor(backend_client)
        light_sensor.start()
        
        # Initialiser les actionneurs
        logger.info("Initialisation des actionneurs...")
        led_controller = LEDController()
        relay_controller = RelayController()
        
        # Initialiser les contrôleurs dans l'API
        init_controllers(led_controller, relay_controller)
        
        logger.info("Tous les services initialisés avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}", exc_info=True)
        cleanup()
        raise


@app.route('/')
def root():
    """Point d'entrée racine."""
    return {
        "service": "SmartHome Raspberry Pi Gateway",
        "status": "running",
        "version": "1.0.0"
    }


@app.route('/health')
def health():
    """Endpoint de santé pour monitoring."""
    queue_size = backend_client.get_queue_size() if backend_client else 0
    
    return {
        "status": "healthy",
        "queue_size": queue_size,
        "sensors": {
            "bluetooth": "active" if bluetooth_sensor else "inactive",
            "light": "active" if light_sensor else "inactive"
        },
        "actuators": {
            "led": "active" if led_controller else "inactive",
            "relay": "active" if relay_controller else "inactive"
        }
    }


if __name__ == '__main__':
    # Enregistrer les gestionnaires de signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialiser les services
        init_services()
        
        # Démarrer le serveur Flask
        logger.info(f"Démarrage du serveur Flask sur {config.FLASK_HOST}:{config.FLASK_PORT}")
        app.run(
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=config.FLASK_DEBUG,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
    finally:
        cleanup()
