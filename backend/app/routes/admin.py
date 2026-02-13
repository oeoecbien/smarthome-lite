"""
Routes d'administration - Accessibles uniquement aux administrateurs
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.database import get_db
from app.dependencies import get_current_user, require_admin, User
from app.models import Device, User as UserModel, Event, SmartDimmingAdjustment, RaspberryPi, LightReading, Presence
from app.services.smart_dimming_service import SmartDimmingService

router = APIRouter()


class SimulateLightReadingRequest(BaseModel):
    """Corps pour simuler une mesure de luminosité (test Smart Dimming)."""
    raspberry_pi_id: int = Field(..., description="ID du Raspberry Pi (lieu de la mesure)")
    lux_value: float = Field(..., ge=0, description="Valeur en lux (ex: 50, 300, 600)")

class SimulatePresenceRequest(BaseModel):
    """Corps pour simuler une détection de présence (test page admin/presence)."""
    raspberry_pi_id: int = Field(..., description="ID du Raspberry Pi")
    sensor_node_id: Optional[int] = Field(None, description="Node ID Z-Wave du capteur (ex: MultiSensor7)")

@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Statistiques globales du système (uniquement pour les admins).
    """
    # Nombre total d'utilisateurs
    total_users = db.query(func.count(UserModel.id)).scalar()
    
    # Nombre total d'appareils
    total_devices = db.query(func.count(Device.id)).scalar()
    
    # Appareils par type
    devices_by_type = db.query(
        Device.type,
        func.count(Device.id).label('count')
    ).group_by(Device.type).all()
    devices_by_type_dict = {d.type: d.count for d in devices_by_type}
    
    # Appareils par état
    devices_on = db.query(func.count(Device.id)).filter(Device.state == True).scalar()
    devices_off = total_devices - devices_on
    
    # Événements aujourd'hui
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    events_today = db.query(func.count(Event.id)).filter(
        Event.timestamp >= today_start
    ).scalar()
    
    # Ajustements Smart Dimming aujourd'hui
    adjustments_today = db.query(func.count(SmartDimmingAdjustment.id)).filter(
        SmartDimmingAdjustment.adjusted_at >= today_start
    ).scalar()
    
    # Raspberry Pi en ligne
    raspberry_pis_online = db.query(func.count(RaspberryPi.id)).filter(
        RaspberryPi.is_online == True
    ).scalar()
    total_raspberry_pis = db.query(func.count(RaspberryPi.id)).scalar()
    
    return {
        "users": {
            "total": total_users
        },
        "devices": {
            "total": total_devices,
            "by_type": devices_by_type_dict,
            "on": devices_on,
            "off": devices_off
        },
        "events": {
            "today": events_today
        },
        "smart_dimming": {
            "adjustments_today": adjustments_today
        },
        "raspberry_pis": {
            "total": total_raspberry_pis,
            "online": raspberry_pis_online,
            "offline": total_raspberry_pis - raspberry_pis_online
        }
    }


@router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Liste tous les utilisateurs (uniquement pour les admins).
    """
    users = db.query(UserModel).all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "device_count": db.query(func.count(Device.id)).filter(
                Device.user_id == user.id
            ).scalar()
        }
        for user in users
    ]


@router.post("/smart-dimming/simulate-reading")
async def simulate_light_reading(
    body: SimulateLightReadingRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Simule une mesure de luminosité pour tester le Smart Dimming sans RPi ni capteur.
    Crée une LightReading puis appelle process_light_reading (même logique que POST /api/light-readings).
    Prérequis : Smart Dimming activé, au moins une lampe dimmable allumée sur ce RPi (non pilotée par capteur).
    """
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == body.raspberry_pi_id).first()
    if not rpi:
        raise HTTPException(status_code=404, detail="Raspberry Pi introuvable")
    reading = LightReading(
        raspberry_pi_id=body.raspberry_pi_id,
        lux_value=body.lux_value,
        sensor_type="simulated",
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    service = SmartDimmingService(db)
    adjustments = await service.process_light_reading(reading)
    return {
        "light_reading_id": reading.id,
        "lux_value": reading.lux_value,
        "adjustments_count": len(adjustments),
        "adjustments": adjustments,
    }


@router.post("/presence/simulate")
async def simulate_presence(
    body: SimulatePresenceRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Simule une détection de présence (une ligne en table presence).
    Utile pour tester la page admin/presence sans avoir le RPi qui envoie POST /api/presence.
    """
    rpi = db.query(RaspberryPi).filter(RaspberryPi.id == body.raspberry_pi_id).first()
    if not rpi:
        raise HTTPException(status_code=404, detail="Raspberry Pi introuvable")
    presence = Presence(
        raspberry_pi_id=body.raspberry_pi_id,
        sensor_node_id=body.sensor_node_id,
    )
    db.add(presence)
    db.commit()
    db.refresh(presence)
    return {
        "id": presence.id,
        "raspberry_pi_id": presence.raspberry_pi_id,
        "raspberry_pi_name": rpi.name,
        "location": rpi.location or "",
        "detected_at": presence.detected_at.isoformat() if presence.detected_at else None,
        "sensor_node_id": presence.sensor_node_id,
    }


@router.get("/zwave-devices")
async def get_zwave_known_devices(admin_user: User = Depends(require_admin)):
    """
    Liste des appareils Z-Wave connus par le backend (ex. Aeotec MultiSensor 7 ZWA024).
    """
    from app.zwave_devices import list_known_devices
    return list_known_devices()


# Note: Les endpoints /api/admin/devices/all et /api/admin/events/all ont été supprimés
# car redondants avec /api/devices/ et /api/events/ qui filtrent déjà par rôle admin.
