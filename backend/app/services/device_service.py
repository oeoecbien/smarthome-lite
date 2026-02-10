"""
Service de gestion des appareils.
Chaîne : Front (web/mobile) → Backend (auth) → RPi (API Flask :5000) → Lampe Z-Wave.
Pilotage lampes par capteur : mouvement (ON + extinction après X s) et luminosité (seuils lux).
"""

import json
import logging
import os
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, Literal

from app.models import Device, RaspberryPi, Event, SensorControlState
from app.config import settings, BRIGHTNESS_MAX

logger = logging.getLogger(__name__)
OMIT = object()  # À passer pour « ne pas modifier » dans update_device_sensor_config


def _rpi_base_url(rpi: RaspberryPi) -> str:
    """URL de base de l'API Flask sur le RPi (port depuis config)."""
    return f"{settings.raspberry_pi_protocol}://{rpi.ip_address}:{settings.raspberry_pi_port}"


class DeviceService:
    """
    Service pour contrôler les appareils via Raspberry Pi (API Flask Z-Wave sur le RPi).
    """

    def __init__(self, db: Session):
        self.db = db

    def _rpi_headers(self) -> dict:
        """Headers pour les appels au RPi (X-API-Key). Utilise RASPBERRY_PI_API_KEY ou, à défaut, RASPBERRY_API_KEY (même .env racine)."""
        headers = dict()
        key = getattr(settings, "raspberry_pi_api_key", None) or os.environ.get("RASPBERRY_API_KEY")
        if key:
            headers["X-API-Key"] = key.strip()
        return headers

    async def _request_rpi(
        self,
        rpi: RaspberryPi,
        method: str,
        endpoint: str,
        timeout_override: Optional[float] = None,
        dont_mark_offline_on_timeout: bool = False,
        **kwargs,
    ) -> dict:
        """
        Requête HTTP vers le RPi (GET ou POST). Met à jour is_online selon le résultat.
        Envoie X-API-Key si RASPBERRY_PI_API_KEY est défini (requis si le RPi exige une clé).
        timeout_override: délai en secondes (ex. 60 pour la lecture capteur Z-Wave, plus lente).
        dont_mark_offline_on_timeout: si True, en cas de timeout on ne passe pas le RPi en hors ligne
          (utile pour la lecture capteur : le timeout peut venir du réveil Z-Wave, pas du RPi).
        """
        url = _rpi_base_url(rpi) + endpoint
        headers = {**self._rpi_headers(), **kwargs.pop("headers", {})}
        if headers:
            kwargs["headers"] = headers
        timeout_sec = timeout_override if timeout_override is not None else settings.raspberry_pi_timeout
        if "/sensor" in endpoint:
            logger.info("RPi sensor request: %s %s (timeout=%ss)", method, url, timeout_sec)
        try:
            async with httpx.AsyncClient(timeout=timeout_sec) as client:
                if method.upper() == "GET":
                    response = await client.get(url, **kwargs)
                else:
                    response = await client.post(url, **kwargs)
                response.raise_for_status()
                if not rpi.is_online:
                    rpi.is_online = True
                    self.db.commit()
                    self.db.refresh(rpi)
                    logger.info("Raspberry Pi %s is now online", rpi.name)
                result = response.json()
                if "/sensor" in endpoint and isinstance(result, dict):
                    motion = result.get("motion")
                    temp = result.get("temperature_c")
                    cached = result.get("cached", False)
                    logger.info(
                        "RPi sensor response OK: node_id=%s motion=%s temp=%s cached=%s",
                        result.get("node_id"), motion, temp, cached,
                    )
                return result
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to {rpi.name} at {url}")
            if not dont_mark_offline_on_timeout and rpi.is_online:
                rpi.is_online = False
                self.db.commit()
                self.db.refresh(rpi)
            if dont_mark_offline_on_timeout:
                raise Exception(
                    f"Lecture du capteur en timeout (appareil Z-Wave sur pile possible). Le RPi « {rpi.name} » est peut-être en ligne. Réessayez."
                )
            raise Exception(f"Raspberry Pi {rpi.name} not responding")
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            body = (e.response.text or "")[:200]
            logger.error(f"HTTP error with {rpi.name}: {status} - {body}")
            if rpi.is_online:
                rpi.is_online = False
                self.db.commit()
                self.db.refresh(rpi)
            if status == 401:
                raise Exception(
                    f"Communication error with {rpi.name}: invalid or missing API key (configure RASPBERRY_PI_API_KEY in backend .env)"
                )
            raise Exception(f"Communication error with {rpi.name} (HTTP {status})")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error with {rpi.name}: {e}")
            if rpi.is_online:
                rpi.is_online = False
                self.db.commit()
                self.db.refresh(rpi)
            raise Exception(f"Communication error with {rpi.name}")

    async def send_command_to_rpi(
        self,
        rpi: RaspberryPi,
        endpoint: str,
        data: dict,
    ) -> dict:
        """Envoie une commande POST au RPi (ex: state, brightness)."""
        return await self._request_rpi(rpi, "POST", endpoint, json=data)

    async def get_sensor_data_from_rpi(
        self,
        rpi: RaspberryPi,
        node_id: int,
    ) -> dict:
        """
        Récupère les données capteur d'un nœud Z-Wave depuis le RPi.
        Compatible Aeotec MultiSensor 7 (ZWA024) : motion, temperature_c, humidity,
        illuminance_lux, ultraviolet, battery_percent, device_type, etc.
        Le RPi utilise getValue en séquentiel (cache driver). Timeout 60 s pour
        appareils sur pile (réveil Z-Wave lent) ; on ne marque pas le RPi hors ligne en cas de timeout.
        """
        endpoint = f"/api/nodes/{node_id}/sensor"
        return await self._request_rpi(
            rpi, "GET", endpoint,
            timeout_override=60.0,
            dont_mark_offline_on_timeout=True,
        )

    async def get_state_from_rpi(self, device: Device) -> Optional[dict]:
        """
        Récupère l'état réel depuis le RPi (GET /api/devices/{gpio_pin}/state).
        Retourne {"state": bool, "brightness": int} ou None en cas d'erreur / si le nœud est un capteur.
        """
        rpi = device.raspberry_pi
        endpoint = f"/api/devices/{device.gpio_pin}/state"
        try:
            data = await self._request_rpi(rpi, "GET", endpoint)
            if not isinstance(data, dict):
                return None
            if data.get("sensor") is True:
                return None  # Nœud capteur : pas de state/brightness
            if "state" not in data:
                return None
            raw = data.get("brightness", 0)
            if raw is None:
                raw = 0
            return {
                "state": bool(data.get("state", False)),
                "brightness": min(BRIGHTNESS_MAX, max(0, int(raw))),
            }
        except Exception as e:
            logger.debug("get_state_from_rpi device %s: %s", device.id, e)
            return None

    async def sync_device_state_from_rpi(self, device_id: int) -> Optional[Device]:
        """
        Met à jour l'appareil en base avec l'état lu depuis le RPi.
        Retourne le device rafraîchi ou None si la lecture RPi échoue (exclut soft-deleted).
        Ignoré pour les appareils de type sensor (pas de state/brightness).
        """
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_(None),
        ).first()
        if not device:
            return None
        if device.type == "sensor":
            return device  # Pas de state/brightness pour les capteurs
        state_data = await self.get_state_from_rpi(device)
        if state_data is None:
            return None
        device.state = state_data["state"]
        device.brightness = min(BRIGHTNESS_MAX, state_data["brightness"])
        self.db.commit()
        self.db.refresh(device)
        return device
    
    async def set_device_state(
        self,
        device_id: int,
        state: bool,
        source: str = "manual"
    ) -> Device:
        """
        Change l'état ON/OFF d'un appareil (exclut les appareils soft-deleted).
        """
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_(None),
        ).first()
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        rpi = device.raspberry_pi
        
        # Envoyer commande au Raspberry Pi
        await self.send_command_to_rpi(
            rpi,
            f"/api/devices/{device.gpio_pin}/state",
            {"state": state}
        )
        
        # Mettre à jour en base
        device.state = state
        
        # Enregistrer l'événement
        event = Event(
            device_id=device.id,
            event_type="state_changed",
            value=str(state).lower(),
            source=source
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(device)
        
        # Déclencher l'évaluation des règles (si source != automatic pour éviter les boucles)
        if source != "automatic":
            try:
                from app.services.rule_engine import RuleEngine
                rule_engine = RuleEngine(self.db)
                executed_rules = rule_engine.evaluate_rules(
                    trigger_event="state_changed",
                    trigger_data={"device_id": device.id, "state": state}
                )
                if executed_rules:
                    logger.info(f"Règles exécutées après changement d'état: {len(executed_rules)}")
            except Exception as e:
                logger.warning(f"Erreur lors de l'évaluation des règles: {e}")
        
        logger.info(f"Device {device.name} state changed to {state} (source: {source})")
        
        return device
    
    async def set_device_brightness(
        self,
        device_id: int,
        brightness: int,
        source: str = "manual",
        transition: Literal["immediate", "fade"] = "immediate"
    ) -> Device:
        """
        Change l'intensité d'un appareil dimmable (exclut les appareils soft-deleted).
        """
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_(None),
        ).first()
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        if device.type not in ["light", "dimmer"]:
            raise ValueError(f"Device {device.name} is not dimmable")
        
        # Stocker 0-100 pour le frontend ; envoyer 0-99 au RPi (Z-Wave)
        brightness_stored = max(0, min(100, brightness))
        brightness_rpi = min(BRIGHTNESS_MAX, brightness_stored)
        rpi = device.raspberry_pi
        
        # Envoyer commande au Raspberry Pi (0-99)
        await self.send_command_to_rpi(
            rpi,
            f"/api/devices/{device.gpio_pin}/brightness",
            {
                "brightness": brightness_rpi,
                "transition": transition
            }
        )
        
        # Mettre à jour en base (0-100)
        previous_brightness = device.brightness
        device.brightness = brightness_stored
        device.state = brightness > 0  # Auto ON si brightness > 0
        
        # Enregistrer l'événement
        event = Event(
            device_id=device.id,
            event_type="brightness_changed",
            value=f"{previous_brightness}->{brightness_stored}",
            source=source
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(device)
        
        # Déclencher l'évaluation des règles (si source != automatic pour éviter les boucles)
        if source != "automatic":
            try:
                from app.services.rule_engine import RuleEngine
                rule_engine = RuleEngine(self.db)
                executed_rules = rule_engine.evaluate_rules(
                    trigger_event="brightness_changed",
                    trigger_data={"device_id": device.id, "brightness": brightness_stored}
                )
                if executed_rules:
                    logger.info(f"Règles exécutées après changement d'intensité: {len(executed_rules)}")
            except Exception as e:
                logger.warning(f"Erreur lors de l'évaluation des règles: {e}")
        
        logger.info(
            f"Device {device.name} brightness changed "
            f"{previous_brightness}% → {brightness_stored}% (source: {source})"
        )
        
        return device
    
    def get_device_with_location(self, device_id: int, user_id: Optional[int] = None) -> dict:
        """
        Récupère un appareil avec informations de localisation (exclut les appareils soft-deleted).
        """
        query = self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_(None),
        )
        if user_id:
            query = query.filter(Device.user_id == user_id)
        device = query.first()
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        out = {
            "id": device.id,
            "name": device.name,
            "type": device.type,
            "state": device.state,
            "brightness": min(100, max(0, device.brightness)),
            "gpio_pin": device.gpio_pin,
            "raspberry_pi_name": device.raspberry_pi.name,
            "location": device.raspberry_pi.location,
            "raspberry_pi_online": device.raspberry_pi.is_online,
            "created_at": device.created_at,
            "updated_at": device.updated_at
        }
        if device.controlled_by_sensor_id is not None:
            out["controlled_by_sensor_id"] = device.controlled_by_sensor_id
            out["sensor_rules"] = self._parse_sensor_rules(device.sensor_rules)
            sensor_dev = self.db.query(Device).filter(
                Device.id == device.controlled_by_sensor_id,
                Device.deleted_at.is_(None),
            ).first()
            out["controlled_by_sensor_name"] = sensor_dev.name if sensor_dev else None
        return out

    def get_all_devices_with_location(self, user_id: Optional[int] = None):
        """
        Récupère tous les appareils avec localisation (filtrés par user_id si fourni).
        Exclut les appareils soft-deleted (deleted_at).
        """
        query = (
            self.db.query(Device)
            .join(RaspberryPi)
            .filter(Device.deleted_at.is_(None))
        )
        if user_id:
            query = query.filter(Device.user_id == user_id)
        devices = query.order_by(Device.id.asc()).all()
        
        result = []
        for d in devices:
            row = {
                "id": d.id,
                "name": d.name,
                "type": d.type,
                "state": d.state,
                "brightness": min(100, max(0, d.brightness)),
                "gpio_pin": d.gpio_pin,
                "raspberry_pi_name": d.raspberry_pi.name,
                "location": d.raspberry_pi.location,
                "raspberry_pi_online": d.raspberry_pi.is_online,
            }
            if d.controlled_by_sensor_id is not None:
                row["controlled_by_sensor_id"] = d.controlled_by_sensor_id
                row["sensor_rules"] = self._parse_sensor_rules(d.sensor_rules)
                sensor_dev = next((x for x in devices if x.id == d.controlled_by_sensor_id), None)
                row["controlled_by_sensor_name"] = sensor_dev.name if sensor_dev else None
            result.append(row)
        return result

    def update_device_sensor_config(
        self,
        device_id: int,
        controlled_by_sensor_id: Any = OMIT,
        sensor_rules: Any = OMIT,
    ) -> Device:
        """Met à jour le pilotage par capteur. OMIT = ne pas modifier le champ."""
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_(None),
        ).first()
        if not device:
            raise ValueError(f"Device {device_id} not found")
        if device.type not in ("light", "dimmer"):
            raise ValueError("Seules les lampes (light/dimmer) peuvent être pilotées par un capteur")
        if controlled_by_sensor_id is not OMIT:
            if controlled_by_sensor_id is not None:
                sensor_dev = self.db.query(Device).filter(
                    Device.id == int(controlled_by_sensor_id),
                    Device.type == "sensor",
                    Device.deleted_at.is_(None),
                ).first()
                if not sensor_dev:
                    raise ValueError(f"Capteur (device {controlled_by_sensor_id}) introuvable ou pas de type sensor")
                device.controlled_by_sensor_id = int(controlled_by_sensor_id)
            else:
                device.controlled_by_sensor_id = None
        if sensor_rules is not OMIT:
            device.sensor_rules = json.dumps(sensor_rules) if sensor_rules else None
        self.db.commit()
        self.db.refresh(device)
        return device

    def _parse_sensor_rules(self, raw: Optional[str]) -> Optional[Dict[str, Any]]:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return None

    async def evaluate_sensor_rules(self, sensor_device_id: int, sensor_data: Dict[str, Any]) -> None:
        """
        Applique les règles capteur → lampe pour toutes les lampes pilotées par ce capteur.
        sensor_data: motion (bool), illuminance_lux (int|None), temperature_c, humidity, etc.
        Règles: motion { on_brightness, off_after_seconds }, illuminance { below_lux, brightness, above_lux, action: "off" }.
        """
        lamps = self.db.query(Device).filter(
            Device.controlled_by_sensor_id == sensor_device_id,
            Device.deleted_at.is_(None),
            Device.type.in_(["light", "dimmer"]),
        ).all()
        if not lamps:
            return
        motion = sensor_data.get("motion") is True
        illuminance_lux = sensor_data.get("illuminance_lux")
        now = datetime.now(timezone.utc)

        for lamp in lamps:
            rules = self._parse_sensor_rules(lamp.sensor_rules)
            if not rules:
                continue
            try:
                # État mouvement pour timer extinction
                state_row = self.db.query(SensorControlState).filter(
                    SensorControlState.sensor_device_id == sensor_device_id,
                    SensorControlState.target_device_id == lamp.id,
                ).first()
                if not state_row:
                    state_row = SensorControlState(
                        sensor_device_id=sensor_device_id,
                        target_device_id=lamp.id,
                    )
                    self.db.add(state_row)
                    self.db.flush()

                motion_rule = rules.get("motion") or {}
                on_brightness = max(0, min(100, int(motion_rule.get("on_brightness", 80))))
                off_after_seconds = max(0, int(motion_rule.get("off_after_seconds", 300)))
                illum_rule = rules.get("illuminance") or {}
                below_lux = int(illum_rule.get("below_lux", 100))
                above_lux = int(illum_rule.get("above_lux", 2000))
                illum_brightness = max(0, min(100, int(illum_rule.get("brightness", 60))))

                if motion:
                    state_row.last_motion_at = now
                    state_row.last_motion_off_at = None
                    self.db.commit()
                    if not lamp.state or lamp.brightness != on_brightness:
                        await self.set_device_brightness(lamp.id, on_brightness, source="automatic")
                    continue

                # Pas de mouvement
                state_row.last_motion_off_at = state_row.last_motion_off_at or now
                self.db.commit()
                elapsed = (now - state_row.last_motion_off_at).total_seconds()

                # Luminosité : si trop de lumière → éteindre ; si pas assez → allumer
                if illuminance_lux is not None:
                    if illuminance_lux > above_lux:
                        if lamp.state:
                            await self.set_device_state(lamp.id, False, source="automatic")
                        continue
                    if illuminance_lux < below_lux:
                        if not lamp.state or lamp.brightness != illum_brightness:
                            await self.set_device_brightness(lamp.id, illum_brightness, source="automatic")
                            await self.set_device_state(lamp.id, True, source="automatic")
                        continue

                # Extinction après X s sans mouvement
                if off_after_seconds > 0 and elapsed >= off_after_seconds and lamp.state:
                    await self.set_device_state(lamp.id, False, source="automatic")
            except Exception as e:
                logger.warning("evaluate_sensor_rules lamp %s: %s", lamp.id, e)