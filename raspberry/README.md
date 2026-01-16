# Code Raspberry Pi - Gestion Z-Wave

Ce dossier contient le code Python pour gérer les appareils Z-Wave depuis le Raspberry Pi 10.109.150.133.

## Fichiers

- **`zwave_client_ws.py`** : Client Python WebSocket pour communiquer avec Z-Wave JS UI (nécessite activation du WebSocket)
- **`api_flask_zwave.py`** : API Flask locale (optionnelle) pour exposer les commandes Z-Wave via HTTP REST
- **`setup_zwave.sh`** : Script de diagnostic et configuration Z-Wave JS UI
- **`CONFIGURATION_ZWAVE.md`** : Guide détaillé pour activer le serveur WebSocket dans Z-Wave JS UI
- **`requirements.txt`** : Dépendances Python nécessaires

## Architecture

```
Backend (10.109.150.75:8000)
    │
    │ HTTP/REST
    │
    ▼
RPi Z-Wave (10.109.150.133)
    │
    ├─ Z-Wave JS UI (Docker) - Port 8091 (interface web)
    │  └─ WebSocket Server (si activé) - Port 3000
    │
    └─ API Flask locale (optionnelle) - Port 5000
       └─ Utilise zwave_client_ws.py pour communiquer avec Z-Wave JS UI
```

## Installation

### Sur le RPi 10.109.150.133

```bash
# Naviguer vers le dossier
cd /home/admin/sae_s5/raspberry

# Créer un environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Configuration Z-Wave JS UI

**IMPORTANT** : Avant d'utiliser le client WebSocket, il faut activer le serveur WebSocket dans Z-Wave JS UI.

### Instructions rapides

1. Accéder à l'interface web : **http://10.109.150.133:8091**
2. Aller dans **Settings** (Paramètres) - icône en haut à droite ou menu latéral
3. Scroller jusqu'à la section **"Home Assistant"**
4. Activer l'option **"Enable Z-Wave JS websocket server"**
   - Cette option active le serveur WebSocket pour la communication programmatique
5. **Sauvegarder** les paramètres (bouton en bas de la page)
6. Redémarrer le container si nécessaire :
   ```bash
   cd /home/admin/zwave-js
   sudo docker compose restart zwave-js
   ```

### Guide détaillé

Consultez **`CONFIGURATION_ZWAVE.md`** pour les instructions complètes et le dépannage.

### Vérification

Après activation, vérifier que le port 3000 est ouvert :
```bash
sudo netstat -tulpn | grep 3000
```

Le WebSocket devrait être accessible sur **ws://10.109.150.133:3000**.

## Utilisation

### Client Z-Wave WebSocket (Recommandé)

Z-Wave JS UI utilise WebSocket pour l'API. Utilisez `zwave_client_ws.py` :

```python
import asyncio
from zwave_client_ws import ZWaveClientWS

async def main():
    # Utiliser localhost si sur le RPi, sinon l'IP du RPi
    client = ZWaveClientWS(ws_url="ws://localhost:3000")  # Port WebSocket configuré
    await client.connect()
    
    # Lister les nœuds
    nodes = await client.get_nodes()
    print(f"Nœuds disponibles: {nodes}")
    
    # Allumer l'ampoule (node 4) à 50%
    await client.set_brightness(4, 50)
    
    # Éteindre
    await client.turn_off(4)
    
    # Récupérer l'état
    state = await client.get_state(4)
    brightness = await client.get_brightness(4)
    print(f"État: {state}, Intensité: {brightness}%")
    
    await client.close()

asyncio.run(main())
```

### Configuration et diagnostic

### Script de configuration

Utiliser le script d'aide pour vérifier la configuration :

```bash
./setup_zwave.sh
```

Ce script vérifie :
- L'état du container Docker
- Les ports ouverts
- L'accessibilité de l'interface web
- La détection du dongle Z-Wave

### Test du client WebSocket

Pour tester le client WebSocket :

```bash
python zwave_client_ws.py
```

Le script devrait :
1. Se connecter à Z-Wave JS UI sur le port 3000
2. Lister les nœuds (001 = contrôleur, 004 = ampoule ABUS)
3. Tester le contrôle de l'ampoule ABUS (nœud 4) : allumage à 50%, puis extinction

### API Flask (Optionnelle)

Si vous voulez exposer une API Flask locale sur le RPi pour que le backend communique via HTTP REST :

```bash
# Démarrer l'API Flask
python api_flask_zwave.py

