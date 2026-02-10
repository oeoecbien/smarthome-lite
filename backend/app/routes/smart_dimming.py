"""
Routes pour le système Smart Dimming.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user, User
from app.services.smart_dimming_service import SmartDimmingService
from app.schemas.smart_dimming import SmartDimmingStatus, SmartDimmingAdjustmentResponse, SmartDimmingAdjustmentFrontendResponse
from app.config import settings

router = APIRouter()


class SmartDimmingEnableRequest(BaseModel):
    """Requête pour activer/désactiver le Smart Dimming."""
    enabled: bool


@router.get("/status", response_model=SmartDimmingStatus)
async def get_smart_dimming_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtient l'état du système Smart Dimming.
    - Utilisateurs normaux: statistiques de leurs appareils uniquement
    - Admins: statistiques globales de tous les appareils
    """
    service = SmartDimmingService(db)
    stats = service.get_statistics()
    
    # Compter les ajustements aujourd'hui
    from datetime import datetime, timedelta
    from app.models import SmartDimmingAdjustment, Device
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    query_adjustments = db.query(SmartDimmingAdjustment).filter(
        SmartDimmingAdjustment.adjusted_at >= today_start
    )
    
    # Filtrer par les devices de l'utilisateur si ce n'est pas un admin
    if current_user.role != "admin":
        user_device_ids = [d.id for d in db.query(Device.id).filter(Device.user_id == current_user.id).all()]
        query_adjustments = query_adjustments.filter(
            SmartDimmingAdjustment.device_id.in_(user_device_ids)
        )
    
    today_count = query_adjustments.count()
    
    # Obtenir les appareils actifs (dimmables allumés, types light et dimmer)
    query_devices = db.query(Device.id).filter(
        Device.type.in_(["light", "dimmer"]),
        Device.state == True,
        Device.deleted_at.is_(None),
    )
    
    # Filtrer par les devices de l'utilisateur si ce n'est pas un admin
    if current_user.role != "admin":
        query_devices = query_devices.filter(Device.user_id == current_user.id)
    
    active_device_ids = query_devices.distinct().all()
    active_devices = [device_id[0] for device_id in active_device_ids]
    
    return {
        "enabled": stats["enabled"],
        "adjustments_today": today_count,
        "active_devices": active_devices
    }


@router.get("/adjustments", response_model=List[SmartDimmingAdjustmentFrontendResponse])
async def get_adjustments(
    device_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère l'historique des ajustements Smart Dimming.
    - Utilisateurs normaux: uniquement les ajustements de leurs appareils
    - Admins: tous les ajustements
    """
    from app.models import Device
    
    # Si device_id fourni, vérifier les permissions
    if device_id:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        # Vérifier les permissions: les utilisateurs normaux ne peuvent voir que leurs appareils
        if current_user.role != "admin" and device.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    service = SmartDimmingService(db)
    adjustments = service.get_adjustment_history(device_id=device_id, limit=limit)
    
    # Filtrer pour ne garder que les ajustements des devices de l'utilisateur si ce n'est pas un admin
    if current_user.role != "admin":
        user_device_ids = {d[0] for d in db.query(Device.id).filter(Device.user_id == current_user.id).all()}
        adjustments = [adj for adj in adjustments if adj.device_id in user_device_ids]
    
    result = []
    for adj in adjustments:
        # Récupérer le nom de l'appareil
        device = db.query(Device).filter(Device.id == adj.device_id).first()
        device_name = device.name if device else "Unknown"
        
        # Récupérer la luminosité si disponible
        light_level = None
        if adj.light_reading_id:
            from app.models import LightReading
            reading = db.query(LightReading).filter(
                LightReading.id == adj.light_reading_id
            ).first()
            if reading:
                light_level = reading.lux_value
        
        result.append({
            "id": adj.id,
            "device_id": adj.device_id,
            "device_name": device_name,
            "scenario": adj.scenario,
            "brightness_before": adj.previous_brightness,
            "brightness_after": adj.applied_brightness,
            "reason": adj.reason,
            "timestamp": adj.adjusted_at.isoformat() if adj.adjusted_at else None
        })
    
    return result


@router.put("/enable")
async def enable_smart_dimming(
    request: SmartDimmingEnableRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Active ou désactive le Smart Dimming globalement.
    """
    # Mettre à jour la configuration (dans un vrai système, on pourrait stocker en BDD)
    # Pour l'instant, on utilise juste la config
    settings.smart_dimming_enabled = request.enabled
    
    return {
        "enabled": request.enabled,
        "message": f"Smart Dimming {'activé' if request.enabled else 'désactivé'}"
    }


@router.put("/pause/{device_id}")
async def pause_smart_dimming_for_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met en pause le Smart Dimming pour un appareil spécifique pendant 30 minutes.
    
    Utile si l'utilisateur ajuste manuellement l'intensité et veut éviter
    que le système ne la modifie automatiquement.
    - Utilisateurs normaux: uniquement leurs appareils
    - Admins: tous les appareils
    """
    from app.models import Device
    from datetime import datetime, timedelta, timezone

    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Appareil introuvable")
    
    # Vérifier les permissions: les utilisateurs normaux ne peuvent modifier que leurs appareils
    if current_user.role != "admin" and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    pause_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    device.smart_dimming_paused_until = pause_until
    db.add(device)
    db.commit()
    db.refresh(device)

    return {
        "device_id": device_id,
        "device_name": device.name,
        "paused": True,
        "paused_until": pause_until.isoformat(),
        "message": f"Smart Dimming mis en pause pour {device.name} pendant 30 minutes"
    }
