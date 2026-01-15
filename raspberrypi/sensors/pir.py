"""
Module de gestion du capteur PIR (Passive Infrared Sensor).
"""

import logging
import threading
import time
import RPi.GPIO as GPIO

import config
from services.backend_client import BackendClient

logger = logging.getLogger(__name__)


class PIRSensor:
    """
    Gestion du capteur PIR pour détection de présence.
    """
    
    def __init__(self, backend_client: BackendClient):
        self.pin = config.PIR_SENSOR_PIN
        self.backend_client = backend_client
        self.thread = None
        self.running = False
        self.last_state = False
        self.debounce_time = 0.1  # 100ms pour éviter les faux positifs
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # Callback pour détection de mouvement
        GPIO.add_event_detect(
            self.pin,
            GPIO.RISING,
            callback=self._on_motion_detected,
            bouncetime=200  # 200ms de debounce matériel
        )
        
        logger.info(f"Capteur PIR initialisé sur GPIO {self.pin}")
    
    def start(self):
        """Démarre la surveillance du capteur PIR."""
        if self.running:
            logger.warning("PIR sensor déjà démarré")
            return
        
        self.running = True
        logger.info("Surveillance PIR démarrée")
    
    def stop(self):
        """Arrête la surveillance du capteur PIR."""
        self.running = False
        GPIO.remove_event_detect(self.pin)
        logger.info("Surveillance PIR arrêtée")
    
    def _on_motion_detected(self, channel):
        """
        Callback appelé lors de la détection de mouvement.
        
        Args:
            channel: Numéro du GPIO (non utilisé mais requis par RPi.GPIO)
        """
        if not self.running:
            return
        
        # Debounce logiciel supplémentaire
        current_time = time.time()
        if not hasattr(self, '_last_detection_time'):
            self._last_detection_time = 0
        
        if current_time - self._last_detection_time < self.debounce_time:
            return
        
        self._last_detection_time = current_time
        
        # Lire l'état actuel
        state = GPIO.input(self.pin)
        
        # Envoyer uniquement si changement d'état (RISING)
        if state and not self.last_state:
            logger.info("Mouvement détecté par le capteur PIR")
            self.backend_client.send_presence_detection()
        
        self.last_state = state
    
    def read_state(self) -> bool:
        """
        Lit l'état actuel du capteur PIR.
        
        Returns:
            True si mouvement détecté, False sinon
        """
        return GPIO.input(self.pin) == GPIO.HIGH