# L'API sera accessible sur http://10.109.150.133:5000
```

**Endpoints disponibles :**
- `GET /health` - Vérifier l'état
- `GET /api/nodes` - Liste des nœuds
- `GET /api/nodes/<node_id>` - Informations d'un nœud
- `POST /api/nodes/<node_id>/state` - Changer état ON/OFF
  ```json
  {"state": true}
  ```
- `POST /api/nodes/<node_id>/brightness` - Changer intensité (0-100)
  ```json
  {"brightness": 50}
  ```
- `GET /api/nodes/<node_id>/current` - État actuel (state + brightness)
- `POST /api/nodes/<node_id>/interview` - Forcer l'interview du nœud

**Exemple de requête depuis le backend :**
```bash
# Allumer l'ampoule (node 4) à 50%
curl -X POST http://10.109.150.133:5000/api/nodes/4/brightness \
  -H "Content-Type: application/json" \
  -d '{"brightness": 50}'
```

## Intégration avec le Backend

Le backend (10.109.150.75) peut utiliser le client Z-Wave de deux façons :

### Option 1 : Direct via WebSocket (Recommandé)

Le backend utilise directement `zwave_client_ws.py` pour communiquer avec Z-Wave JS UI via WebSocket.

**Avantages :**
- Communication directe, pas de couche intermédiaire
- Plus rapide
- Moins de composants à maintenir

**Inconvénients :**
- Nécessite que le backend puisse se connecter au WebSocket du RPi
- Gestion des connexions WebSocket dans le backend

### Option 2 : Via API Flask

Le backend communique avec l'API Flask locale (http://10.109.150.133:5000) qui fait le pont avec Z-Wave JS UI.

**Avantages :**
- Interface REST standard (HTTP)
- Plus simple à intégrer dans le backend existant
- L'API Flask gère les connexions WebSocket

**Inconvénients :**
- Couche supplémentaire (légère latence)
- Un service supplémentaire à maintenir

## État actuel du système

- **RPi Z-Wave** : 10.109.150.133
- **Z-Wave JS UI** : http://10.109.150.133:8091 (interface web)
- **WebSocket Server** : À activer dans l'interface (généralement port 3000)
- **Ampoule Z-Wave** : Node ID 004 (ABUS Security Center Bulb SHLM10010 - FW v2.23)
- **Contrôleur Z-Wave** : Node ID 001 (Silicon Labs USB Controller 700/800 Series - FW v7.17.2)

## Dépannage

### Le WebSocket ne se connecte pas

1. **Utiliser le script de diagnostic** :
   ```bash
   ./setup_zwave.sh
   ```

2. Vérifier que Z-Wave JS UI est démarré :
   ```bash
   docker ps | grep zwave-js
   ```

3. Vérifier les logs :
   ```bash
   docker logs zwave-js | tail -20
   ```

4. **Vérifier que le serveur WebSocket est activé dans l'interface Z-Wave JS UI** :
   - Accéder à http://10.109.150.133:8091
   - Settings → Home Assistant → Enable Z-Wave JS websocket server
   - Vérifier que le port 3000 est exposé dans `docker-compose.yml`
   - Sauvegarder et redémarrer si nécessaire

5. Vérifier que le port 3000 est ouvert :
   ```bash
   sudo netstat -tulpn | grep 3000
   ```

6. Consulter `CONFIGURATION_ZWAVE.md` pour les instructions détaillées

### Solution temporaire : Contrôle manuel

En attendant l'activation du WebSocket, vous pouvez contrôler l'ampoule via l'interface web :
- Accéder à http://10.109.150.133:8091
- Aller dans l'onglet "Nodes"
- Cliquer sur le nœud 4 (ampoule ABUS)
- Utiliser les contrôles dans l'interface

### L'ampoule ne répond pas

1. Vérifier que l'ampoule est bien incluse (visible dans l'interface Z-Wave JS UI)
2. Vérifier la distance entre le dongle et l'ampoule
3. Forcer l'interview de l'ampoule dans l'interface Z-Wave JS UI
4. Vérifier les logs Z-Wave pour les erreurs de communication

## Notes importantes

- Z-Wave JS UI doit être accessible et le serveur WebSocket activé
- Le port 3000 doit être exposé dans le `docker-compose.yml` pour que le WebSocket soit accessible
- Le client WebSocket est asynchrone et utilise `websockets` pour les connexions
- L'API Flask est optionnelle et n'est nécessaire que si vous préférez une interface REST

## Références

- **Z-Wave JS UI Documentation** : https://zwave-js.github.io/zwave-js-ui/
- **Z-Wave JS API** : https://zwave-js.github.io/node-zwave-js/
- **Guide de configuration** : Voir `CONFIGURATION_ZWAVE.md`
