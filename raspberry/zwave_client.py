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
import time
from typing import Any, Dict, List, Optional, Tuple

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
        # Cache nœud (node_id -> (payload, timestamp)) pour éviter timeouts répétés sur capteurs lents
        self._cache_node: Dict[int, Tuple[dict, float]] = {}
        self._cache_node_ttl_sec: float = 90.0
        # Cache liste complète des nœuds (TTL long) quand getNodes réussit
        self._cache_nodes_list: Optional[Tuple[list, float]] = None
        self._cache_nodes_list_ttl_sec: float = 300.0
        # Cache données capteur (node_id -> (data dict, timestamp)) pour éviter réponses vides après timeout
        self._cache_sensor_data: Dict[int, Tuple[Dict[str, Any], float]] = {}
        self._cache_sensor_data_ttl_sec: float = 90.0

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

    def _binary_sensor_value_id(self, node_id: int, endpoint: int = 0) -> dict:
        """ValueId pour CC 48 Binary Sensor (mouvement)."""
        return {
            "nodeId": node_id,
            "commandClass": CC_BINARY_SENSOR,
            "endpoint": endpoint,
            "property": "currentValue",
        }

    def _multilevel_sensor_value_id(self, node_id: int, property_name: str, endpoint: int = 0) -> dict:
        """ValueId pour CC 49 Multilevel Sensor (temp, illuminance, humidity, uv)."""
        return {
            "nodeId": node_id,
            "commandClass": CC_MULTILEVEL_SENSOR,
            "endpoint": endpoint,
            "property": property_name,
        }

    def _battery_value_id(self, node_id: int, endpoint: int = 0) -> dict:
        """ValueId pour CC 128 Battery (level)."""
        return {
            "nodeId": node_id,
            "commandClass": CC_BATTERY,
            "endpoint": endpoint,
            "property": "level",
        }

    async def _get_motion_via_getvalue(self, node_id: int) -> Optional[bool]:
        """
        Lit uniquement le mouvement via getValue(CC 48). Plus rapide que getNode.
        Essaie currentValue (endpoint 0 puis 1). Retourne None si timeout/erreur.
        """
        for endpoint in (0, 1):
            try:
                vid = self._binary_sensor_value_id(node_id, endpoint)
                result = await asyncio.wait_for(
                    self._call_api("getValue", vid),
                    timeout=8.0,
                )
                if result is None:
                    continue
                val = result.get("value") if isinstance(result, dict) else result
                if val is not None:
                    return bool(val)
            except (asyncio.TimeoutError, Exception):
                continue
        return None

    async def _get_sensor_values_via_getvalue(self, node_id: int) -> Dict[str, Any]:
        """
        Lit toutes les valeurs capteur via getValue (CC 48, 49, 128).
        Utilise le cache du driver (pas de réveil du nœud) — rapide pour capteurs sur pile.
        Retourne le même format que _sensor_values_from_node (motion, temperature_c, etc.).
        """
        out: Dict[str, Any] = {
            "motion": False,
            "temperature_c": None,
            "humidity": None,
            "illuminance_lux": None,
            "ultraviolet": None,
            "battery_percent": None,
        }
        timeout_per_call = 10.0

        async def get_one(vid: dict, kind: str) -> Tuple[str, Any]:
            try:
                result = await asyncio.wait_for(
                    self._call_api("getValue", vid),
                    timeout=timeout_per_call,
                )
                if result is None:
                    return (kind, None)
                if isinstance(result, dict):
                    val = result.get("value") if "value" in result else result.get("newValue") or result.get("currentValue")
                else:
                    val = result
                if val is None:
                    return (kind, None)
                if kind == "motion":
                    return (kind, bool(val))
                if kind == "battery_percent":
                    return (kind, min(100, max(0, int(val))))
                f = self._float_from_value(val) if not isinstance(val, (int, float)) else float(val)
                if f is None:
                    return (kind, None)
                if kind == "temperature_c":
                    return (kind, round(f, 1))
                if kind == "illuminance_lux":
                    return (kind, int(round(f)))
                if kind in ("humidity", "ultraviolet"):
                    return (kind, round(f, 1))
                return (kind, None)
            except (asyncio.TimeoutError, Exception):
                return (kind, None)

        # Mouvement (CC 48)
        for ep in (0, 1):
            vid = self._binary_sensor_value_id(node_id, ep)
            _, v = await get_one(vid, "motion")
            if v is not None:
                out["motion"] = v
                break

        # CC 49 + batterie en parallèle
        value_ids: List[Tuple[dict, str]] = [
            (self._multilevel_sensor_value_id(node_id, "Air temperature"), "temperature_c"),
            (self._multilevel_sensor_value_id(node_id, "Illuminance"), "illuminance_lux"),
            (self._multilevel_sensor_value_id(node_id, "Humidity"), "humidity"),
            (self._multilevel_sensor_value_id(node_id, "Ultraviolet"), "ultraviolet"),
            (self._battery_value_id(node_id), "battery_percent"),
        ]
        tasks = [get_one(vid, kind) for vid, kind in value_ids]
        results = await asyncio.gather(*tasks)
        for (_, kind), (_, val) in zip(value_ids, results):
            if val is not None:
                out[kind] = val

        return out

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

    async def _get_nodes_via_http(self) -> list:
        """Tente de récupérer la liste des nœuds via API HTTP (Z-Wave JS UI expose parfois /api/nodes)."""
        try:
            import aiohttp
        except ImportError:
            return []
        for path in ("/api/nodes", "/nodes"):
            try:
                url = self.base_url.rstrip("/") + path
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status != 200:
                            continue
                        content_type = (resp.headers.get("Content-Type") or "").lower()
                        if "application/json" not in content_type:
                            continue
                        data = await resp.json()
                        if isinstance(data, list):
                            return [n for n in data if isinstance(n, dict)]
                        if isinstance(data, dict):
                            nodes = data.get("nodes") or data.get("result") or data.get("data")
                            if isinstance(nodes, list):
                                return [n for n in nodes if isinstance(n, dict)]
            except Exception as e:
                logger.debug("_get_nodes_via_http %s: %s", path, e)
        return []

    def _get_nodes_from_caches(self) -> list:
        """Liste construite depuis le cache liste (si valide) ou depuis les nœuds déjà lus (_cache_node)."""
        now = time.monotonic()
        if self._cache_nodes_list:
            lst, ts = self._cache_nodes_list
            if now - ts <= self._cache_nodes_list_ttl_sec and lst:
                return lst
            self._cache_nodes_list = None
        # Sinon : retourner les nœuds déjà lus (get_node / sensor) encore en cache
        out = []
        to_del = []
        for node_id, (payload, ts) in list(self._cache_node.items()):
            if now - ts > self._cache_node_ttl_sec:
                to_del.append(node_id)
                continue
            if isinstance(payload, dict):
                out.append(payload)
        for k in to_del:
            del self._cache_node[k]
        return out

    async def get_nodes(self) -> list:
        """Liste des nœuds Z-Wave. HTTP puis Socket.IO ; si tout timeout, retourne le cache (liste ou nœuds déjà lus)."""
        nodes = await self._get_nodes_via_http()
        if nodes:
            self._cache_nodes_list = (nodes, time.monotonic())
            return nodes
        for method in ("getNodes", "getAllNodes"):
            try:
                result = await asyncio.wait_for(
                    self._call_api(method),
                    timeout=min(25.0, self.timeout + 5),
                )
                if result and isinstance(result, list):
                    self._cache_nodes_list = (result, time.monotonic())
                    return result
                if isinstance(result, dict):
                    nodes = result.get("nodes") or result.get("result") or result.get("data")
                    if isinstance(nodes, list) and nodes:
                        self._cache_nodes_list = (nodes, time.monotonic())
                        return nodes
                    logger.debug("get_nodes %s: dict sans nodes/result/data: %s", method, list(result.keys())[:10])
                elif result is not None:
                    logger.debug("get_nodes %s: type inattendu %s", method, type(result).__name__)
            except asyncio.TimeoutError:
                logger.debug("get_nodes %s: timeout", method)
            except Exception as e1:
                logger.debug("get_nodes %s: %s", method, e1)
        # Fallback: getNodeCount puis getNode pour chaque id
        try:
            count = await self._call_api("getNodeCount") or 0
            count = int(count) if count is not None else 0
            nodes = []
            for i in range(1, min(count + 1, 256)):
                try:
                    n = await asyncio.wait_for(self._call_api("getNode", i), timeout=10.0)
                    if n and isinstance(n, dict):
                        nodes.append(n)
                except (asyncio.TimeoutError, Exception):
                    continue
            if nodes:
                self._cache_nodes_list = (nodes, time.monotonic())
                return nodes
        except Exception as e2:
            logger.debug("get_nodes fallback: %s", e2)
        # Tout a timeout : tenter HTTP pour node_id 1-10 en parallèle (au cas où l'UI expose /api/nodes/<id>)
        async def _try_http(nid: int) -> Optional[dict]:
            return await self._get_node_via_http(nid)
        try:
            tasks = [asyncio.wait_for(_try_http(nid), timeout=4.0) for nid in range(1, 11)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            now = time.monotonic()
            for nid, r in zip(range(1, 11), results):
                if isinstance(r, dict):
                    self._cache_node[nid] = (r, now)
        except (asyncio.TimeoutError, Exception):
            pass
        return self._get_nodes_from_caches()

    def _get_cached_node(self, node_id: int) -> Optional[dict]:
        """Retourne le nœud en cache s'il est encore valide (TTL)."""
        entry = self._cache_node.get(node_id)
        if not entry:
            return None
        payload, ts = entry
        if time.monotonic() - ts > self._cache_node_ttl_sec:
            del self._cache_node[node_id]
            return None
        return payload

    async def get_node(self, node_id: int) -> Optional[dict]:
        """Détails d'un nœud. Tente HTTP puis Socket.IO ; en timeout retourne le cache si disponible."""
        node = await self._get_node_via_http(node_id)
        if node:
            self._cache_node[node_id] = (node, time.monotonic())
            return node
        try:
            # Timeout 25s pour réseaux Z-Wave lents (capteurs batterie, réveil)
            node = await asyncio.wait_for(
                self._call_api("getNode", node_id),
                timeout=25.0,
            )
            if node:
                self._cache_node[node_id] = (node, time.monotonic())
            return node
        except asyncio.TimeoutError:
            cached = self._get_cached_node(node_id)
            if cached:
                logger.debug("get_node %s: timeout (lecture Z-Wave lente), retour cache", node_id)
                return cached
            logger.warning("get_node %s: timeout (lecture Z-Wave lente)", node_id)
            return None
        except Exception as e:
            logger.error(f"get_node {node_id}: {e}")
            cached = self._get_cached_node(node_id)
            if cached:
                logger.debug("get_node %s: erreur, retour cache", node_id)
                return cached
            return None

    def _bool_from_value_dict(self, v: dict) -> Optional[bool]:
        """Extrait un booléen depuis un objet valeur (value, newValue ou currentValue)."""
        val = v.get("value") if "value" in v else v.get("newValue") or v.get("currentValue")
        if val is None:
            return None
        return bool(val)

    def _motion_from_node(self, node: Optional[dict]) -> bool:
        """Extrait l'état mouvement (CC 48 Binary Sensor) depuis l'objet node. MultiSensor7."""
        if not node:
            return False
        values = node.get("values") or {}
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict) and v.get("commandClass") == CC_BINARY_SENSOR:
                    b = self._bool_from_value_dict(v)
                    if b is not None:
                        return b
            return False
        # format dict: "48-0-currentValue" ou "5-48-0-currentValue"
        for k, v in values.items():
            if not isinstance(v, dict):
                continue
            if str(v.get("commandClass")) == str(CC_BINARY_SENSOR) or (isinstance(k, str) and "48-" in k):
                b = self._bool_from_value_dict(v)
                if b is not None:
                    return b
        return False

    async def get_motion_state(self, node_id: int) -> bool:
        """Lit l'état mouvement du nœud (MultiSensor7, CC 48 Binary Sensor)."""
        node = await self.get_node(node_id)
        return self._motion_from_node(node)

    def _node_has_command_class(self, node: Optional[dict], cc: int) -> bool:
        """Vérifie si le nœud expose la command class donnée (ex. 38 = Multilevel Switch, 48 = Binary Sensor)."""
        if not node:
            return False
        values = node.get("values") or {}
        cc_str = str(cc)
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict) and str(v.get("commandClass")) == cc_str:
                    return True
            return False
        for k, v in values.items():
            if isinstance(v, dict) and str(v.get("commandClass")) == cc_str:
                return True
            if isinstance(k, str) and (k.startswith(f"{cc}-") or f"-{cc}-" in k):
                return True
        return False

    def _is_sensor_node(self, node: Optional[dict]) -> bool:
        """True si le nœud est un capteur (MultiSensor 7 ou Binary Sensor sans Multilevel Switch)."""
        if not node:
            return False
        if self._is_aeotec_multisensor7(node):
            return True
        has_cc38 = self._node_has_command_class(node, CC_MULTILEVEL_SWITCH)
        has_cc48 = self._node_has_command_class(node, CC_BINARY_SENSOR)
        return has_cc48 and not has_cc38

    async def is_sensor_node(self, node_id: int) -> bool:
        """True si le nœud est un capteur (utilise le cache ou HTTP pour éviter getNode lent)."""
        node = self._get_cached_node(node_id)
        if node is not None:
            return self._is_sensor_node(node)
        node = await self._get_node_via_http(node_id)
        if node is not None:
            self._cache_node[node_id] = (node, time.monotonic())
            return self._is_sensor_node(node)
        return False

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
                if cc == CC_BINARY_SENSOR:
                    b = self._bool_from_value_dict(v)
                    if b is not None:
                        out["motion"] = b
                    continue
                elif cc == CC_MULTILEVEL_SENSOR:
                    val = v.get("value") if "value" in v else v.get("newValue")
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
                    val = v.get("value") if "value" in v else v.get("newValue")
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
                b = self._bool_from_value_dict(v)
                if b is not None:
                    out["motion"] = b
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

    def _sensor_data_has_values(self, data: Dict[str, Any]) -> bool:
        """True si les données capteur contiennent au moins une valeur lue (pas tout vide)."""
        if data.get("motion"):
            return True
        if data.get("temperature_c") is not None:
            return True
        if data.get("humidity") is not None:
            return True
        if data.get("illuminance_lux") is not None:
            return True
        if data.get("ultraviolet") is not None:
            return True
        if data.get("battery_percent") is not None:
            return True
        return False

    async def get_sensor_data(self, node_id: int) -> Dict[str, Any]:
        """
        Lit toutes les valeurs capteur du nœud (mouvement, température, humidité, luminosité, UV, batterie).
        Compatible Aeotec MultiSensor 7 (ZWA024). Retourne aussi device_type si reconnu.
        Ordre : HTTP get_node (rapide) → si échec, getValue par valeur (cache driver, rapide) → sinon get_node Socket → cache.
        """
        # 1) Tenter d'abord le nœud via HTTP (souvent plus rapide, pas de réveil)
        node = await self._get_node_via_http(node_id)
        if node is not None:
            self._cache_node[node_id] = (node, time.monotonic())
            data = self._sensor_values_from_node(node)
            data["node_id"] = node_id
            if self._is_aeotec_multisensor7(node):
                data["device_type"] = "aeotec_multisensor7"
                data["device_name"] = AEOTEC_MULTISENSOR7_NAME
                data["device_model"] = AEOTEC_MULTISENSOR7_MODEL
            else:
                data["device_type"] = None
                data["device_name"] = None
                data["device_model"] = None
            if self._sensor_data_has_values(data):
                self._cache_sensor_data[node_id] = (dict(data), time.monotonic())
            return data

        # 2) Pas de node HTTP : lire chaque valeur via getValue (cache du driver, sans réveil du nœud)
        data = await self._get_sensor_values_via_getvalue(node_id)
        data["node_id"] = node_id
        if self._sensor_data_has_values(data):
            data["device_type"] = "aeotec_multisensor7"
            data["device_name"] = AEOTEC_MULTISENSOR7_NAME
            data["device_model"] = AEOTEC_MULTISENSOR7_MODEL
            self._cache_sensor_data[node_id] = (dict(data), time.monotonic())
            return data

        # 3) Fallback : get_node via Socket (peut être lent / timeout sur capteur pile)
        node = await self.get_node(node_id)
        data = self._sensor_values_from_node(node)
        data["node_id"] = node_id
        if not data["motion"] and node is None:
            motion_direct = await self._get_motion_via_getvalue(node_id)
            if motion_direct is not None:
                data["motion"] = motion_direct
        if node and self._is_aeotec_multisensor7(node):
            data["device_type"] = "aeotec_multisensor7"
            data["device_name"] = AEOTEC_MULTISENSOR7_NAME
            data["device_model"] = AEOTEC_MULTISENSOR7_MODEL
        else:
            data["device_type"] = None
            data["device_name"] = None
            data["device_model"] = None
        if self._sensor_data_has_values(data):
            self._cache_sensor_data[node_id] = (dict(data), time.monotonic())
            return data

        # 4) Rien lu : retourner le cache si valide, sinon unknown
        now = time.monotonic()
        entry = self._cache_sensor_data.get(node_id)
        if entry:
            cached_data, ts = entry
            if now - ts <= self._cache_sensor_data_ttl_sec:
                out = dict(cached_data)
                out["cached"] = True
                out["node_id"] = node_id
                return out
            self._cache_sensor_data.pop(node_id, None)
        data["unknown"] = True
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
        def _int_from_val(v: Any) -> Optional[int]:
            if v is None:
                return None
            if isinstance(v, dict):
                v = v.get("value") or v.get("newValue") or v.get("currentValue")
            if v is None:
                return None
            try:
                return int(v)
            except (TypeError, ValueError):
                return None
        values = node.get("values")
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict) and v.get("commandClass") == CC_MULTILEVEL_SWITCH and v.get("property") == PROP_CURRENT_VALUE:
                    val = _int_from_val(v)
                    if val is not None:
                        return val
        elif isinstance(values, dict):
            for k, v in values.items():
                if "currentValue" in str(k) and isinstance(v, dict):
                    val = _int_from_val(v)
                    if val is not None:
                        return val
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

    def _int_from_getvalue_response(self, val: Any) -> Optional[int]:
        """Extrait un int depuis la réponse getValue (dict avec value/newValue/currentValue ou scalaire)."""
        if val is None:
            return None
        if isinstance(val, dict):
            v = val.get("value") if "value" in val else val.get("newValue") or val.get("currentValue")
            if v is None:
                return None
            try:
                return int(v)
            except (TypeError, ValueError):
                return None
        try:
            return int(val)
        except (TypeError, ValueError):
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
        # 3) Socket getValue (timeout 15s pour réseaux lents)
        value_id = self._value_id(node_id, PROP_CURRENT_VALUE)
        for vid in (value_id, self._value_id_str(node_id, PROP_CURRENT_VALUE)):
            try:
                result = await asyncio.wait_for(
                    self._call_api("getValue", vid),
                    timeout=15.0,
                )
                v = self._int_from_getvalue_response(result)
                if v is not None:
                    self._cache_current_value[node_id] = v
                    return (v, False)
            except (asyncio.TimeoutError, Exception) as e:
                logger.debug("getValue timeout/error for node %s: %s", node_id, e)
        # 4) Socket getNode (timeout 25s)
        try:
            node = await asyncio.wait_for(
                self._call_api("getNode", node_id),
                timeout=25.0,
            )
            val = self._current_value_from_node(node)
            if val is not None:
                self._cache_current_value[node_id] = val
                return (val, False)
        except (asyncio.TimeoutError, Exception) as e2:
            logger.debug("getNode for node %s: %s", node_id, e2)
        # 5) Cache (dernier état connu : écrit ou lecture précédente)
        cached = self._cache_current_value.get(node_id)
        return (cached, cached is not None)

    async def get_state_and_brightness(self, node_id: int) -> Tuple[bool, int, bool, bool]:
        """
        Retourne (state, brightness 0-100, from_cache, unknown).
        unknown=True quand la lecture a échoué et pas de cache (état réel inconnu, ne pas afficher OFF).
        """
        val, from_cache = await self._get_current_value(node_id)
        if val is None:
            # Aucune valeur lue et pas de cache → état inconnu (lampe peut être ON ou OFF)
            return (False, 0, False, True)
        brightness = 100 if val == 255 else min(100, max(0, val))
        return (val > 0, brightness, from_cache, False)

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
