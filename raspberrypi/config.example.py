# Configuration Raspberry Pi
# Copier ce fichier vers config.py et remplir les valeurs

# Backend Configuration
BACKEND_URL = "http://votre-serveur:8000"
API_KEY = "votre-api-key-64-caracteres"  # Récupérée depuis le backend

# GPIO Configuration
PIR_SENSOR_PIN = 4          # GPIO 4 (Pin 7)
LIGHT_SENSOR_TYPE = "BH1750"  # "BH1750" ou "LDR"
LIGHT_SENSOR_I2C_ADDRESS = 0x23  # Pour BH1750

# LED Configuration
LED_PWM_PIN = 18            # GPIO 18 (Pin 12)
LED_PWM_FREQUENCY = 1000    # Hz

# Relay Configuration
RELAY_PIN = 23              # GPIO 23 (Pin 16)

# Monitoring
LIGHT_READING_INTERVAL = 10  # Secondes entre chaque mesure
HEARTBEAT_INTERVAL = 60      # Secondes entre chaque heartbeat

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

