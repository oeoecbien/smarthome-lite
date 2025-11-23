# Raspberry Pi - Passerelle IoT

Service Flask exécuté sur Raspberry Pi pour gérer les capteurs et actionneurs.

## Fonctionnalités

- Lecture des capteurs (PIR, luminosité)
- Contrôle des actionneurs (LED, relais)
- Publication d'événements vers le backend
- Réception de commandes depuis le backend

## Installation

```bash
# Sur Raspberry Pi
git clone <repo-url>
cd raspberrypi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
# Éditer config.py
python main.py
```

## Configuration

Éditer `config.py` :
- URL du backend
- API Key (récupérée depuis le backend)
- Configuration GPIO (pins des capteurs/actionneurs)

## Structure

```
raspberrypi/
├── main.py              # Point d'entrée
├── config.py            # Configuration
├── sensors/             # Modules capteurs
├── actuators/           # Modules actionneurs
├── api/                 # API Flask locale
└── services/            # Services (monitoring, events)
```

## Démarrage Automatique

Créer un service systemd pour démarrage au boot :

```bash
sudo cp smarthome-rpi.service /etc/systemd/system/
sudo systemctl enable smarthome-rpi
sudo systemctl start smarthome-rpi
```

