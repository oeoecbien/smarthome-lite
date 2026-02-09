"""
Service de gestion des appareils.
Chaîne : Front (web/mobile) → Backend (auth) → RPi (API Flask :5000) → Lampe Z-Wave.
"""

import logging
import httpx
from typing import Optional, Literal
from sqlalchemy.orm import Session

from app.models import Device, RaspberryPi, Event
from app.config import settings, BRIGHTNESS_MAX

logger = logging.getLogger(__name__)


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
        """Headers pour les appels au RPi (X-API-Key si configuré)."""
        headers = dict()
        if getattr(settings, "raspberry_pi_api_key", None):
            headers["X-API-Key"] = settings.raspberry_pi_api_key
        return headers

    async def _request_rpi(
        self,
        rpi: RaspberryPi,
        method: str,
        endpoint: str,
        timeout_override: Optional[float] = None,
        **kwargs,
    ) -> dict:
        """
        Requête HTTP vers le RPi (GET ou POST). Met à jour is_online selon le résultat.
        Envoie X-API-Key si RASPBERRY_PI_API_KEY est défini (requis si le RPi exige une clé).
        timeout_override: délai en secondes (ex. 20 pour la lecture capteur Z-Wave, plus lente).
        """
        url = _rpi_base_url(rpi) + endpoint
        headers = {**self._rpi_headers(), **kwargs.pop("headers", {})}
        if headers:
            kwargs["headers"] = headers
        timeout_sec = timeout_override if timeout_override is not None else settings.raspberry_pi_timeout
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
                    logger.info(f"Raspberry Pi {rpi.name} is now online")
                return response.json()
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to {rpi.name} at {url}")
            if rpi.is_online:
                rpi.is_online = False
                self.db.commit()
                self.db.refresh(rpi)
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
        Timeout plus long (20 s) car la lecture Z-Wave (get_node + parsing) peut être lente.
        """
        endpoint = f"/api/nodes/{node_id}/sensor"
        return await self._request_rpi(rpi, "GET", endpoint, timeout_override=20.0)

    async def get_state_from_rpi(self, device: Device) -> Optional[dict]:
        """
        Récupère l'état réel depuis le RPi (GET /api/devices/{gpio_pin}/state).
        Retourne {"state": bool, "brightness": int} ou None en cas d'erreur.
        """
        rpi = device.raspberry_pi
        endpoint = f"/api/devices/{device.gpio_pin}/state"
        try:
            data = await self._request_rpi(rpi, "GET", endpoint)
            if isinstance(data, dict) and "state" in data:
                raw = int(data.get("brightness", 0))
                return {
                    "state": bool(data.get("state", False)),
                    "brightness": min(BRIGHTNESS_MAX, max(0, raw)),
                }
            return None
        except Exception as e:
            logger.debug("get_state_from_rpi device %s: %s", device.id, e)
            return None

    async def sync_device_state_from_rpi(self, device_id: int) -> Optional[Device]:
        """
        Met à jour l'appareil en base avec l'état lu depuis le RPi.
        Retourne le device rafraîchi ou None si la lecture RPi échoue (exclut soft-deleted).
        """
        device = self.db.query(Device).filter(
            Device.id == device_id,
            Device.deleted_at.is_(None),
        ).first()
        if not device:
            return None
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
        
        return {
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
        
        return [
            {
                "id": d.id,
                "name": d.name,
                "type": d.type,
                "state": d.state,
                "brightness": min(100, max(0, d.brightness)),
                "raspberry_pi_name": d.raspberry_pi.name,
                "location": d.raspberry_pi.location,
                "raspberry_pi_online": d.raspberry_pi.is_online
            }
            for d in devices
        ]