"""
Module de contrôle des LED avec PWM pour dimming.
"""

import logging
import RPi.GPIO as GPIO

import config

logger = logging.getLogger(__name__)


class LEDController:
    """
    Contrôleur de LED avec PWM pour ajustement d'intensité (dimming).
    """
    
    def __init__(self):
        self.pin = config.LED_PWM_PIN
        self.frequency = config.LED_PWM_FREQUENCY
        self.pwm = None
        self.current_brightness = 0
        
        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        
        # Initialiser PWM
        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.pwm.start(0)  # Démarrer à 0% (LED éteinte)
        
        logger.info(f"LED Controller initialisé sur GPIO {self.pin} (PWM {self.frequency}Hz)")
    
    def set_brightness(self, brightness: int):
        """
        Définit l'intensité de la LED.
        
        Args:
            brightness: Intensité en pourcentage (0-100)
        """
        # Valider la plage
        brightness = max(0, min(100, int(brightness)))
        
        try:
            self.pwm.ChangeDutyCycle(brightness)
            self.current_brightness = brightness
            logger.debug(f"LED brightness réglée à {brightness}%")
        except Exception as e:
            logger.error(f"Erreur lors du réglage de la LED: {e}")
    
    def turn_on(self, brightness: int = 100):
        """
        Allume la LED.
        
        Args:
            brightness: Intensité en pourcentage (0-100), défaut 100%
        """
        self.set_brightness(brightness)
        logger.info(f"LED allumée à {brightness}%")
    
    def turn_off(self):
        """Éteint la LED."""
        self.set_brightness(0)
        logger.info("LED éteinte")
    
    def get_brightness(self) -> int:
        """
        Retourne l'intensité actuelle de la LED.
        
        Returns:
            Intensité en pourcentage (0-100)
        """
        return self.current_brightness
    
    def cleanup(self):
        """Nettoie les ressources GPIO."""
        if self.pwm:
            self.pwm.stop()
            GPIO.cleanup(self.pin)
            logger.info("LED Controller nettoyé")
