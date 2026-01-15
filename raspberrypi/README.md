# Raspberry Pi - Passerelle IoT

Service Flask exécuté sur Raspberry Pi pour gérer les capteurs et actionneurs. Communication bidirectionnelle avec le backend FastAPI.

## Fonctionnalités

- **Lecture des capteurs** : PIR (détection de présence) et luminosité (BH1750 ou LDR)
- **Contrôle des actionneurs** : LED avec PWM (dimming) et relais (prises connectées)
- **Publication d'événements** : Envoi automatique des détections et mesures au backend
- **Réception de commandes** : API Flask locale pour recevoir les commandes du backend
- **Heartbeat** : Signal périodique pour indiquer l'état en ligne
- **Queue de messages** : Stockage des événements en cas de perte de connexion

## Installation

### Prérequis

- Raspberry Pi avec Raspberry Pi OS
- Python 3.9+
- Accès GPIO (nécessite les permissions appropriées)
- Composants matériels :
  - Capteur PIR
  - Capteur de luminosité (BH1750 via I2C ou LDR via SPI/ADC)
  - LED avec résistance
  - Relais (optionnel)

### Étapes d'Installation

```bash
# Sur Raspberry Pi
git clone <repo-url>
cd raspberrypi

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Configurer
cp config.example.py config.py
# Éditer config.py avec vos paramètres
nano config.py

# Tester le service
python main.py
```

## Configuration

Éditer `config.py` ou utiliser des variables d'environnement :

### Configuration Backend

- `BACKEND_URL` : URL du backend FastAPI (ex: `http://10.109.150.75:8000`)
- `API_KEY` : Clé API récupérée depuis le backend (64 caractères)

### Configuration GPIO

- `PIR_SENSOR_PIN` : GPIO pour le capteur PIR (défaut: GPIO 4)
- `LIGHT_SENSOR_TYPE` : Type de capteur (`BH1750` ou `LDR`)
- `LIGHT_SENSOR_I2C_ADDRESS` : Adresse I2C pour BH1750 (défaut: 0x23)
- `LED_PWM_PIN` : GPIO pour la LED avec PWM (défaut: GPIO 18)
- `LED_PWM_FREQUENCY` : Fréquence PWM en Hz (défaut: 1000)
- `RELAY_PIN` : GPIO pour le relais (défaut: GPIO 23)

### Configuration Monitoring

- `LIGHT_READING_INTERVAL` : Intervalle entre mesures de luminosité en secondes (défaut: 10)
- `HEARTBEAT_INTERVAL` : Intervalle entre heartbeats en secondes (défaut: 60)
- `LOG_LEVEL` : Niveau de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

### Configuration Flask

- `FLASK_HOST` : Adresse d'écoute (défaut: `0.0.0.0`)
- `FLASK_PORT` : Port d'écoute (défaut: `5000`)
- `FLASK_DEBUG` : Mode debug (défaut: `False`)

## Structure du Projet

```
raspberrypi/
├── main.py                    # Point d'entrée Flask
├── config.py                  # Configuration (créé depuis config.example.py)
├── config.example.py          # Exemple de configuration
├── requirements.txt            # Dépendances Python
├── smarthome-rpi.service       # Fichier systemd pour démarrage automatique
│
├── sensors/                   # Modules capteurs
│   ├── __init__.py
│   ├── pir.py                 # Gestion capteur PIR
│   └── light.py               # Gestion capteur luminosité (BH1750/LDR)
│
├── actuators/                 # Modules actionneurs
│   ├── __init__.py
│   ├── led.py                 # Contrôle LED avec PWM
│   └── relay.py               # Contrôle relais
│
├── api/                       # API Flask locale
│   ├── __init__.py
│   └── routes.py              # Endpoints REST locaux
│
└── services/                  # Services utilitaires
    ├── __init__.py
    ├── backend_client.py      # Client HTTP pour communication backend
    ├── heartbeat.py           # Service heartbeat périodique
    └── event_queue.py         # Queue de messages (référence)
```

## Fonctionnement

### Capteurs

**Capteur PIR (détection de présence) :**
- Détection automatique des mouvements
- Envoi immédiat d'événements au backend via `POST /api/presence`
- Anti-rebond matériel et logiciel intégré

