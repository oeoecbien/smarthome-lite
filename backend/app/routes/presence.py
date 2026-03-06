"""
Routes pour la détection de présence (mouvement MultiSensor7).
Utilisées par le Raspberry Pi (Z-Wave) pour enregistrer les détections de mouvement.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Presence, RaspberryPi, Device
from app.dependencies import verify_raspberry_pi, require_admin, User, PaginationParams
from app.services.rule_engine import RuleEngine
from app.services.device_service import DeviceService

router = APIRouter()
logger = logging.getLogger(__name__)


class PresenceCreate(BaseModel):
    """Schéma pour création d'une détection de mouvement (MultiSensor7)."""
    sensor_node_id: Optional[int] = None  # Node ID Z-Wave du capteur (ex: MultiSensor7)


class PresenceResponse(BaseModel):
    """Schéma de réponse pour une détection."""
    id: int
    raspberry_pi_id: int
    raspberry_pi_name: str
    location: str
    detected_at: datetime
    sensor_node_id: Optional[int] = None


@router.post("", response_model=PresenceResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=PresenceResponse, status_code=status.HTTP_201_CREATED)
async def create_presence(
    request: PresenceCreate,
    rpi: RaspberryPi = Depends(verify_raspberry_pi),
    db: Session = Depends(get_db)
):
    """
    Enregistre une détection de mouvement (appelé par le RPi quand le détecteur Z-Wave signale un mouvement).

    Si le détecteur est enregistré comme Device (type sensor) avec gpio_pin = sensor_node_id,
    les règles capteur→lampe (sensor_rules) sont appliquées (allumage, extinction après X s).
    Les règles génériques (presence_detected) sont aussi évaluées.
    """
    # Anti-rebond : ne pas enregistrer si une détection a déjà eu lieu dans les 5 dernières secondes (même RPi)
    five_seconds_ago = datetime.now() - timedelta(seconds=5)
    recent = (
        db.query(Presence)
        .filter(
            Presence.raspberry_pi_id == rpi.id,
            Presence.detected_at >= five_seconds_ago,
        )
        .first()
    )
    if recent:
        return {
            "id": recent.id,
            "raspberry_pi_id": recent.raspberry_pi_id,
            "raspberry_pi_name": rpi.name,
            "location": rpi.location or "",
            "detected_at": recent.detected_at,
            "sensor_node_id": recent.sensor_node_id,
        }

    presence = Presence(
        raspberry_pi_id=rpi.id,
        sensor_node_id=request.sensor_node_id,
    )
    db.add(presence)
    db.commit()
    db.refresh(presence)

    # Si le détecteur est enregistré comme Device (type sensor), appliquer les règles capteur → lampe
    sensor_node_id = request.sensor_node_id
    if sensor_node_id is not None:
        sensor_device = (
            db.query(Device)
            .filter(
                Device.raspberry_pi_id == rpi.id,
                Device.gpio_pin == sensor_node_id,
                Device.type == "sensor",
                Device.deleted_at.is_(None),
            )
            .first()
        )
        if sensor_device:
            try:
                device_service = DeviceService(db)
                await device_service.evaluate_sensor_rules(
                    sensor_device.id,
                    {"motion": True},
                )
                logger.debug(
                    "Règles capteur→lampe appliquées pour le détecteur (device_id=%s, node_id=%s)",
                    sensor_device.id,
                    sensor_node_id,
                )
            except Exception as e:
                logger.warning("evaluate_sensor_rules après présence: %s", e)

    # Règles génériques (presence_detected)
    try:
        rule_engine = RuleEngine(db)
        trigger_data = {
            "raspberry_pi_id": rpi.id,
            "location": rpi.location,
        }
        executed_rules = await rule_engine.evaluate_rules(
            trigger_event="presence_detected",
            trigger_data=trigger_data
        )
        if executed_rules:
            logger.debug("Règles exécutées après détection de mouvement: %s", len(executed_rules))
    except Exception as e:
        logger.error("Erreur lors de l'évaluation des règles: %s", e)

    return {
        "id": presence.id,
        "raspberry_pi_id": presence.raspberry_pi_id,
        "raspberry_pi_name": rpi.name,
        "location": rpi.location or "",
        "detected_at": presence.detected_at,
        "sensor_node_id": presence.sensor_node_id,
    }


@router.get("", response_model=List[PresenceResponse], include_in_schema=False)
@router.get("/", response_model=List[PresenceResponse])
async def get_presence_history(
    raspberry_pi_id: Optional[int] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Récupère l'historique des détections de mouvement (admins uniquement).
    """
    query = db.query(Presence)
    if raspberry_pi_id:
        query = query.filter(Presence.raspberry_pi_id == raspberry_pi_id)

    presences = (
        query.order_by(Presence.detected_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
        .all()
    )

    result = []
    for presence in presences:
        rpi = db.query(RaspberryPi).filter(RaspberryPi.id == presence.raspberry_pi_id).first()
        result.append({
            "id": presence.id,
            "raspberry_pi_id": presence.raspberry_pi_id,
            "raspberry_pi_name": rpi.name if rpi else "Unknown",
            "location": rpi.location if rpi else "Unknown",
            "detected_at": presence.detected_at,
            "sensor_node_id": presence.sensor_node_id,
        })
    return result
