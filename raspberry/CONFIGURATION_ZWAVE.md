# Configuration Z-Wave JS UI - Activation du WebSocket

## Problème

Z-Wave JS UI nécessite une configuration spécifique pour activer le serveur WebSocket qui permet la communication programmatique. Par défaut, seul l'interface web est accessible.

## Solution : Activer le serveur WebSocket dans Z-Wave JS UI

### Étape 1 : Accéder à l'interface web

1. Ouvrir un navigateur et aller sur : **http://10.109.150.133:8091**
2. Se connecter à l'interface Z-Wave JS UI

### Étape 2 : Configurer le serveur WebSocket

1. Aller dans **Settings** (Paramètres) - icône en haut à droite ou menu latéral
2. Scroller jusqu'à la section **"Home Assistant"**
3. Activer l'option **"Enable Z-Wave JS websocket server"**
   - Cette option active le serveur WebSocket qui peut être utilisé avec Home Assistant ou directement via API
4. **Sauvegarder** les paramètres (bouton en bas de la page)

### Étape 3 : Vérifier la configuration

Après activation, le serveur WebSocket devrait être accessible. Le port par défaut est généralement **3000**, mais peut varier selon la configuration.

### Étape 4 : Exposer le port 3000 dans Docker

**IMPORTANT** : Le port 3000 doit être exposé dans le `docker-compose.yml` pour que le WebSocket soit accessible depuis l'extérieur du container.

Vérifier que le fichier `/home/admin/zwave-js/docker-compose.yml` contient :

```yaml
ports:
  - "8091:8091"  # Interface web
  - "3000:3000"  # WebSocket server (ajouter cette ligne si absente)
```

Si le port 3000 n'est pas exposé, l'ajouter et redémarrer le container :

```bash
# Sur le RPi 10.109.150.133
cd /home/admin/zwave-js
sudo docker compose down
sudo docker compose up -d
```

### Étape 5 : Redémarrer le container (si nécessaire)

Si le WebSocket ne fonctionne pas après activation, redémarrer le container :

```bash
# Sur le RPi 10.109.150.133
cd /home/admin/zwave-js
sudo docker compose restart zwave-js

# Ou redémarrer complètement
sudo docker compose down
sudo docker compose up -d
```

### Étape 6 : Vérifier que le WebSocket est actif

Vérifier les logs du container :

```bash
sudo docker logs zwave-js | grep -i "websocket\|socket\|server" | tail -10
```

Vous devriez voir des messages indiquant que le serveur WebSocket est démarré.

### Étape 7 : Tester la connexion

```bash
cd /home/admin/sae_s5/raspberry
source venv/bin/activate
python test_zwave_connection.py
```

Le script devrait maintenant trouver l'endpoint WebSocket fonctionnel.

### Étape 8 : Tester le client WebSocket

```bash
python zwave_client_ws.py
```

Le client devrait se connecter et pouvoir contrôler l'ampoule.

## Configuration Docker - Port 3000

**IMPORTANT** : Le port 3000 doit être exposé dans le `docker-compose.yml` pour que le WebSocket soit accessible.

Le fichier `/home/admin/zwave-js/docker-compose.yml` doit contenir :

```yaml
services:
  zwave-js:
    # ... configuration existante ...
    ports:
      - "8091:8091"  # Interface web
      - "3000:3000"  # WebSocket server (OBLIGATOIRE)
```

**Note** : Le port 3000 doit être disponible. Vérifier avec :
```bash
sudo netstat -tulpn | grep 3000
```

## Dépannage

### Le WebSocket ne se connecte toujours pas après activation

1. **Vérifier que l'option est bien activée** dans l'interface Z-Wave JS UI :
   - Settings → Home Assistant → "Enable Z-Wave JS websocket server" doit être coché

2. **Vérifier que le port est bien exposé dans Docker** :
   ```bash
   sudo docker ps | grep zwave-js
   # Vérifier que le port 3000 est listé dans PORTS (si configuré)
   ```

3. **Vérifier les logs pour les erreurs** :
   ```bash
   sudo docker logs zwave-js | tail -50
   ```

4. **Vérifier que le port n'est pas utilisé par un autre service** :
   ```bash
   sudo netstat -tulpn | grep 3000
   ```

5. **Tester la connexion depuis le RPi lui-même** :
   ```bash
   python test_zwave_connection.py
   ```

6. **Vérifier le firewall** :
   ```bash
   sudo ufw status
   # Si nécessaire, autoriser le port 3000
   sudo ufw allow 3000/tcp
   ```

### Solution de contournement : Utiliser l'interface web

Si le WebSocket ne peut pas être activé, vous pouvez toujours contrôler l'ampoule via l'interface web Z-Wave JS UI à l'adresse http://10.109.150.133:8091.

## Alternative : Contrôle via l'interface web

Si le WebSocket n'est pas disponible ou si vous préférez une solution simple :

1. Accéder à http://10.109.150.133:8091
2. Aller dans l'onglet **"Nodes"**
3. Cliquer sur le nœud 4 (ampoule ABUS)
4. Utiliser les contrôles dans l'interface pour :
   - Allumer/éteindre
   - Ajuster l'intensité
   - Voir l'état actuel

Cette méthode fonctionne toujours mais nécessite une interaction manuelle.

## Note importante

Z-Wave JS UI peut avoir différentes configurations selon la version. Si le WebSocket n'est pas disponible après avoir suivi ces étapes :
- Vérifier la version de Z-Wave JS UI : `sudo docker exec zwave-js node --version`
- Consulter la documentation officielle : https://zwave-js.github.io/zwave-js-ui/
- Vérifier les issues GitHub pour des problèmes similaires

## Emplacement de l'option dans l'interface

Dans l'interface Z-Wave JS UI :
- **Settings** → Scroller jusqu'à **"Home Assistant"**
- Option : **"Enable Z-Wave JS websocket server"**
- Cette option active le serveur WebSocket sur le port configuré (généralement 3000)
