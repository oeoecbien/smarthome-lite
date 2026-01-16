"""
Service de gestion des appareils
"""

import logging
import httpx
from typing import Optional, Literal
from sqlalchemy.orm import Session

from app.models import Device, RaspberryPi, Event
from app.config import settings

logger = logging.getLogger(__name__)

class DeviceService:
    """
    Service pour contrôler les appareils via Raspberry Pi
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def send_command_to_rpi(
        self,
        rpi: RaspberryPi,
        endpoint: str,
        data: dict
    ) -> dict:
        """
        Envoie une commande HTTP au Raspberry Pi
        
        Args:
            rpi: Instance RaspberryPi
            endpoint: Endpoint de l'API Flask (ex: "/api/devices/1/state")
            data: Données JSON à envoyer
        
        Returns:
            Réponse JSON du Raspberry Pi
        """
        if not rpi.is_online:
            raise Exception(f"Raspberry Pi {rpi.name} is offline")
        
        url = f"http://{rpi.ip_address}:5000{endpoint}"
        headers = {"X-API-Key": rpi.api_key}
        
        try:
            async with httpx.AsyncClient(timeout=settings.raspberry_pi_timeout) as client:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                return response.json()
        
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to {rpi.name} at {url}")
            raise Exception(f"Raspberry Pi {rpi.name} not responding")
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error with {rpi.name}: {e}")
            raise Exception(f"Communication error with {rpi.name}")
    
    async def set_device_state(
        self,
        device_id: int,
        state: bool,
        source: str = "manual"
    ) -> Device:
        """
        Change l'état ON/OFF d'un appareil
        """
        device = self.db.query(Device).filter(Device.id == device_id).first()
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
        Change l'intensité d'un appareil dimmable
        """
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        if device.type not in ["light", "dimmer"]:
            raise ValueError(f"Device {device.name} is not dimmable")
        
        rpi = device.raspberry_pi
        
        # Envoyer commande au Raspberry Pi
        await self.send_command_to_rpi(
            rpi,
            f"/api/devices/{device.gpio_pin}/brightness",
            {
                "brightness": brightness,
                "transition": transition
            }
        )
        
        # Mettre à jour en base
        previous_brightness = device.brightness
        device.brightness = brightness
        device.state = brightness > 0  # Auto ON si brightness > 0
        
        # Enregistrer l'événement
        event = Event(
            device_id=device.id,
            event_type="brightness_changed",
            value=f"{previous_brightness}->{brightness}",
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
                    trigger_data={"device_id": device.id, "brightness": brightness}
                )
                if executed_rules:
                    logger.info(f"Règles exécutées après changement d'intensité: {len(executed_rules)}")
            except Exception as e:
                logger.warning(f"Erreur lors de l'évaluation des règles: {e}")
        
        logger.info(
            f"Device {device.name} brightness changed "
            f"{previous_brightness}% → {brightness}% (source: {source})"
        )
        
        return device
    
    def get_device_with_location(self, device_id: int, user_id: Optional[int] = None) -> dict:
        """
        Récupère un appareil avec informations de localisation
        """
        query = self.db.query(Device).filter(Device.id == device_id)
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
            "brightness": device.brightness,
            "gpio_pin": device.gpio_pin,
            "raspberry_pi_name": device.raspberry_pi.name,
            "location": device.raspberry_pi.location,
            "raspberry_pi_online": device.raspberry_pi.is_online,
            "created_at": device.created_at,
            "updated_at": device.updated_at
        }
    
    def get_all_devices_with_location(self, user_id: Optional[int] = None):
        """
        Récupère tous les appareils avec localisation (filtrés par user_id si fourni)
        """
        query = self.db.query(Device).join(RaspberryPi)
        if user_id:
            query = query.filter(Device.user_id == user_id)
        devices = query.all()
        
        return [
            {
                "id": d.id,
                "name": d.name,
                "type": d.type,
                "state": d.state,
                "brightness": d.brightness,
                "raspberry_pi_name": d.raspberry_pi.name,
                "location": d.raspberry_pi.location,
                "raspberry_pi_online": d.raspberry_pi.is_online
            }
            for d in devices
        ]