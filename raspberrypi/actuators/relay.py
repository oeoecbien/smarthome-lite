"""
Module de contrôle des relais pour prises connectées.
"""

import logging
import RPi.GPIO as GPIO

import config

logger = logging.getLogger(__name__)


class RelayController:
    """
    Contrôleur de relais pour prises connectées.
    """
    
    def __init__(self):
        self.pin = config.RELAY_PIN
        self.current_state = False
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)  # Relais OFF par défaut
        
        logger.info(f"Relay Controller initialisé sur GPIO {self.pin}")
    
    def set_state(self, state: bool):
        """
        Définit l'état du relais.
        
        Args:
            state: True pour ON, False pour OFF
        """
        try:
            GPIO.output(self.pin, GPIO.HIGH if state else GPIO.LOW)
            self.current_state = state
            status = "ON" if state else "OFF"
            logger.info(f"Relay {status}")
        except Exception as e:
            logger.error(f"Erreur lors du contrôle du relais: {e}")
    
    def turn_on(self):
        """Active le relais (prise ON)."""
        self.set_state(True)
    
    def turn_off(self):
        """Désactive le relais (prise OFF)."""
        self.set_state(False)
    
    def get_state(self) -> bool:
        """
        Retourne l'état actuel du relais.
        
        Returns:
            True si ON, False si OFF
        """
        return self.current_state
    
    def toggle(self):
        """Inverse l'état du relais."""
        self.set_state(not self.current_state)
    
    def cleanup(self):
        """Nettoie les ressources GPIO."""
        GPIO.output(self.pin, GPIO.LOW)  # Éteindre avant cleanup
        GPIO.cleanup(self.pin)
        logger.info("Relay Controller nettoyé")
