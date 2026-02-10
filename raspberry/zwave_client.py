"""
Client Z-Wave : WebSocket (zwave-js-server, port 3000) en priorité, puis Socket.IO (Z-Wave JS UI, 8091).

- Port 3000 : WebSocket zwave-js-server (commandes setValue).
- Port 8091 : Socket.IO Z-Wave JS UI (lectures getValue / getNode).

Reconnaissance des appareils (nom, modèle) : zwave_constants.device_info_from_node.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import socketio

from zwave_cache import SimpleCache
from zwave_constants import (
    CommandClass,
    MultilevelSensorType,
    ON_LEVEL_FULL,
    PROP_CURRENT_VALUE,
    PROP_TARGET_VALUE,
    device_info_from_node,
)

logger = logging.getLogger(__name__)


def extract_zwave_value(payload: Any) -> Optional[Any]:
    """
    Extrait la valeur primitive d'une réponse Z-Wave (getValue, node.values, etc.).
    Accepte : {value}, {newValue}, {currentValue}, ou valeur directe (scalaire / list).
    """
    if payload is None:
        return None
    if isinstance(payload, dict):
        v = payload.get("value") if "value" in payload else payload.get("newValue") or payload.get("currentValue")
        return v
    return payload


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
        self._cache_node = SimpleCache[int, dict](ttl_sec=90.0)
        self._cache_nodes_list: Optional[Tuple[list, float]] = None
        self._cache_nodes_list_ttl_sec: float = 300.0
        self._cache_sensor_data = SimpleCache[int, Dict[str, Any]](ttl_sec=90.0)

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
                # Limiter à 12s pour rester sous le timeout backend (60s) quand on enchaîne HTTP + getValue capteur
                wait = min(12, self.timeout)
                await self._sio.connect(
                    self.base_url,
                    wait_timeout=wait,
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
            "commandClass": CommandClass.MULTILEVEL_SWITCH,
            "endpoint": 0,
            "property": property_name,
        }

    def _value_id_str(self, node_id: int, property_name: str = PROP_TARGET_VALUE) -> str:
        """Format string du valueId (ex. 3-38-0-targetValue) utilisé par Z-Wave JS UI."""
        return f"{node_id}-{CommandClass.MULTILEVEL_SWITCH}-0-{property_name}"

    def _binary_sensor_value_id(self, node_id: int, endpoint: int = 0) -> dict:
        """ValueId pour CC 48 Binary Sensor (mouvement)."""
        return {
            "nodeId": node_id,
            "commandClass": CommandClass.SENSOR_BINARY,
            "endpoint": endpoint,
            "property": "currentValue",
        }

    def _multilevel_sensor_value_id(self, node_id: int, property_name: str, endpoint: int = 0) -> dict:
        """ValueId pour CC 49 Multilevel Sensor (temp, illuminance, humidity, uv)."""
        return {
            "nodeId": node_id,
            "commandClass": CommandClass.SENSOR_MULTILEVEL,
            "endpoint": endpoint,
            "property": property_name,
        }

    def _multilevel_sensor_value_id_numeric(self, node_id: int, property_id: int, endpoint: int = 0) -> dict:
        """ValueId CC 49 avec property numérique (compatible zwave-js)."""
        return {
            "nodeId": node_id,
            "commandClass": CommandClass.SENSOR_MULTILEVEL,
            "endpoint": endpoint,
            "property": property_id,
        }

    def _battery_value_id(self, node_id: int, endpoint: int = 0) -> dict:
        """ValueId pour CC 128 Battery (level)."""
        return {
            "nodeId": node_id,
            "commandClass": CommandClass.BATTERY,
            "endpoint": endpoint,
            "property": "level",
        }

    async def _get_motion_via_getvalue(self, node_id: int) -> Optional[bool]:
        """
        Lit uniquement le mouvement via getValue(CC 48). Limité à 2 essais (3s chacun)
        pour ne pas dépasser le timeout backend après le fast path.
        """
        for vid in (
            {"nodeId": node_id, "commandClass": CommandClass.SENSOR_BINARY, "endpoint": 0, "property": "Motion"},
            {"nodeId": node_id, "commandClass": CommandClass.SENSOR_BINARY, "endpoint": 0, "property": "currentValue"},
        ):
            result = await self._get_value_one_call(vid, timeout_sec=3.0)
            if result is None:
                continue
            val = extract_zwave_value(result)
            if val is not None:
                return bool(val)
        return None

    async def _get_value_any_format(self, vid, timeout_sec: float = 6.0) -> Optional[Any]:
        """
        Appelle getValue avec valueId (dict ou string). Z-Wave JS UI accepte parfois
        la forme string "nodeId-commandClass-endpoint-property".
        """
        result = None
        for payload in (vid, self._value_id_to_string(vid) if isinstance(vid, dict) else None):
            if payload is None:
                continue
            try:
                result = await asyncio.wait_for(
                    self._call_api("getValue", payload),
                    timeout=timeout_sec,
                )
                if result is not None:
                    break
            except (asyncio.TimeoutError, Exception):
                continue
        return result

    async def _get_value_one_call(self, vid, timeout_sec: float = 4.0) -> Optional[Any]:
        """Un seul getValue : essaie d'abord string (format panneau), puis objet."""
        value_id_str = self._value_id_to_string(vid) if isinstance(vid, dict) else None
        for payload in (value_id_str, vid):
            if payload is None:
                continue
            try:
                result = await asyncio.wait_for(
                    self._call_api("getValue", payload),
                    timeout=timeout_sec,
                )
                if result is not None:
                    return result
            except (asyncio.TimeoutError, Exception):
                continue
        return None

    # ValueId strings exacts comme dans Z-Wave JS UI (ex. [5-48-0-Motion], [5-49-0-Air temperature])
    # CC 48 = Binary Sensor (mouvement), CC 49 = Multilevel Sensor (temp, lux, humidité, UV), CC 128 = Battery
    _SENSOR_VALUE_IDS = [
        ("{node_id}-48-0-Motion", "motion", "bool"),
        ("{node_id}-49-0-Air temperature", "temperature_c", "float"),
        ("{node_id}-49-0-Illuminance", "illuminance_lux", "float"),
        ("{node_id}-49-0-Humidity", "humidity", "float"),
        ("{node_id}-49-0-Ultraviolet", "ultraviolet", "float"),
        ("{node_id}-128-0-level", "battery_percent", "int"),
    ]

    async def _get_sensor_data_simple(self, node_id: int, timeout_per_call: float = 10.0) -> Dict[str, Any]:
        """
        Lecture capteur simple : un getValue par valueId string (format panneau Z-Wave JS UI).
        Pas de timeout court — 10 s par appel pour appareils sur pile (réveil lent).
        """
        out: Dict[str, Any] = {
            "motion": False,
            "temperature_c": None,
            "humidity": None,
            "illuminance_lux": None,
            "ultraviolet": None,
            "battery_percent": None,
        }
        for tpl in self._SENSOR_VALUE_IDS:
            vid_str = tpl[0].format(node_id=node_id)
            kind, typ = tpl[1], tpl[2]
            try:
                result = await asyncio.wait_for(
                    self._call_api("getValue", vid_str),
                    timeout=timeout_per_call,
                )
                val = extract_zwave_value(result)
                if val is None:
                    continue
                if kind == "motion":
                    out["motion"] = bool(val)
                elif kind == "battery_percent":
                    try:
                        out["battery_percent"] = min(100, max(0, int(val)))
                    except (TypeError, ValueError):
                        pass
                else:
                    try:
                        f = float(val)
                        if kind == "temperature_c":
                            out["temperature_c"] = round(f, 1)
                        elif kind == "illuminance_lux":
                            out["illuminance_lux"] = int(round(f))
                        elif kind in ("humidity", "ultraviolet"):
                            out[kind] = round(f, 1)
                    except (TypeError, ValueError):
                        pass
            except asyncio.TimeoutError:
                logger.debug("getValue %s timeout (node %s)", vid_str, node_id)
            except Exception as e:
                logger.debug("getValue %s: %s", vid_str, e)
        return out

    async def _get_sensor_values_via_getvalue_fast(self, node_id: int) -> Dict[str, Any]:
        """Délègue à la lecture simple (valueId strings, timeout 10s/appel)."""
        return await self._get_sensor_data_simple(node_id, timeout_per_call=10.0)

    def _value_id_to_string(self, vid: dict) -> Optional[str]:
        """Construit la forme string du valueId (ex. 5-49-0-Air temperature ou 5-49-0-1)."""
        node_id = vid.get("nodeId")
        cc = vid.get("commandClass")
        ep = vid.get("endpoint", 0)
        prop = vid.get("property")
        if node_id is None or cc is None:
            return None
        return f"{node_id}-{cc}-{ep}-{prop}"

    async def _get_sensor_values_via_getvalue(self, node_id: int) -> Dict[str, Any]:
        """
        Lit toutes les valeurs capteur via getValue (CC 48, 49, 128), en séquentiel pour éviter
        l'erreur Socket.IO « / is not a connected namespace » (appels concurrents non supportés).
        Essaie valueId en objet et en string ; pour CC 49 essaie property nom et property numérique.
        """
        out: Dict[str, Any] = {
            "motion": False,
            "temperature_c": None,
            "humidity": None,
            "illuminance_lux": None,
            "ultraviolet": None,
            "battery_percent": None,
        }
        timeout_per_call = 6.0

        async def get_one(vid, kind: str) -> Optional[Any]:
            try:
                result = await self._get_value_any_format(vid, timeout_sec=timeout_per_call)
                val = extract_zwave_value(result)
                if val is None:
                    return None
                if kind == "motion":
                    return bool(val)
                if kind == "battery_percent":
                    return min(100, max(0, int(val)))
                raw = extract_zwave_value(val) if isinstance(val, dict) else val
                try:
                    f = float(raw)
                except (TypeError, ValueError):
                    return None
                if kind == "temperature_c":
                    return round(f, 1)
                if kind == "illuminance_lux":
                    return int(round(f))
                if kind in ("humidity", "ultraviolet"):
                    return round(f, 1)
                return None
            except (asyncio.TimeoutError, Exception):
                return None

        # Motion (CC 48) : essayer currentValue, Motion, Sensor state (endpoints 0 et 1)
        motion_done = False
        for ep in (0, 1):
            for prop in ("currentValue", "Motion", "Sensor state"):
                vid = {"nodeId": node_id, "commandClass": CommandClass.SENSOR_BINARY, "endpoint": ep, "property": prop}
                v = await get_one(vid, "motion")
                if v is not None:
                    out["motion"] = v
                    motion_done = True
                    break
            if motion_done:
                break
        # CC 49 : essayer property string puis property numérique

        cc49_tries = [
            ("Air temperature", MultilevelSensorType.AIR_TEMPERATURE, "temperature_c"),
            ("Illuminance", MultilevelSensorType.ILLUMINANCE, "illuminance_lux"),
            ("Humidity", MultilevelSensorType.HUMIDITY, "humidity"),
            ("Ultraviolet", MultilevelSensorType.ULTRAVIOLET, "ultraviolet"),
        ]
        for prop_name, prop_id_enum, kind in cc49_tries:
            if out.get(kind) is not None:
                continue
            vid_str = self._multilevel_sensor_value_id(node_id, prop_name)
            v = await get_one(vid_str, kind)
            if v is not None:
                out[kind] = v
                continue
            vid_num = self._multilevel_sensor_value_id_numeric(node_id, int(prop_id_enum))
            v = await get_one(vid_num, kind)
            if v is not None:
                out[kind] = v

        # Batterie (CC 128)
        if out.get("battery_percent") is None:
            v = await get_one(self._battery_value_id(node_id), "battery_percent")
            if v is not None:
                out["battery_percent"] = v

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
                        "commandClass": CommandClass.MULTILEVEL_SWITCH,
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
        for node_id, payload in self._cache_node.items():
            if isinstance(payload, dict):
                out.append(payload)
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
                    self._cache_node.set(nid, r)
        except (asyncio.TimeoutError, Exception):
            pass
        return self._get_nodes_from_caches()

    def _get_cached_node(self, node_id: int) -> Optional[dict]:
        """Retourne le nœud en cache s'il est encore valide (TTL)."""
        return self._cache_node.get(node_id)

    async def get_node(self, node_id: int) -> Optional[dict]:
        """Détails d'un nœud. Tente HTTP puis Socket.IO ; en timeout retourne le cache si disponible."""
        node = await self._get_node_via_http(node_id)
        if node:
            self._cache_node.set(node_id, node)
            return node
        try:
            # Timeout 25s pour réseaux Z-Wave lents (capteurs batterie, réveil)
            node = await asyncio.wait_for(
                self._call_api("getNode", node_id),
                timeout=25.0,
            )
            if node:
                self._cache_node.set(node_id, node)
            return node
        except asyncio.TimeoutError:
            cached = self._cache_node.get(node_id)
            if cached:
                logger.debug("get_node %s: timeout (lecture Z-Wave lente), retour cache", node_id)
                return cached
            logger.warning("get_node %s: timeout (lecture Z-Wave lente)", node_id)
            return None
        except Exception as e:
            logger.error(f"get_node {node_id}: {e}")
            cached = self._cache_node.get(node_id)
            if cached:
                logger.debug("get_node %s: erreur, retour cache", node_id)
                return cached
            return None

    def _motion_from_node(self, node: Optional[dict]) -> bool:
        """Extrait l'état mouvement (CC 48 Binary Sensor) depuis l'objet node."""
        if not node:
            return False
        values = node.get("values") or {}
        cc = CommandClass.SENSOR_BINARY
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict) and v.get("commandClass") == cc:
                    b = extract_zwave_value(v)
                    if b is not None:
                        return bool(b)
            return False
        for k, v in values.items():
            if not isinstance(v, dict):
                continue
            if str(v.get("commandClass")) == str(cc) or (isinstance(k, str) and "48-" in k):
                b = extract_zwave_value(v)
                if b is not None:
                    return bool(b)
        return False

    async def get_motion_state(self, node_id: int) -> bool:
        """Lit l'état mouvement du nœud (MultiSensor7, CC 48 Binary Sensor)."""
        node = await self.get_node(node_id)
        return self._motion_from_node(node)

    def _node_has_command_class(self, node: Optional[dict], cc: Any) -> bool:
        """Vérifie si le nœud expose la command class donnée (IntEnum ou int)."""
        if not node:
            return False
        values = node.get("values") or {}
        cc_val = int(cc) if hasattr(cc, "__int__") else cc
        cc_str = str(cc_val)
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict) and str(v.get("commandClass")) == cc_str:
                    return True
            return False
        for k, v in values.items():
            if isinstance(v, dict) and str(v.get("commandClass")) == cc_str:
                return True
            if isinstance(k, str) and (k.startswith(f"{cc_val}-") or f"-{cc_val}-" in k):
                return True
        return False

    def _is_sensor_node(self, node: Optional[dict]) -> bool:
        """True si le nœud est un capteur (reconnu par le registre ou Binary Sensor sans Multilevel Switch)."""
        if not node:
            return False
        if device_info_from_node(node) is not None:
            return True
        has_cc38 = self._node_has_command_class(node, CommandClass.MULTILEVEL_SWITCH)
        has_cc48 = self._node_has_command_class(node, CommandClass.SENSOR_BINARY)
        return has_cc48 and not has_cc38

    async def is_sensor_node(self, node_id: int) -> bool:
        """True si le nœud est un capteur (utilise le cache ou HTTP pour éviter getNode lent)."""
        node = self._cache_node.get(node_id)
        if node is not None:
            return self._is_sensor_node(node)
        node = await self._get_node_via_http(node_id)
        if node is not None:
            self._cache_node.set(node_id, node)
            return self._is_sensor_node(node)
        return False

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
                prop = v.get("property")
                prop_key = v.get("propertyKey")
                prop_str = str(prop or "") + " " + str(prop_key or "")
                if cc == CommandClass.SENSOR_BINARY:
                    b = extract_zwave_value(v)
                    if b is not None:
                        out["motion"] = bool(b)
                    continue
                elif cc == CommandClass.SENSOR_MULTILEVEL:
                    raw = extract_zwave_value(v)
                    try:
                        f = float(raw)
                    except (TypeError, ValueError):
                        continue
                    if prop == 1 or prop_key == 1 or "Air temperature" in prop_str:
                        out["temperature_c"] = round(f, 1)
                    elif prop == 5 or prop_key == 5 or "Humidity" in prop_str:
                        out["humidity"] = round(f, 1)
                    elif prop == 3 or prop_key == 3 or "Illuminance" in prop_str:
                        out["illuminance_lux"] = int(round(f))
                    elif prop == 27 or prop_key == 27 or "Ultraviolet" in prop_str:
                        out["ultraviolet"] = round(f, 1)
                elif cc == CommandClass.BATTERY and (prop == "level" or prop == 128 or "level" in str(prop)):
                    val = extract_zwave_value(v)
                    if val is not None:
                        try:
                            out["battery_percent"] = min(100, max(0, int(val)))
                        except (TypeError, ValueError):
                            pass
            return out
        # format dict: "5-49-0-Air temperature", "49-0-1", "48-0-currentValue"
        # CC 49 property numeric: 1=Air temperature, 3=Illuminance, 5=Humidity, 27=Ultraviolet
        cc49_property_map = {"1": "temperature_c", "3": "illuminance_lux", "5": "humidity", "27": "ultraviolet"}
        for k, v in values.items():
            if not isinstance(v, dict):
                continue
            kstr = str(k)
            if str(CommandClass.SENSOR_BINARY) in kstr or kstr.startswith("48-"):
                b = extract_zwave_value(v)
                if b is not None:
                    out["motion"] = bool(b)
            elif str(CommandClass.SENSOR_MULTILEVEL) in kstr or kstr.startswith("49-"):
                raw = extract_zwave_value(v)
                try:
                    f = float(raw)
                except (TypeError, ValueError):
                    continue
                prop = str(v.get("property", ""))
                prop_key = str(v.get("propertyKey", ""))
                # Clé du type "49-0-1" ou "49-0-Air temperature"
                parts = kstr.split("-")
                last_part = parts[-1] if parts else ""
                if last_part in cc49_property_map:
                    kind = cc49_property_map[last_part]
                    if kind == "temperature_c":
                        out["temperature_c"] = round(f, 1)
                    elif kind == "illuminance_lux":
                        out["illuminance_lux"] = int(round(f))
                    elif kind == "humidity":
                        out["humidity"] = round(f, 1)
                    elif kind == "ultraviolet":
                        out["ultraviolet"] = round(f, 1)
                elif "Air temperature" in kstr or "Air temperature" in prop or prop_key == "1":
                    out["temperature_c"] = round(f, 1)
                elif "Humidity" in kstr or "Humidity" in prop or prop_key == "5":
                    out["humidity"] = round(f, 1)
                elif "Illuminance" in kstr or "Illuminance" in prop or prop_key == "3":
                    out["illuminance_lux"] = int(round(f))
                elif "Ultraviolet" in kstr or "Ultraviolet" in prop or prop_key == "27":
                    out["ultraviolet"] = round(f, 1)
            elif str(CommandClass.BATTERY) in kstr or kstr.startswith("128-"):
                if "level" in kstr or v.get("property") == "level":
                    val = extract_zwave_value(v)
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
        Lit les valeurs capteur du nœud (MultiSensor 7 : CC 48 Motion, CC 49 temp/lux/humidity/UV, CC 128 batterie).
        Un seul chemin : HTTP get_node (si dispo) puis sinon getValue par valueId string (format panneau).
        Pas de timeout court — 10 s par getValue pour appareils sur pile.
        """
        # 1) HTTP get_node (port Z-Wave JS UI, ex. 8091) — rapide si l’UI expose /api/nodes/{id}
        node = await self._get_node_via_http(node_id)
        if node is not None:
            self._cache_node.set(node_id, node)
            data = self._sensor_values_from_node(node)
            data["node_id"] = node_id
            info = device_info_from_node(node)
            if info:
                data["device_type"] = info["device_type"]
                data["device_name"] = info["device_name"]
                data["device_model"] = info["device_model"]
            else:
                data["device_type"] = data["device_name"] = data["device_model"] = None
            if self._sensor_data_has_values(data):
                self._cache_sensor_data.set(node_id, dict(data))
            return data

        # 2) Lecture simple : getValue avec valueId strings (ex. 5-48-0-Motion, 5-49-0-Air temperature)
        data = await self._get_sensor_data_simple(node_id, timeout_per_call=10.0)
        data["node_id"] = node_id
        data["device_type"] = "aeotec_multisensor7"
        data["device_name"] = "Aeotec MultiSensor 7"
        data["device_model"] = "ZWA024"
        if self._sensor_data_has_values(data):
            self._cache_sensor_data.set(node_id, dict(data))
            logger.info("get_sensor_data node %s: données via getValue (valueId strings)", node_id)
            return data

        # 3) Aucune valeur : cache ou unknown
        cached_data = self._cache_sensor_data.get(node_id)
        if cached_data is not None:
            out = dict(cached_data)
            out["cached"] = True
            out["node_id"] = node_id
            logger.info("get_sensor_data node %s: retour cache", node_id)
            return out
        self._cache_sensor_data.pop(node_id, None)
        logger.warning("get_sensor_data node %s: aucune donnée (HTTP + getValue)", node_id)
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
        values = node.get("values")
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict) and v.get("commandClass") == CommandClass.MULTILEVEL_SWITCH and v.get("property") == PROP_CURRENT_VALUE:
                    val = extract_zwave_value(v)
                    if val is not None:
                        try:
                            return int(val)
                        except (TypeError, ValueError):
                            pass
        elif isinstance(values, dict):
            for k, v in values.items():
                if "currentValue" in str(k) and isinstance(v, dict):
                    val = extract_zwave_value(v)
                    if val is not None:
                        try:
                            return int(val)
                        except (TypeError, ValueError):
                            pass
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
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
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
        # Fallback : récupérer la liste des nœuds et extraire le bon (certaines UIs n'exposent pas GET /nodes/{id})
        for list_path in ("/api/nodes", "/nodes"):
            try:
                url = self.base_url.rstrip("/") + list_path
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status != 200:
                            continue
                        content_type = (resp.headers.get("Content-Type") or "").lower()
                        if "application/json" not in content_type:
                            continue
                        data = await resp.json()
                        nodes = data if isinstance(data, list) else (data.get("nodes") or data.get("data")) if isinstance(data, dict) else None
                        if not nodes:
                            continue
                        for n in nodes:
                            if isinstance(n, dict) and (n.get("id") == node_id or n.get("nodeId") == node_id):
                                logger.debug("_get_node_via_http: node %s trouvé via %s", node_id, list_path)
                                return n
            except Exception as e:
                logger.debug("_get_node_via_http list %s: %s", list_path, e)
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
                raw = extract_zwave_value(result)
                try:
                    v = int(raw) if raw is not None else None
                except (TypeError, ValueError):
                    v = None
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
