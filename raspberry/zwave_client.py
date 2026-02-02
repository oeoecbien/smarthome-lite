"""
Client Z-Wave pour communiquer avec Z-Wave JS UI via Socket.IO.
Utilise l'API exposée par Z-Wave JS UI (port 8091 par défaut).
"""

import asyncio
import logging
from typing import Any, Optional

import socketio

logger = logging.getLogger(__name__)

# Command Class 38 = Multilevel Switch (dimmer / ampoule)
CC_MULTILEVEL_SWITCH = 38
# Propriétés pour CC 38
PROP_CURRENT_VALUE = "currentValue"
PROP_TARGET_VALUE = "targetValue"


class ZWaveClient:
    """
    Client asynchrone pour Z-Wave JS UI.
    Se connecte au serveur Socket.IO (même URL que l'interface web, ex: http://localhost:8091).
    """

    def __init__(self, base_url: str = "http://localhost:8091", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._sio: Optional[socketio.AsyncClient] = None

    async def _ensure_connected(self) -> socketio.AsyncClient:
        """Connexion Socket.IO si nécessaire."""
        if self._sio is None or not self._sio.connected:
            self._sio = socketio.AsyncClient(
                reconnection=True,
                reconnection_attempts=3,
                reconnection_delay=1,
            )

            @self._sio.event
            async def connect():
                logger.debug("Socket.IO connecté à Z-Wave JS UI")

            @self._sio.event
            async def disconnect():
                logger.debug("Socket.IO déconnecté de Z-Wave JS UI")

            try:
                await self._sio.connect(
                    self.base_url,
                    wait_timeout=self.timeout,
                    transports=["websocket", "polling"],
                )
            except Exception as e:
                logger.error(f"Impossible de se connecter à Z-Wave JS UI à {self.base_url}: {e}")
                raise
        return self._sio

    async def _call_api(self, method: str, *args: Any) -> Any:
        """
        Appel générique à l'API Z-Wave JS UI via Socket.IO.
        Format attendu: emit('api', { method, args }, callback).
        """
        sio = await self._ensure_connected()
        payload = {"method": method, "args": list(args)}
        try:
            result = await asyncio.wait_for(
                sio.call("api", payload, timeout=self.timeout),
                timeout=self.timeout,
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Timeout lors de l'appel API {method}")
            raise
        except Exception as e:
            logger.error(f"Erreur API {method}: {e}")
            raise

    def _value_id(self, node_id: int, property_name: str = PROP_TARGET_VALUE) -> dict:
        """Construit un valueId pour Multilevel Switch (CC 38)."""
        return {
            "nodeId": node_id,
            "commandClass": CC_MULTILEVEL_SWITCH,
            "endpoint": 0,
            "property": property_name,
        }

    async def _set_value(
        self,
        node_id: int,
        value: int,
        value_id: Optional[dict] = None,
        transition_duration: Optional[str] = None,
    ) -> Any:
        """
        Définit une valeur sur un nœud (Multilevel Switch CC 38).
        value: 0 = OFF, 1-99 = niveau, 255 = ON (full).
        Utilise emit (fire-and-forget) au lieu de call() pour éviter les timeouts :
        Z-Wave JS UI peut attendre l'acquittement du périphérique avant de rappeler.
        """
        vid = value_id or self._value_id(node_id)
        options = {}
        if transition_duration:
            options["transitionDuration"] = transition_duration
        args = [vid, value]
        if options:
            args.append(options)
        payload = {"method": "setValue", "args": args}
        sio = await self._ensure_connected()
        await sio.emit("api", payload)
        # Laisser le temps à la commande d'être envoyée (pas d'attente du callback)
        await asyncio.sleep(0.3)
        return {"success": True, "nodeId": node_id, "value": value}

    async def get_nodes(self) -> list:
        """Liste des nœuds Z-Wave (sans le contrôleur 1)."""
        try:
            result = await self._call_api("getNodes")
            if result and isinstance(result, list):
                return result
            # Parfois retourné comme { nodes: [...] }
            if isinstance(result, dict) and "nodes" in result:
                return result["nodes"]
            return []
        except Exception:
            # Fallback: getNodeCount puis getNode pour chaque id
            try:
                count = await self._call_api("getNodeCount") or 0
                nodes = []
                for i in range(1, count + 1):
                    n = await self._call_api("getNode", i)
                    if n:
                        nodes.append(n)
                return nodes
            except Exception as e2:
                logger.error(f"get_nodes fallback: {e2}")
                return []

    async def get_node(self, node_id: int) -> Optional[dict]:
        """Détails d'un nœud."""
        try:
            return await self._call_api("getNode", node_id)
        except Exception as e:
            logger.error(f"get_node {node_id}: {e}")
            return None

    async def turn_on(self, node_id: int, transition_duration: Optional[str] = None) -> Any:
        """Allume le nœud (Multilevel Switch à 255 ou currentValue > 0)."""
        return await self._set_value(node_id, 255, transition_duration=transition_duration)

    async def turn_off(self, node_id: int) -> Any:
        """Éteint le nœud (Multilevel Switch à 0)."""
        return await self._set_value(node_id, 0)

    async def set_brightness(
        self,
        node_id: int,
        brightness: int,
        transition_duration: Optional[str] = None,
    ) -> Any:
        """
        Règle l'intensité 0-100.
        Z-Wave Multilevel Switch utilise 0-99 ou 255 (ON); on mappe 100 -> 99.
        """
        if brightness <= 0:
            return await self.turn_off(node_id)
        level = min(99, max(1, brightness))
        return await self._set_value(
            node_id, level, transition_duration=transition_duration
        )

    async def get_state(self, node_id: int) -> bool:
        """État ON/OFF (currentValue > 0)."""
        try:
            val = await self._call_api("getValue", node_id, CC_MULTILEVEL_SWITCH, 0, PROP_CURRENT_VALUE)
            if val is None:
                return False
            if isinstance(val, dict) and "value" in val:
                return int(val.get("value", 0)) > 0
            return int(val) > 0
        except Exception as e:
            logger.debug(f"get_state {node_id}: {e}")
            return False

    async def get_brightness(self, node_id: int) -> int:
        """Valeur currentValue 0-99 (ou 255 pour ON)."""
        try:
            val = await self._call_api("getValue", node_id, CC_MULTILEVEL_SWITCH, 0, PROP_CURRENT_VALUE)
            if val is None:
                return 0
            if isinstance(val, dict) and "value" in val:
                v = int(val["value"])
            else:
                v = int(val)
            if v == 255:
                return 100
            return min(100, max(0, v))
        except Exception as e:
            logger.debug(f"get_brightness {node_id}: {e}")
            return 0

    async def interview_node(self, node_id: int) -> Any:
        """Lance l'interview d'un nœud."""
        return await self._call_api("refreshInfo", node_id)

    async def close(self) -> None:
        """Ferme la connexion Socket.IO."""
        if self._sio and self._sio.connected:
            await self._sio.disconnect()
            self._sio = None
