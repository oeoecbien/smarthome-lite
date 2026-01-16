"""
Client Python WebSocket pour communiquer avec Z-Wave JS UI
Utilise WebSocket au lieu de REST API
"""

import asyncio
import json
import logging
import uuid
from typing import Optional, Dict, Any, List

try:
    import websockets
except ImportError:
    print("websockets n'est pas installé. Installez-le avec: pip install websockets")
    raise

logger = logging.getLogger(__name__)


class ZWaveClientWS:
    """
    Client WebSocket pour communiquer avec Z-Wave JS UI
    
    Usage:
        client = ZWaveClientWS(ws_url="ws://localhost:8091")
        await client.connect()
        nodes = await client.get_nodes()
        await client.set_brightness(node_id=4, brightness=50)
    """
    
    def __init__(self, ws_url: str = "ws://localhost:3000", schema_version: int = 29):
        """
        Initialise le client Z-Wave WebSocket
        
        Args:
            ws_url: URL WebSocket de Z-Wave JS UI (peut être ws://host:port ou ws://host:port/socket.io)
            schema_version: Version du schéma Z-Wave JS (par défaut 29, peut être 1-30 selon la version)
        """
        # Si l'URL ne contient pas de chemin, essayer différents chemins possibles
        if '/' not in ws_url.replace('://', '').split(':')[-1]:
            # Essayer d'abord le chemin standard
            self.ws_url = ws_url
        else:
            self.ws_url = ws_url
        self.schema_version = schema_version
        self.ws = None
        self.message_id = 0
        self.pending_requests = {}
        self.connected = False
        self.initial_state = None  # Stocker l'état initial qui contient les nœuds
    
    def _new_message_id(self) -> str:
        """Génère un nouvel ID de message unique"""
        self.message_id += 1
        return str(self.message_id)
    
    async def connect(self):
        """Établit la connexion WebSocket"""
        # Essayer différents chemins WebSocket possibles
        possible_paths = [
            self.ws_url,  # Essayer d'abord l'URL telle quelle
            f"{self.ws_url}/socket.io",  # Socket.io path
            f"{self.ws_url}/ws",  # Chemin /ws
        ]
        
        last_error = None
        for ws_url_try in possible_paths:
            try:
                logger.info(f"Tentative de connexion à {ws_url_try}...")
                self.ws = await websockets.connect(ws_url_try, ping_interval=None)
                
                # Recevoir le message de bienvenue
                welcome = await self.ws.recv()
                logger.debug(f"Message de bienvenue: {welcome}")
                self.ws_url = ws_url_try  # Sauvegarder l'URL qui fonctionne
                break
            except Exception as e:
                last_error = e
                logger.debug(f"Échec avec {ws_url_try}: {e}")
                if self.ws:
                    try:
                        await self.ws.close()
                    except:
                        pass
                    self.ws = None
                continue
        else:
            # Aucun chemin n'a fonctionné
            raise ConnectionError(f"Impossible de se connecter à Z-Wave JS UI. Dernière erreur: {last_error}")
        
        try:
            
            # Initialiser la connexion
            await self._send({
                "messageId": self._new_message_id(),
                "command": "initialize",
                "schemaVersion": self.schema_version,
                "additionalUserAgentComponents": {
                    "client": "sae_s5_python"
                }
            })
            
            # Attendre la réponse d'initialisation
            init_response = await self._receive_response()
            logger.debug(f"Initialisation: {init_response}")
            
            # Démarrer l'écoute
            await self._send({
                "messageId": self._new_message_id(),
                "command": "start_listening"
            })
            
            # Recevoir l'état initial
            initial_state = await self._receive_response()
            self.initial_state = initial_state
            logger.debug(f"État initial reçu")
            
            self.connected = True
            logger.info("Connexion WebSocket établie")
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {e}")
            raise
    
    async def _send(self, message: Dict[str, Any]):
        """Envoie un message via WebSocket"""
        if not self.ws:
            raise RuntimeError("WebSocket non connecté")
        await self.ws.send(json.dumps(message))
        logger.debug(f"Message envoyé: {message.get('command')}")
    
    async def _receive_response(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Reçoit une réponse via WebSocket"""
        if not self.ws:
            raise RuntimeError("WebSocket non connecté")
        
        try:
            message = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            response = json.loads(message)
            return response
        except asyncio.TimeoutError:
            raise TimeoutError("Timeout lors de la réception de la réponse")
    
    async def _send_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Envoie une commande et attend la réponse"""
        message_id = self._new_message_id()
        message = {
            "messageId": message_id,
            "command": command,
            **kwargs
        }
        
        await self._send(message)
        response = await self._receive_response()
        
        # Vérifier si c'est la bonne réponse
        if response.get("messageId") == message_id:
            return response
        
        # Sinon, continuer à recevoir jusqu'à trouver la bonne réponse
        while True:
            response = await self._receive_response()
            if response.get("messageId") == message_id:
                return response
    
    async def get_nodes(self) -> List[int]:
        """Récupère la liste de tous les nœuds Z-Wave"""
        if not self.connected:
            await self.connect()
        
        # Essayer de récupérer depuis l'état initial
        if self.initial_state:
            # L'état initial peut contenir les nœuds dans différents formats
            if "result" in self.initial_state:
                result = self.initial_state.get("result", {})
                # Chercher les nœuds dans l'état
                if "nodes" in result:
                    nodes = result["nodes"]
                    if isinstance(nodes, list):
                        return nodes
                    elif isinstance(nodes, dict):
                        return list(nodes.keys())
                # Chercher dans le driver state
                driver_state = result.get("driver", {}).get("nodes", {})
                if driver_state:
                    return [int(node_id) for node_id in driver_state.keys() if node_id.isdigit()]
        
        # Essayer la commande driver.get_node_ids
        try:
            response = await self._send_command("driver.get_node_ids")
            if response.get("result", {}).get("success"):
                nodes = response.get("result", {}).get("nodeIds", [])
                if nodes:
                    logger.info(f"Récupéré {len(nodes)} nœuds Z-Wave via get_node_ids")
                    return nodes
        except Exception as e:
            logger.debug(f"get_node_ids a échoué: {e}")
        
        # Dernière tentative : utiliser les nœuds connus
        logger.warning("Impossible de récupérer la liste complète des nœuds, utilisation des nœuds connus")
        return [1, 4]  # Contrôleur (1) et ampoule ABUS (4)
    
    async def get_node(self, node_id: int) -> Dict[str, Any]:
        """Récupère les informations d'un nœud spécifique"""
        if not self.connected:
            await self.connect()
        
        response = await self._send_command("node.get_state", nodeId=node_id)
        
        # success est au niveau racine, pas dans result
        if response.get("success", False):
            state = response.get("result", {}).get("state", {})
            if state:
                return state
            else:
                logger.error(f"État vide pour le nœud {node_id}: {response}")
                raise ValueError(f"État vide pour le nœud {node_id}")
        else:
            error = response.get("result", {}).get("error", "Unknown error")
            logger.error(f"Erreur lors de la récupération du nœud {node_id}: {error}")
            raise ValueError(f"Impossible de récupérer le nœud {node_id}: {error}")
    
    async def set_value(
        self,
        node_id: int,
        value_id: Dict[str, Any],
        value: Any
    ) -> Dict[str, Any]:
        """
        Définit une valeur sur un nœud Z-Wave
        
        Args:
            node_id: ID du nœud Z-Wave
            value_id: Dictionnaire avec les propriétés du Value ID (commandClass, property, etc.)
            value: Valeur à définir
        """
        if not self.connected:
            await self.connect()
        
        response = await self._send_command(
            "node.set_value",
            nodeId=node_id,
            valueId=value_id,
            value=value
        )
        
        # success est au niveau racine
        if response.get("success", False):
            logger.info(f"Nœud {node_id}: valeur définie = {value}")
            return response.get("result", {})
        else:
            error = response.get("result", {}).get("error", response.get("error", "Unknown error"))
            logger.error(f"Erreur lors de la définition de la valeur: {error}")
            raise ValueError(f"Erreur: {error}")
    
    async def set_brightness(self, node_id: int, brightness: int) -> Dict[str, Any]:
        """
        Définit l'intensité d'une ampoule Z-Wave (0-100%)
        
        Args:
            node_id: ID du nœud Z-Wave
            brightness: Intensité en pourcentage (0-100)
        """
        # Convertir 0-100% en 0-99 pour Z-Wave
        if brightness == 0:
            zwave_value = 0
        else:
            zwave_value = max(1, int((brightness / 100) * 99))
        
        # Value ID pour Multilevel Switch (intensité)
        value_id = {
            "commandClass": 38,  # Multilevel Switch
            "endpoint": 0,
            "property": "targetValue"
        }
        
        return await self.set_value(node_id, value_id, zwave_value)
    
    async def turn_on(self, node_id: int, brightness: int = 99) -> Dict[str, Any]:
        """Allume un nœud Z-Wave"""
        return await self.set_brightness(node_id, brightness)
    
    async def turn_off(self, node_id: int) -> Dict[str, Any]:
        """Éteint un nœud Z-Wave"""
        return await self.set_brightness(node_id, 0)
    
    async def get_brightness(self, node_id: int) -> Optional[int]:
        """Récupère l'intensité actuelle d'une ampoule"""
        try:
            node = await self.get_node(node_id)
            values = node.get("values", [])
            
            # values peut être une liste ou un dictionnaire
            if isinstance(values, list):
                # Chercher la valeur currentValue du Multilevel Switch dans la liste
                for value_data in values:
                    if (value_data.get("commandClass") == 38 and
                        value_data.get("property") == "currentValue"):
                        zwave_value = value_data.get("value", 0)
                        # Convertir 0-99 → 0-100%
                        return int((zwave_value / 99) * 100) if zwave_value > 0 else 0
            elif isinstance(values, dict):
                # Format dictionnaire (ancien format)
                for value_key, value_data in values.items():
                    if (value_data.get("commandClass") == 38 and
                        value_data.get("property") == "currentValue"):
                        zwave_value = value_data.get("value", 0)
                        return int((zwave_value / 99) * 100) if zwave_value > 0 else 0
            return None
        except Exception as e:
            logger.warning(f"Impossible de récupérer l'intensité du nœud {node_id}: {e}")
            return None
    
    async def get_state(self, node_id: int) -> bool:
        """Récupère l'état ON/OFF d'une ampoule"""
        brightness = await self.get_brightness(node_id)
        return brightness is not None and brightness > 0
    
    async def close(self):
        """Ferme la connexion WebSocket"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            logger.info("Connexion WebSocket fermée")


# Exemple d'utilisation
if __name__ == "__main__":
    import socket
    
    async def test():
        # Utiliser localhost si on est sur le RPi, sinon l'IP du RPi
        hostname = socket.gethostname()
        if 'raspberrypi' in hostname.lower():
            # Sur le RPi, utiliser directement le port 3000 (WebSocket server)
            ws_url = "ws://localhost:3000"
        else:
            ws_url = "ws://10.109.150.133:3000"
        
        # Forcer UTF-8 pour stdout
        import sys
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        
        print(f"Connexion a Z-Wave JS UI: {ws_url}")
        
        client = ZWaveClientWS(ws_url=ws_url, schema_version=1)
        
        try:
            await client.connect()
            
            # Lister les nœuds
            nodes = await client.get_nodes()
            print(f"\nNoeuds disponibles: {len(nodes)}")
            for node_id in nodes:
                try:
                    node_info = await client.get_node(node_id)
                    node_name = node_info.get("name", "Unknown")
                    manufacturer = node_info.get("manufacturer", "Unknown")
                    print(f"  - Node {node_id}: {node_name} ({manufacturer})")
                except Exception as e:
                    print(f"  - Node {node_id}: (erreur: {e})")
            
            # Tester avec le nœud 4 (ampoule ABUS) si disponible
            node_id = 4
            if node_id not in nodes:
                print(f"\nATTENTION: Noeud {node_id} non trouve. Utilisez un noeud disponible.")
                return
            
            # Récupérer les informations
            node_info = await client.get_node(node_id)
            print(f"\nInformations du noeud {node_id}:")
            device_config = node_info.get('deviceConfig', {})
            label = node_info.get('label', device_config.get('label', 'Unknown'))
            manufacturer = device_config.get('manufacturer', 'Unknown')
            print(f"  Nom: {label}")
            print(f"  Fabricant: {manufacturer}")
            
            # Tester l'allumage
            print(f"\nTest: Allumage a 50%")
            await client.set_brightness(node_id, 50)
            await asyncio.sleep(2)
            
            # Récupérer l'état
            brightness = await client.get_brightness(node_id)
            state = await client.get_state(node_id)
            print(f"  Etat: {'ON' if state else 'OFF'}, Intensite: {brightness}%")
            
            # Éteindre
            print(f"\nTest: Extinction")
            await client.turn_off(node_id)
            await asyncio.sleep(1)
            
            state = await client.get_state(node_id)
            print(f"  Etat: {'ON' if state else 'OFF'}")
            
        except Exception as e:
            print(f"ERREUR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await client.close()
    
    # Forcer UTF-8 pour stdout avant de lancer
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    
    asyncio.run(test())
