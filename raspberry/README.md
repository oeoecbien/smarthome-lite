# API Flask Z-Wave (Raspberry Pi)

API Flask déployée sur le Raspberry Pi qui héberge **Z-Wave JS UI**. Elle expose les commandes Z-Wave (ON/OFF, intensité) et respecte le **contrat du backend** SmartHome Lite (`sae_s5/backend`). C’est l’**implémentation actuelle** du contrôleur RPi pour ce projet ; une option **GPIO / Bluetooth** (capteurs PIR, BH1750, relais) est décrite dans le README principal du projet pour référence.

## Liens avec le projet

| Composant | Rôle |
|-----------|------|
| **Backend** (`sae_s5/backend`) | Enregistre les Raspberry Pi et les appareils ; envoie les commandes HTTP vers `http://<rpi.ip_address>:5000/api/devices/...` |
| **Z-Wave JS** (`zwave-js/docker-compose.yml`) | Conteneur Z-Wave JS UI, port **8091** (SOCKET_PORT). Cette API s’y connecte en Socket.IO. |
| **Cette API** (`sae_s5/raspberry`) | Écoute sur le port **5000** ; reçoit les appels du backend et les traduit en commandes Z-Wave via Z-Wave JS UI. |

## Architecture

```
Backend (FastAPI, ex: 10.109.150.75:8000)
    │
    │  HTTP  →  http://<rpi.ip>:5000/api/devices/{gpio_pin}/state
    │           http://<rpi.ip>:5000/api/devices/{gpio_pin}/brightness
    ▼
RPi (cette API Flask :5000 + Z-Wave JS UI :8091)
    │
    │  Socket.IO  →  Z-Wave JS UI (localhost:8091, voir zwave-js/docker-compose.yml)
    ▼
Z-Wave JS UI (Docker)
    │
    └──  Dongle Z-Wave  →  Ampoules / prises (node_id = 2, 3, …)
```

- **Backend** : pour chaque appareil, stocke `raspberry_pi_id` et `gpio_pin`. Pour un RPi Z-Wave, **gpio_pin = node_id Z-Wave** (ex. 2 pour une ampoule).
- **RPi** : reçoit `/api/devices/<id>/...` avec `id = gpio_pin = node_id`, appelle Z-Wave JS UI en Socket.IO.

## Configuration

**Pas de `.env` dans `raspberry/`** : toute la config est dans **`sae_s5/.env`** à la racine du projet. Au démarrage, l’API charge ce fichier (chemin `sae_s5/raspberry/../.env`).

