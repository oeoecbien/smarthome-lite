# Configuration Raspberry Pi
# Copier ce fichier vers config.py et remplir les valeurs

# Backend Configuration
BACKEND_URL = "http://votre-serveur:8000"
API_KEY = "votre-api-key-64-caracteres"  # Récupérée depuis le backend

# Bluetooth Configuration
BLUETOOTH_SCAN_INTERVAL = 30      # Secondes entre chaque scan
BLUETOOTH_SCAN_DURATION = 10       # Durée du scan en secondes
BLUETOOTH_RSSI_THRESHOLD = -80     # RSSI minimum en dBm (-80 = proche, -100 = loin)
BLUETOOTH_KNOWN_DEVICES = []       # Liste des MAC addresses à surveiller (optionnel)
                                    # Exemple: ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]

# GPIO Configuration (pour autres capteurs/actionneurs)
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