**Capteur de luminosité :**
- Lecture périodique selon `LIGHT_READING_INTERVAL`
- Support BH1750 (I2C) et LDR (SPI/ADC)
- Envoi automatique des mesures au backend via `POST /api/light-readings`
- Mode simulation si matériel non disponible

### Actionneurs

**LED avec PWM :**
- Contrôle d'intensité de 0 à 100%
- Réception de commandes via `PUT /api/devices/{id}/brightness`
- Synchronisation d'état avec le backend

**Relais :**
- Contrôle ON/OFF pour prises connectées
- Réception de commandes via `PUT /api/devices/{id}/state`
- Synchronisation d'état avec le backend

### Communication Backend

**Envoi d'événements :**
- Détections de présence → `POST /api/presence`
- Mesures de luminosité → `POST /api/light-readings`
- Authentification via header `X-API-Key`

**Réception de commandes :**
- Le backend envoie des commandes HTTP POST à `http://<rpi_ip>:5000/api/devices/{id}/state` ou `/brightness`
- Authentification requise via header `X-API-Key`

**Heartbeat :**
- Envoi périodique pour indiquer que le Raspberry Pi est en ligne
- Intervalle configurable via `HEARTBEAT_INTERVAL`

**Queue de messages :**
- En cas de perte de connexion, les événements sont stockés dans une queue
- Réenvoi automatique lorsque la connexion est rétablie

## API Locale

Le service expose une API Flask locale sur le port 5000 (configurable) :

### Endpoints

- `GET /` : Informations sur le service
- `GET /health` : Vérification de santé
- `GET /api/status` : Statut des actionneurs
- `PUT /api/devices/{id}/state` : Changer l'état d'un appareil (ON/OFF)
- `PUT /api/devices/{id}/brightness` : Ajuster l'intensité lumineuse (0-100%)

**Note** : Les `device_id` sont mappés aux actionneurs (ex: 1 = LED, 2 = Relais). Ce mapping peut être étendu selon vos besoins.

## Démarrage Automatique

### Service systemd

Créer un service systemd pour démarrage au boot :

```bash
# Copier le fichier service
sudo cp smarthome-rpi.service /etc/systemd/system/

# Ajuster le chemin dans le fichier si nécessaire
sudo nano /etc/systemd/system/smarthome-rpi.service

# Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable smarthome-rpi
sudo systemctl start smarthome-rpi

# Vérifier le statut
sudo systemctl status smarthome-rpi

# Voir les logs
sudo journalctl -u smarthome-rpi -f
```

### Configuration du service

Éditer `/etc/systemd/system/smarthome-rpi.service` et ajuster :
- `User` : Utilisateur qui exécute le service (défaut: `pi`)
- `WorkingDirectory` : Chemin vers le dossier `raspberrypi`
- `ExecStart` : Chemin vers l'interpréteur Python dans le venv

## Dépannage

### Le service ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u smarthome-rpi -n 50

# Tester manuellement
cd /home/pi/smarthome/raspberrypi
source venv/bin/activate
python main.py
```

### Erreurs GPIO

- Vérifier les permissions : l'utilisateur doit être dans le groupe `gpio`
- Vérifier que les pins GPIO sont correctement configurés dans `config.py`
- Vérifier que les composants sont correctement connectés

### Erreurs de connexion au backend

- Vérifier que `BACKEND_URL` est correct
- Vérifier que l'API Key est valide
- Vérifier la connectivité réseau : `ping <backend_ip>`
- Vérifier les logs pour les erreurs HTTP

### Capteurs non détectés

- **BH1750** : Vérifier la connexion I2C (`i2cdetect -y 1`)
- **LDR** : Vérifier la connexion SPI et l'ADC (MCP3008)
- Le code fonctionne en mode simulation si le matériel n'est pas disponible

## Sécurité

- **API Key** : Authentification requise pour toutes les communications avec le backend
- **Validation** : Validation des commandes reçues avant exécution
- **Isolation** : Le service Flask local n'est accessible que sur le réseau local

## Notes

- Le code fonctionne en mode simulation si les bibliothèques GPIO ne sont pas disponibles (développement hors Raspberry Pi)
- Les événements sont mis en queue en cas de perte de connexion et réenvoyés automatiquement
- Le heartbeat permet au backend de savoir si le Raspberry Pi est en ligne