Variables utilisées (dans `sae_s5/.env`) :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `ZWAVE_JS_UI_URL` | URL Z-Wave JS UI (port 8091, interface web) | `http://localhost:8091` |
| `ZWAVE_JS_WS_URL` | **WebSocket** zwave-js-server (port **3000**) — utilisé en priorité pour `setValue` (ON/OFF, brightness). Voir [zwave-js-server](https://github.com/zwave-js/zwave-js-server). | Dérivé de `ZWAVE_JS_UI_URL` → `ws://host:3000` |
| `ZWAVE_API_HOST` | Interface d’écoute Flask | `0.0.0.0` |
| `ZWAVE_API_PORT` | Port de l’API (backend appelle ce port) | `5000` |
| `RASPBERRY_API_KEY` | Optionnel : clé pour header `X-API-Key` sur `/api/devices/*` et `/api/presence` | - |
| `MULTISENSOR7_NODE_ID` | Node ID Z-Wave du capteur de mouvement (ex. Aeotec MultiSensor 7). `0` = désactivé. | `0` |
| `ZWAVE_DEBUG` | Mode debug (ou `FLASK_DEBUG`) | `true` |

**Pourquoi le WebSocket (port 3000) ?** Le conteneur Z-Wave JS UI expose le port **3000** avec le protocole [zwave-js-server](https://github.com/zwave-js/zwave-js-server) (WebSocket brut, commande `node.set_value`). Les commandes d’écriture (luminosité, ON/OFF) passent par ce WebSocket en priorité ; si indisponible, le client utilise Socket.IO (port 8091).

## Lier le backend au RPi Z-Wave

### 1. Démarrer Z-Wave JS UI (sur le RPi)

```bash
cd zwave-js
docker compose up -d
```

Vérifier que le port **8091** est bien exposé (cf. `docker-compose.yml`).

### 2. Enregistrer le Raspberry Pi dans le backend

Via l’API admin ou la BDD, créer un Raspberry Pi avec :

- **name** : ex. `RPi Z-Wave`
- **location** : ex. `Salon`
- **ip_address** : IP du RPi où tournent Z-Wave JS UI et cette API (ex. `10.109.150.133`)

### 3. Créer les appareils (node_id = gpio_pin)

Pour chaque nœud Z-Wave à piloter, créer un **device** dans le backend :

- **raspberry_pi_id** : id du RPi enregistré
- **gpio_pin** : **node_id Z-Wave** (ex. **3** pour l’ampoule ABUS)
- **name** : ex. `Ampoule ABUS`
- **type** : `light` ou `dimmer`

Le backend appellera alors :

- `POST http://<rpi.ip>:5000/api/devices/3/state` avec `{"state": true|false}`
- `POST http://<rpi.ip>:5000/api/devices/3/brightness` avec `{"brightness": 0-100, "transition": "immediate"|"fade"}`

### 4. Démarrer l’API Flask sur le RPi

```bash
cd sae_s5/raspberry
pip install -r requirements.txt
python api_flask_zwave.py
```

En production :  
`gunicorn -w 1 -b 0.0.0.0:5000 api_flask_zwave:app`

### 5. Heartbeat (RPi « en ligne » dans l’interface)

Pour que le backend marque le RPi comme **en ligne** et que l’interface affiche le statut :

- Dans `sae_s5/.env` sur le RPi (ou partagé) : `BACKEND_URL=http://<ip-backend>:8000` et `RASPBERRY_API_KEY=<clé>`.
- La clé doit correspondre à celle enregistrée pour ce RPi dans l’admin (ou à `RASPBERRY_PI_API_KEY` du backend si une clé globale est utilisée).
- Au démarrage, l’API Flask envoie périodiquement `GET {BACKEND_URL}/api/raspberry-pis/heartbeat` avec le header `X-API-Key`. Le backend met alors à jour l’IP du RPi et `is_online = true`.

### 6. Contrôle depuis l’interface web

1. **Admin** enregistre le RPi (Admin → Raspberry Pis) puis les utilisateurs voient la liste dans « Ajouter un appareil ».
2. **Utilisateur** va sur **Appareils** → **Nouvel appareil** : choisit le RPi, saisit le **node_id Z-Wave** dans le champ « GPIO Pin », nom et type, puis crée.
3. Les cartes appareil permettent d’**allumer/éteindre** (switch) et de régler l’**intensité** (slider). Les commandes passent par le backend qui appelle `http://<rpi.ip>:5000/api/devices/<node_id>/state` ou `/brightness`.

Si le RPi est hors ligne, l’interface affiche une erreur explicite et peut afficher le statut « RPi hors ligne » sur la carte.

### 7. Vérifications

- Backend : `http://<backend>:8000/docs` → tester `PUT /api/devices/{id}/state` et `PUT /api/devices/{id}/brightness`.
- RPi : `curl http://<rpi.ip>:5000/health` → `{"status":"ok", "zwave_js_ui_url":"http://localhost:8091"}`.
- Z-Wave JS UI : `http://<rpi.ip>:8091` pour l’interface et les nœuds.

## Routes

### Compatibles backend (device_service)

| Méthode | Route | Corps | Description |
|--------|--------|--------|-------------|
| GET | `/api/devices/<id>/state` | - | État et intensité actuels |
| POST | `/api/devices/<id>/state` | `{"state": true\|false}` | ON/OFF |
| POST | `/api/devices/<id>/brightness` | `{"brightness": 0-100, "transition": "immediate"\|"fade"}` | Intensité |

### API Z-Wave (nœuds)

| Méthode | Route | Description |
|--------|--------|-------------|
| GET | `/health` | Santé de l’API |
| GET | `/api/nodes` | Liste des nœuds |
| GET | `/api/nodes/<node_id>` | Détail d’un nœud |
| POST | `/api/nodes/<node_id>/state` | ON/OFF |
| POST | `/api/nodes/<node_id>/brightness` | Intensité |
| GET | `/api/nodes/<node_id>/current` | État + intensité |
| POST | `/api/nodes/<node_id>/interview` | Forcer l’interview |

## Lampe ABUS Security Center Bulb (node 3)

Appareil testé : **ABUS Security Center Bulb** (SHLM10010), node_id **3**.

| Propriété | Valeur |
|-----------|--------|
| Command Class | 38 (Multilevel Switch) |
| Endpoint | 0 |
| **currentValue** | Lecture seule, 0–99 (état actuel) |
| **targetValue** | Lecture/écriture, 0–99 (cible) |
| valueId (lecture) | `3-38-0-currentValue` |
| valueId (écriture) | `3-38-0-targetValue` |

Cette lampe n’utilise **que la plage 0–99** (pas de valeur 255 pour « ON »). Le client Z-Wave (`zwave_client.py`) envoie donc **99** pour « allumer à fond » et mappe 0–100 % du backend vers 0–99 pour `targetValue`. Les réponses `currentValue` (0–99) sont converties en 0–100 pour l’API.

## Détection de mouvement (MultiSensor7)

Si un **MultiSensor7** (ou autre capteur Z-Wave avec CC 48 Binary Sensor) est sur le réseau, l’API Flask peut interroger son état et envoyer une détection de mouvement au backend à chaque **front montant** (mouvement détecté).

### Prérequis

- **Z-Wave** : le capteur (ex. Aeotec MultiSensor 7) est inclus dans le réseau et interrogé (Z-Wave JS UI).
- **Backend** : le RPi est enregistré dans **Administration → Raspberry Pis** avec la clé API (`RASPBERRY_API_KEY`).
- **.env** : `BACKEND_URL`, `RASPBERRY_API_KEY` et **`MULTISENSOR7_NODE_ID`** (node_id du capteur, ex. 5). Si `MULTISENSOR7_NODE_ID=0` ou non défini, la détection mouvement est désactivée.

### Comportement

Au démarrage de `api_flask_zwave.py`, un thread en arrière-plan :

1. Toutes les 5 secondes, lit l’état du nœud (Binary Sensor CC 48).
2. Si l’état passe de « pas de mouvement » à « mouvement », envoie `POST {BACKEND_URL}/api/presence` avec `{"sensor_node_id": <node_id>}` et le header `X-API-Key`.

Le backend enregistre la présence en BDD (table `presence`), déclenche les règles (ex. « si présence → allumer la lampe ») et l’IA utilise cette présence pour le scénario (Day / Away / etc.).

## Fichiers

| Fichier | Rôle |
|---------|------|
| `api_flask_zwave.py` | Serveur Flask, routes `/api/devices/...` et `/api/nodes/...`, thread motion → backend |
| `config.py` | Lecture des variables (depuis `sae_s5/.env`), alignée zwave-js et backend |
| `zwave_client.py` | Client Socket.IO vers Z-Wave JS UI (port 8091), lecture mouvement CC 48 |
| `requirements.txt` | Dépendances Python (Flask, python-socketio, aiohttp, …) |

## Dépannage

- **Timeout / connexion refusée** : Z-Wave JS UI doit écouter sur `http://localhost:8091` sur le même RPi que cette API. Vérifier `docker compose ps` et les ports dans `zwave-js/docker-compose.yml`.
- **Backend ne reçoit pas de réponse** : API Flask en `0.0.0.0:5000`, pare-feu du RPi autorisant le port 5000 depuis l’IP du backend.
- **Nœud non reconnu** : Dans Z-Wave JS UI, vérifier que le nœud est interviewé et supporte Multilevel Switch (CC 38) pour dimmers.
- **« Raspberry Pi RPI Salon not responding » (500 sur PUT /api/devices/7/state)** : Le backend appelle l’API Flask du RPi à l’adresse enregistrée (Admin → Raspberry Pis). Vérifier que **`api_flask_zwave.py` tourne bien sur la machine dont l’IP est enregistrée** (ex. 10.109.150.133). Si vous lancez Flask sur une autre machine (ex. votre PC), soit mettre à jour l’IP du RPi dans l’admin, soit lancer Flask sur le RPi (SSH sur 10.109.150.133 puis `python api_flask_zwave.py`). Vérifier aussi que le port 5000 est accessible depuis le serveur backend (pare-feu, réseau).