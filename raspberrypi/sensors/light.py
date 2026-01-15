"""
Module de gestion du capteur de luminosité (BH1750 ou LDR).
"""

import logging
import threading
import time

import config
from services.backend_client import BackendClient

logger = logging.getLogger(__name__)

# Import conditionnel selon le type de capteur
if config.LIGHT_SENSOR_TYPE == "BH1750":
    try:
        from smbus2 import SMBus
        BH1750_AVAILABLE = True
    except ImportError:
        logger.warning("smbus2 non disponible, simulation du capteur BH1750")
        BH1750_AVAILABLE = False
else:
    BH1750_AVAILABLE = False
    try:
        import RPi.GPIO as GPIO
        import spidev
        SPI_AVAILABLE = True
    except ImportError:
        logger.warning("spidev non disponible, simulation du capteur LDR")
        SPI_AVAILABLE = False


class LightSensor:
    """
    Gestion du capteur de luminosité (BH1750 via I2C ou LDR via SPI/ADC).
    """
    
    def __init__(self, backend_client: BackendClient):
        self.sensor_type = config.LIGHT_SENSOR_TYPE
        self.backend_client = backend_client
        self.interval = config.LIGHT_READING_INTERVAL
        self.thread = None
        self.running = False
        
        # Configuration selon le type de capteur
        if self.sensor_type == "BH1750":
            self._init_bh1750()
        else:  # LDR
            self._init_ldr()
        
        logger.info(f"Capteur de luminosité {self.sensor_type} initialisé")
    
    def _init_bh1750(self):
        """Initialise le capteur BH1750 via I2C."""
        self.i2c_address = config.LIGHT_SENSOR_I2C_ADDRESS
        
        if BH1750_AVAILABLE:
            try:
                self.bus = SMBus(1)  # I2C bus 1 (GPIO 2/3)
                # Mode de mesure continu haute résolution (1 lux)
                self.bus.write_byte(self.i2c_address, 0x10)
                logger.info(f"BH1750 initialisé sur I2C address 0x{self.i2c_address:02X}")
            except Exception as e:
                logger.error(f"Erreur initialisation BH1750: {e}")
                self.bus = None
        else:
            self.bus = None
            logger.warning("BH1750 en mode simulation")
    
    def _init_ldr(self):
        """Initialise le capteur LDR (via SPI/ADC)."""
        if SPI_AVAILABLE:
            try:
                # Configuration SPI pour MCP3008 (ADC 10 bits)
                self.spi = spidev.SpiDev()
                self.spi.open(0, 0)  # Bus 0, Device 0
                self.spi.max_speed_hz = 1000000
                logger.info("LDR initialisé via SPI")
            except Exception as e:
                logger.error(f"Erreur initialisation LDR: {e}")
                self.spi = None
        else:
            self.spi = None
            logger.warning("LDR en mode simulation")
    
    def start(self):
        """Démarre la lecture périodique du capteur."""
        if self.running:
            logger.warning("Light sensor déjà démarré")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._reading_loop, daemon=True)
        self.thread.start()
        logger.info(f"Lecture périodique démarrée (intervalle: {self.interval}s)")
    
    def stop(self):
        """Arrête la lecture périodique du capteur."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        # Nettoyer les ressources
        if self.sensor_type == "BH1750" and hasattr(self, 'bus') and self.bus:
            try:
                self.bus.close()
            except:
                pass
        elif self.sensor_type == "LDR" and hasattr(self, 'spi') and self.spi:
            try:
                self.spi.close()
            except:
                pass
        
        logger.info("Lecture périodique arrêtée")
    
    def _reading_loop(self):
        """Boucle de lecture périodique."""
        while self.running:
            try:
                lux_value = self.read_lux()
                if lux_value is not None:
                    self.backend_client.send_light_reading(lux_value)
                else:
                    logger.warning("Impossible de lire la luminosité")
            except Exception as e:
                logger.error(f"Erreur lors de la lecture de luminosité: {e}")
            
            # Attendre l'intervalle avant la prochaine lecture
            time.sleep(self.interval)
    
    def read_lux(self) -> float:
        """
        Lit la valeur de luminosité en lux.
        
        Returns:
            Valeur en lux, ou None en cas d'erreur
        """
        if self.sensor_type == "BH1750":
            return self._read_bh1750()
        else:  # LDR
            return self._read_ldr()
    
    def _read_bh1750(self) -> float:
        """Lit la valeur depuis le BH1750."""
        if not BH1750_AVAILABLE or not self.bus:
            # Mode simulation : retourner une valeur aléatoire réaliste
            import random
            return random.uniform(10, 500)
        
        try:
            # Lire 2 bytes (high byte, low byte)
            data = self.bus.read_i2c_block_data(self.i2c_address, 0x10, 2)
            lux = (data[0] << 8) | data[1]
            lux = lux / 1.2  # Conversion selon datasheet
            return round(lux, 2)
        except Exception as e:
            logger.error(f"Erreur lecture BH1750: {e}")
            return None
    
    def _read_ldr(self) -> float:
        """Lit la valeur depuis le LDR via ADC."""
        if not SPI_AVAILABLE or not self.spi:
            # Mode simulation : retourner une valeur aléatoire réaliste
            import random
            return random.uniform(10, 500)
        
        try:
            # Lire depuis le canal 0 du MCP3008
            adc_value = self._read_adc(0)
            
            # Conversion ADC (0-1023) vers lux approximatif
            # Cette formule doit être calibrée selon votre LDR
            # Formule simplifiée : lux = (1023 - adc_value) * 500 / 1023
            lux = (1023 - adc_value) * 500 / 1023
            return round(lux, 2)
        except Exception as e:
            logger.error(f"Erreur lecture LDR: {e}")
            return None
    
    def _read_adc(self, channel: int) -> int:
        """
        Lit une valeur depuis le MCP3008 ADC via SPI.
        
        Args:
            channel: Canal ADC (0-7)
            
        Returns:
            Valeur ADC (0-1023)
        """
        # Protocole SPI pour MCP3008
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data
