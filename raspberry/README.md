# API Flask Z-Wave (RPi)

API Flask déployée sur le Raspberry Pi qui héberge Z-Wave JS UI. Elle expose les commandes Z-Wave (ON/OFF, intensité) et est **compatible avec le backend** (10.109.150.75:8000).

## Architecture

```
Backend (10.109.150.75:8000)     →  HTTP  →  RPi (10.109.150.133:5000)  →  Socket.IO  →  Z-Wave JS UI (localhost:8091)
       ↑                                 ↑                                        ↑
   FastAPI /docs                    API Flask                              Contrôle Z-Wave
   Control Panel web                /api/devices/...                       (ampoule node 2, etc.)
```

- **Backend** : enregistre les Raspberry Pi et les appareils. Pour chaque commande (état, luminosité), il envoie une requête HTTP au RPi concerné.
- **RPi Z-Wave** : exécute cette API Flask (port 5000) et Z-Wave JS UI (port 8091). L’API traduit les appels `/api/devices/{id}/...` en commandes Z-Wave via Socket.IO.
- **Mapping** : dans la base du backend, le champ `gpio_pin` d’un appareil sur le RPi Z-Wave contient en fait le **node_id Z-Wave** (ex. `2` pour l’ampoule ABUS).

## Lier le backend au RPi Z-Wave

### 1. Enregistrer le Raspberry Pi dans le backend

Dans la base de données (table `raspberry_pis`) ou via l’API/admin, créez un RPi avec :

- **name** : ex. `RPi Z-Wave`
- **location** : ex. `Salon`
- **ip_address** : `10.109.150.133` (l’IP du RPi où tournent Z-Wave JS UI et cette API Flask)
- **api_key_hash** : hash de la clé API (selon votre schéma d’auth)

### 2. Créer les appareils Z-Wave (node_id = gpio_pin)

Pour chaque nœud Z-Wave à piloter depuis le backend, créez un **device** lié à ce RPi :

- **raspberry_pi_id** : id du RPi enregistré ci-dessus
- **gpio_pin** : **node_id Z-Wave** (ex. `2` pour l’ampoule ABUS Security Center Bulb)
- **name** : ex. `Ampoule ABUS`
- **type** : `light` ou `dimmer`

Exemple pour l’ampoule (node 2) :

| Champ          | Valeur        |
|----------------|---------------|
| raspberry_pi_id | id du RPi Z-Wave |
| gpio_pin       | **2**         |
| name           | Ampoule ABUS  |
| type           | dimmer        |

Le backend appellera alors :

- `POST http://10.109.150.133:5000/api/devices/2/state` avec `{"state": true/false}`
- `POST http://10.109.150.133:5000/api/devices/2/brightness` avec `{"brightness": 0-100, "transition": "immediate"|"fade"}`

### 3. Démarrer les services sur le RPi (10.109.150.133)

1. **Z-Wave JS UI** (Docker, port 8091) :

   ```bash
   cd /chemin/vers/zwave-js
   docker compose up -d
   ```

2. **API Flask Z-Wave** (port 5000) :

   ```bash
   cd sae_s5/raspberry
   pip install -r requirements.txt
   python api_flask_zwave.py
   ```

   Ou en production : `gunicorn -w 1 -b 0.0.0.0:5000 api_flask_zwave:app`

### 4. Vérifications

- Backend : `http://10.109.150.75:8000/docs` → tester `PUT /devices/{id}/state` et `PUT /devices/{id}/brightness`.
- RPi : `curl http://10.109.150.133:5000/health` → `{"status":"ok", "zwave_js_ui_url":"http://localhost:8091"}`.
- Z-Wave JS UI : `http://10.109.150.133:8091/#/control-panel` pour voir les nœuds (ex. 001 contrôleur, 002 ampoule).

## Routes exposées

### Compatibles backend (utilisées par le backend)

| Méthode | Route | Corps | Description |
|--------|--------|--------|-------------|
| POST | `/api/devices/<id>/state` | `{"state": true\|false}` | ON/OFF (id = node_id Z-Wave) |
| POST | `/api/devices/<id>/brightness` | `{"brightness": 0-100, "transition": "immediate"\|"fade"}` | Intensité |

### API Z-Wave (nœuds par node_id)

| Méthode | Route | Description |
|--------|--------|-------------|
| GET | `/health` | Santé de l’API |
| GET | `/api/nodes` | Liste des nœuds |
| GET | `/api/nodes/<node_id>` | Détail d’un nœud |
| POST | `/api/nodes/<node_id>/state` | ON/OFF |
| POST | `/api/nodes/<node_id>/brightness` | Intensité |
| GET | `/api/nodes/<node_id>/current` | État + intensité actuels |
| POST | `/api/nodes/<node_id>/interview` | Forcer l’interview |

## Fichiers

- **api_flask_zwave.py** : serveur Flask, routes `/api/devices/...` et `/api/nodes/...`.
- **zwave_client.py** : client Socket.IO vers Z-Wave JS UI (port 8091).
- **requirements.txt** : `python-socketio[asyncio_client]`, `flask`, `flask-cors`.

## Dépannage

- **Timeout / connexion refusée** : vérifier que Z-Wave JS UI écoute sur `http://localhost:8091` sur le même RPi que l’API Flask.
- **Backend ne reçoit pas de réponse** : vérifier que l’API Flask écoute sur `0.0.0.0:5000` et que le pare-feu du RPi autorise le port 5000 depuis 10.109.150.75.
- **Node non reconnu** : dans Z-Wave JS UI, vérifier que le nœud (ex. 002) est interviewé et que Multilevel Switch (CC 38) est supporté.
