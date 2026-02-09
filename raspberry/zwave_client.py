"""
Client Z-Wave : WebSocket (zwave-js-server, port 3000) en priorité, puis Socket.IO (Z-Wave JS UI, 8091).

- Port 3000 (docker-compose) : protocole zwave-js-server (WebSocket brut), commande node.set_value.
  Voir https://github.com/zwave-js/zwave-js-server
- Port 8091 : Socket.IO (interface web Z-Wave JS UI), fallback si WebSocket indisponible.

Compatibilité lampe ABUS (node 3) : CC 38, currentValue/targetValue 0-99.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Tuple

import socketio

logger = logging.getLogger(__name__)

# Command Class 38 = Multilevel Switch (dimmer / ampoule)
CC_MULTILEVEL_SWITCH = 38
# Command Class 48 = Binary Sensor (mouvement MultiSensor7)
CC_BINARY_SENSOR = 48
# Command Class 49 = Multilevel Sensor (temp, humidité, luminosité, UV)
CC_MULTILEVEL_SENSOR = 49
# Command Class 128 = Battery
CC_BATTERY = 128
# Propriétés pour CC 38 (alignées sur Z-Wave JS UI, ex. lampe ABUS node 3)
PROP_CURRENT_VALUE = "currentValue"
PROP_TARGET_VALUE = "targetValue"

# Aeotec MultiSensor 7 (ZWA024) : manufacturerId 881, productType 2, productId 24
AEOTEC_MANUFACTURER_ID = 881
AEOTEC_MULTISENSOR7_PRODUCT_TYPE = 2
AEOTEC_MULTISENSOR7_PRODUCT_ID = 24
AEOTEC_MULTISENSOR7_MODEL = "ZWA024"
AEOTEC_MULTISENSOR7_NAME = "Aeotec MultiSensor 7"

# Niveau "ON" : 99 pour compatibilité appareils 0-99 uniquement (ex. ABUS SHLM10010)
# Certains dimmers acceptent 255 (dernier niveau), d'autres uniquement 0-99
ON_LEVEL_FULL = 99


class ZWaveClient:
    """
    Client Z-Wave : tente d'abord le WebSocket (zwave-js-server, port 3000), puis Socket.IO (8091).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8091",
        ws_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.ws_url = (ws_url or "").strip() or None  # ex. ws://localhost:3000
        self.timeout = timeout
        self._sio: Optional[socketio.AsyncClient] = None
        self._cache_current_value: Dict[int, int] = {}

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

    def _value_id_str(self, node_id: int, property_name: str = PROP_TARGET_VALUE) -> str:
        """Format string du valueId (ex. 3-38-0-targetValue) utilisé par Z-Wave JS UI."""
        return f"{node_id}-{CC_MULTILEVEL_SWITCH}-0-{property_name}"

    async def _set_value_via_ws(
        self,
        node_id: int,
        value: int,
        transition_duration: Optional[str] = None,
    ) -> Optional[dict]:
        """
        setValue via WebSocket (zwave-js-server, port 3000). Protocole documenté sur
        https://github.com/zwave-js/zwave-js-server (command node.set_value).
        """
        if not self.ws_url:
            return None
        try:
            import aiohttp
        except ImportError:
            return None
        try:
            timeout = aiohttp.ClientTimeout(total=min(15, self.timeout + 5))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.ws_connect(self.ws_url) as ws:
                    # 1) Recevoir version
                    msg = await ws.receive()
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        return None
                    data = json.loads(msg.data)
                    if data.get("type") != "version":
                        logger.debug("WS: attendu type=version, reçu %s", data.get("type"))
                        return None
                    schema = data.get("maxSchemaVersion", 0)
                    # 2) initialize
                    await ws.send_str(json.dumps({
                        "messageId": "init",
                        "command": "initialize",
                        "schemaVersion": min(schema, 31),
                    }))
                    while True:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5)
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        data = json.loads(msg.data)
                        if data.get("type") == "result" and data.get("messageId") == "init":
                            if not data.get("success", True):
                                raise RuntimeError("initialize failed")
                            break
                    # 3) start_listening
                    await ws.send_str(json.dumps({
                        "messageId": "listen",
                        "command": "start_listening",
                    }))
                    while True:
                        msg = await asyncio.wait_for(ws.receive(), timeout=10)
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        data = json.loads(msg.data)
                        if data.get("type") == "result" and data.get("messageId") == "listen":
                            if not data.get("success", True):
                                raise RuntimeError("start_listening failed")
                            break
                    # 4) node.set_value (valueId sans nodeId, cf. zwave-js-server API)
                    value_id = {
                        "commandClass": CC_MULTILEVEL_SWITCH,
                        "endpoint": 0,
                        "property": PROP_TARGET_VALUE,
                    }
                    payload = {
                        "messageId": f"set-{node_id}-{value}",
                        "command": "node.set_value",
                        "nodeId": node_id,
                        "valueId": value_id,
                        "value": value,
                    }
                    if transition_duration:
                        payload["options"] = {"transitionDuration": transition_duration}
                    await ws.send_str(json.dumps(payload))
                    # 5) Attendre résultat
                    set_msg_id = payload["messageId"]
                    while True:
                        msg = await asyncio.wait_for(ws.receive(), timeout=15)
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        data = json.loads(msg.data)
                        if data.get("messageId") == set_msg_id and data.get("type") == "result":
                            if data.get("success"):
                                self._cache_current_value[node_id] = value
                                return {"success": True, "nodeId": node_id, "value": value}
                            err = data.get("errorCode") or data.get("zwaveErrorMessage") or "unknown"
                            raise RuntimeError(f"node.set_value failed: {err}")
        except asyncio.TimeoutError:
            logger.warning("WebSocket setValue node %s timeout", node_id)
            return None
        except Exception as e:
            logger.debug("_set_value_via_ws node %s: %s", node_id, e)
            return None

    async def _set_value(
        self,
        node_id: int,
        value: int,
        value_id: Optional[dict] = None,
        transition_duration: Optional[str] = None,
    ) -> Any:
        """
        Définit targetValue (CC 38). Priorité : WebSocket (port 3000, zwave-js-server),
        puis Socket.IO (port 8091).
        """
        result = await self._set_value_via_ws(node_id, value, transition_duration)
        if result is not None:
            return result
        logger.debug("WebSocket indisponible, fallback Socket.IO pour node %s", node_id)
        vid = value_id or self._value_id(node_id, PROP_TARGET_VALUE)
        args = [vid, value]
        if transition_duration:
            args.append({"transitionDuration": transition_duration})
        timeout_sec = min(15, self.timeout + 5)
        try:
            result = await asyncio.wait_for(
                self._call_api("setValue", *args),
                timeout=timeout_sec,
            )
            self._cache_current_value[node_id] = value
            return result if result is not None else {"success": True, "nodeId": node_id, "value": value}
        except asyncio.TimeoutError:
            logger.warning("setValue node %s timeout (commande peut avoir été envoyée)", node_id)
            self._cache_current_value[node_id] = value
            return {"success": True, "nodeId": node_id, "value": value, "timeout": True}
        except Exception as e:
            logger.debug("setValue (object valueId) node %s: %s, try string valueId", node_id, e)
            try:
                vid_str = self._value_id_str(node_id, PROP_TARGET_VALUE)
                result = await asyncio.wait_for(
                    self._call_api("setValue", vid_str, value),
                    timeout=timeout_sec,
                )
                self._cache_current_value[node_id] = value
                return result if result is not None else {"success": True, "nodeId": node_id, "value": value}
            except Exception as e2:
                logger.error("setValue node %s: %s", node_id, e2)
                raise

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
        """Détails d'un nœud. Tente d'abord le HTTP (plus rapide) puis Socket.IO avec timeout court."""
        node = await self._get_node_via_http(node_id)
        if node:
            return node
        try:
            # Timeout court (15s) pour ne pas bloquer trop longtemps si Z-Wave JS UI est lent
            return await asyncio.wait_for(
                self._call_api("getNode", node_id),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            logger.warning("get_node %s: timeout (lecture Z-Wave lente)", node_id)
            return None
        except Exception as e:
            logger.error(f"get_node {node_id}: {e}")
            return None

    def _motion_from_node(self, node: Optional[dict]) -> bool:
        """Extrait l'état mouvement (CC 48 Binary Sensor) depuis l'objet node. MultiSensor7."""
        if not node:
            return False
        values = node.get("values") or {}
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict) and v.get("commandClass") == CC_BINARY_SENSOR:
                    val = v.get("value") if "value" in v else v.get("newValue")
                    if val is not None:
                        return bool(val)
            return False
        # format dict: "48-0-currentValue" ou équivalent
        for k, v in values.items():
            if not isinstance(v, dict):
                continue
            if str(v.get("commandClass")) == str(CC_BINARY_SENSOR) or (isinstance(k, str) and k.startswith("48-")):
                val = v.get("value") if "value" in v else v.get("newValue")
                if val is not None:
                    return bool(val)
        return False

    async def get_motion_state(self, node_id: int) -> bool:
        """Lit l'état mouvement du nœud (MultiSensor7, CC 48 Binary Sensor)."""
        node = await self.get_node(node_id)
        return self._motion_from_node(node)

    def _is_aeotec_multisensor7(self, node: Optional[dict]) -> bool:
        """Vérifie si le nœud est un Aeotec MultiSensor 7 (ZWA024)."""
        if not node:
            return False
        mid = node.get("manufacturerId") or node.get("manufacturer_id")
        pt = node.get("productType") or node.get("product_type")
        pid = node.get("productId") or node.get("product_id")
        if mid is not None and pt is not None and pid is not None:
            if int(mid) == AEOTEC_MANUFACTURER_ID and int(pt) == AEOTEC_MULTISENSOR7_PRODUCT_TYPE and int(pid) == AEOTEC_MULTISENSOR7_PRODUCT_ID:
                return True
        # Certaines APIs exposent sous deviceConfig
        dev = node.get("deviceConfig") or node.get("device_config") or {}
        if dev:
            mid = dev.get("manufacturerId") or dev.get("manufacturer_id")
            pt = dev.get("productType") or dev.get("product_type")
            pid = dev.get("productId") or dev.get("product_id")
            if mid is not None and pt is not None and pid is not None:
                if int(mid) == AEOTEC_MANUFACTURER_ID and int(pt) == AEOTEC_MULTISENSOR7_PRODUCT_TYPE and int(pid) == AEOTEC_MULTISENSOR7_PRODUCT_ID:
                    return True
        return False

    def _float_from_value(self, v: Any) -> Optional[float]:
        """Extrait un float depuis une valeur (value ou newValue)."""
        if v is None:
            return None
        if isinstance(v, dict):
            v = v.get("value") or v.get("newValue")
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _sensor_values_from_node(self, node: Optional[dict]) -> Dict[str, Any]:
        """
        Extrait les valeurs capteur depuis un nœud (MultiSensor 7 : CC 48, 49, 128).
        Retourne motion, temperature_c, humidity, illuminance_lux, ultraviolet, battery_percent.
        """
        out: Dict[str, Any] = {
            "motion": False,
            "temperature_c": None,
            "humidity": None,
            "illuminance_lux": None,
            "ultraviolet": None,
            "battery_percent": None,
        }
        if not node:
            return out
        values = node.get("values") or {}
        if isinstance(values, list):
            for v in values:
                if not isinstance(v, dict):
                    continue
                cc = v.get("commandClass")
                prop = v.get("property") or v.get("propertyKey") or ""
                val = v.get("value") if "value" in v else v.get("newValue")
                if cc == CC_BINARY_SENSOR:
                    if val is not None:
                        out["motion"] = bool(val)
                elif cc == CC_MULTILEVEL_SENSOR:
                    f = self._float_from_value(val) if val is not None else self._float_from_value(v)
                    if f is None:
                        continue
                    if "Air temperature" in str(prop) or prop == "Air temperature":
                        out["temperature_c"] = round(f, 1)
                    elif "Humidity" in str(prop) or prop == "Humidity":
                        out["humidity"] = round(f, 1)
                    elif "Illuminance" in str(prop) or prop == "Illuminance":
                        out["illuminance_lux"] = int(round(f))
                    elif "Ultraviolet" in str(prop) or prop == "Ultraviolet":
                        out["ultraviolet"] = round(f, 1)
                elif cc == CC_BATTERY and (prop == "level" or "level" in str(prop)):
                    if val is not None:
                        try:
                            out["battery_percent"] = min(100, max(0, int(val)))
                        except (TypeError, ValueError):
                            pass
            return out
        # format dict: "5-49-0-Air temperature" ou "48-0-currentValue"
        for k, v in values.items():
            if not isinstance(v, dict):
                continue
            kstr = str(k)
            if str(CC_BINARY_SENSOR) in kstr or kstr.startswith("48-"):
                val = v.get("value") if "value" in v else v.get("newValue")
                if val is not None:
                    out["motion"] = bool(val)
            elif str(CC_MULTILEVEL_SENSOR) in kstr or kstr.startswith("49-"):
                f = self._float_from_value(v)
                if f is None:
                    continue
                if "Air temperature" in kstr or "Air temperature" in str(v.get("property", "")):
                    out["temperature_c"] = round(f, 1)
                elif "Humidity" in kstr or "Humidity" in str(v.get("property", "")):
                    out["humidity"] = round(f, 1)
                elif "Illuminance" in kstr or "Illuminance" in str(v.get("property", "")):
                    out["illuminance_lux"] = int(round(f))
                elif "Ultraviolet" in kstr or "Ultraviolet" in str(v.get("property", "")):
                    out["ultraviolet"] = round(f, 1)
            elif str(CC_BATTERY) in kstr or kstr.startswith("128-"):
                if "level" in kstr or v.get("property") == "level":
                    val = v.get("value") if "value" in v else v.get("newValue")
                    if val is not None:
                        try:
                            out["battery_percent"] = min(100, max(0, int(val)))
                        except (TypeError, ValueError):
                            pass
        return out

    async def get_sensor_data(self, node_id: int) -> Dict[str, Any]:
        """
        Lit toutes les valeurs capteur du nœud (mouvement, température, humidité, luminosité, UV, batterie).
        Compatible Aeotec MultiSensor 7 (ZWA024). Retourne aussi device_type si reconnu.
        """
        node = await self.get_node(node_id)
        data = self._sensor_values_from_node(node)
        data["node_id"] = node_id
        if node and self._is_aeotec_multisensor7(node):
            data["device_type"] = "aeotec_multisensor7"
            data["device_name"] = AEOTEC_MULTISENSOR7_NAME
            data["device_model"] = AEOTEC_MULTISENSOR7_MODEL
        else:
            data["device_type"] = None
            data["device_name"] = None
            data["device_model"] = None
        return data

    async def turn_on(self, node_id: int, transition_duration: Optional[str] = None) -> Any:
        """Allume le nœud (targetValue = ON_LEVEL_FULL). Compatible 0-99 (ex. ABUS node 3)."""
        return await self._set_value(node_id, ON_LEVEL_FULL, transition_duration=transition_duration)

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
        Règle l'intensité 0-100. Mappe vers targetValue 0-99 (CC 38).
        Compatible lampe ABUS (currentValue/targetValue min 0, max 99).
        """
        if brightness <= 0:
            return await self.turn_off(node_id)
        level = min(99, max(1, brightness))
        return await self._set_value(
            node_id, level, transition_duration=transition_duration
        )

    def _current_value_from_node(self, node: Optional[dict]) -> Optional[int]:
        """Extrait currentValue (CC 38) depuis l'objet node (values[] ou values{})."""
        if not node:
            return None
        values = node.get("values")
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict) and v.get("commandClass") == CC_MULTILEVEL_SWITCH and v.get("property") == PROP_CURRENT_VALUE:
                    val = v.get("value") if "value" in v else v.get("newValue")
                    if val is not None:
                        return int(val)
        elif isinstance(values, dict):
            for k, v in values.items():
                if "currentValue" in str(k) and isinstance(v, dict):
                    val = v.get("value") if "value" in v else v.get("newValue")
                    if val is not None:
                        return int(val)
        return None

    async def _get_current_value_via_ws(self, node_id: int) -> Optional[int]:
        """
        Lit currentValue via WebSocket (zwave-js-server). Après start_listening,
        le résultat contient result.state.nodes ; on en extrait la valeur du nœud.
        """
        if not self.ws_url:
            return None
        try:
            import aiohttp
        except ImportError:
            return None
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.ws_connect(self.ws_url) as ws:
                    msg = await ws.receive()
                    if msg.type != aiohttp.WSMsgType.TEXT:
                        return None
                    data = json.loads(msg.data)
                    if data.get("type") != "version":
                        return None
                    schema = data.get("maxSchemaVersion", 0)
                    await ws.send_str(json.dumps({
                        "messageId": "init",
                        "command": "initialize",
                        "schemaVersion": min(schema, 31),
                    }))
                    while True:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5)
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        data = json.loads(msg.data)
                        if data.get("type") == "result" and data.get("messageId") == "init":
                            break
                    await ws.send_str(json.dumps({
                        "messageId": "listen",
                        "command": "start_listening",
                    }))
                    while True:
                        msg = await asyncio.wait_for(ws.receive(), timeout=15)
                        if msg.type != aiohttp.WSMsgType.TEXT:
                            continue
                        data = json.loads(msg.data)
                        if data.get("type") == "result" and data.get("messageId") == "listen":
                            result = data.get("result") or {}
                            state = result.get("state") or {}
                            nodes = state.get("nodes") or state.get("controller", {}).get("nodes") or []
                            if not nodes and isinstance(state.get("driver"), dict):
                                nodes = state.get("driver", {}).get("nodes") or []
                            for n in nodes:
                                if not isinstance(n, dict):
                                    continue
                                nid = n.get("nodeId") or n.get("id")
                                if nid == node_id:
                                    val = self._current_value_from_node(n)
                                    if val is not None:
                                        self._cache_current_value[node_id] = val
                                        return val
                            break
        except Exception as e:
            logger.debug("_get_current_value_via_ws node %s: %s", node_id, e)
        return None

    async def _get_node_via_http(self, node_id: int) -> Optional[dict]:
        """Tente de récupérer le nœud via API HTTP (évite les timeouts Socket.IO)."""
        try:
            import aiohttp
        except ImportError:
            return None
        for path in (f"/api/nodes/{node_id}", f"/nodes/{node_id}"):
            try:
                url = self.base_url.rstrip("/") + path
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                        if resp.status != 200:
                            continue
                        content_type = (resp.headers.get("Content-Type") or "").lower()
                        if "application/json" not in content_type:
                            continue
                        data = await resp.json()
                        if isinstance(data, dict) and (data.get("values") is not None or "nodeId" in str(data)):
                            return data
                        if isinstance(data, list):
                            for n in data:
                                if isinstance(n, dict) and (n.get("id") == node_id or n.get("nodeId") == node_id):
                                    return n
                            continue
                        if isinstance(data, dict) and data.get("nodes"):
                            for n in data["nodes"]:
                                if isinstance(n, dict) and (n.get("id") == node_id or n.get("nodeId") == node_id):
                                    return n
                            continue
                        return data if isinstance(data, dict) else None
            except Exception as e:
                logger.debug("_get_node_via_http %s %s: %s", path, node_id, e)
        return None

    async def _get_current_value(self, node_id: int) -> Tuple[Optional[int], bool]:
        """Lit currentValue (CC 38). Ordre : WebSocket → HTTP → Socket.IO getValue/getNode → cache."""
        # 1) WebSocket (même canal que setValue, fiable)
        val = await self._get_current_value_via_ws(node_id)
        if val is not None:
            return (val, False)
        # 2) API HTTP si disponible
        node = await self._get_node_via_http(node_id)
        if node:
            val = self._current_value_from_node(node)
            if val is not None:
                self._cache_current_value[node_id] = val
                return (val, False)
        # 3) Socket getValue (timeout court)
        value_id = self._value_id(node_id, PROP_CURRENT_VALUE)
        try:
            val = await asyncio.wait_for(
                self._call_api("getValue", value_id),
                timeout=min(5, self.timeout),
            )
            if val is not None:
                v = int(val["value"]) if isinstance(val, dict) and "value" in val else int(val)
                self._cache_current_value[node_id] = v
                return (v, False)
        except (asyncio.TimeoutError, Exception) as e:
            logger.debug("getValue timeout/error for node %s: %s", node_id, e)
        # 4) Socket getNode
        try:
            node = await self._call_api("getNode", node_id)
            val = self._current_value_from_node(node)
            if val is not None:
                self._cache_current_value[node_id] = val
                return (val, False)
        except Exception as e2:
            logger.debug("getNode for node %s: %s", node_id, e2)
        # 5) Cache (dernier état écrit)
        cached = self._cache_current_value.get(node_id)
        return (cached, cached is not None)

    async def get_state_and_brightness(self, node_id: int) -> Tuple[bool, int, bool]:
        """Retourne (state, brightness 0-100, from_cache). Une seule lecture pour les deux."""
        val, from_cache = await self._get_current_value(node_id)
        if val is None:
            return (False, 0, False)
        brightness = 100 if val == 255 else min(100, max(0, val))
        return (val > 0, brightness, from_cache)

    async def get_state(self, node_id: int) -> bool:
        """État ON/OFF (currentValue > 0)."""
        val, _ = await self._get_current_value(node_id)
        return (val or 0) > 0

    async def get_brightness(self, node_id: int) -> int:
        """Valeur currentValue en 0-100."""
        val, _ = await self._get_current_value(node_id)
        if val is None:
            return 0
        if val == 255:
            return 100
        return min(100, max(0, val))

    async def interview_node(self, node_id: int) -> Any:
        """Lance l'interview d'un nœud."""
        return await self._call_api("refreshInfo", node_id)

    async def close(self) -> None:
        """Ferme la connexion Socket.IO."""
        if self._sio and self._sio.connected:
            await self._sio.disconnect()
            self._sio = None
