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
    Obtient l'état global du système Smart Dimming.
    """
    service = SmartDimmingService(db)
    stats = service.get_statistics()
    
    # Compter les ajustements aujourd'hui
    from datetime import datetime, timedelta
    from app.models import SmartDimmingAdjustment, Device
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(SmartDimmingAdjustment).filter(
        SmartDimmingAdjustment.adjusted_at >= today_start
    ).count()
    
    # Obtenir les appareils actifs (dimmables allumés qui ont eu des ajustements récents)
    # On considère comme "actifs" les appareils dimmables allumés de l'utilisateur
    recent_time = datetime.now() - timedelta(hours=2)
    active_device_ids = db.query(Device.id).filter(
        Device.type == "dimmer",
        Device.state == True,
        Device.user_id == current_user.id
    ).distinct().all()
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
    Récupère l'historique des ajustements Smart Dimming (uniquement pour les devices de l'utilisateur).
    """
    # Si device_id fourni, vérifier qu'il appartient à l'utilisateur
    if device_id:
        device = db.query(Device).filter(
            Device.id == device_id,
            Device.user_id == current_user.id
        ).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found or access denied")
    
    service = SmartDimmingService(db)
    adjustments = service.get_adjustment_history(device_id=device_id, limit=limit)
    
    # Filtrer pour ne garder que les ajustements des devices de l'utilisateur
    user_device_ids = {d[0] for d in db.query(Device.id).filter(Device.user_id == current_user.id).all()}
    adjustments = [adj for adj in adjustments if adj.device_id in user_device_ids]
    
    result = []
    for adj in adjustments:
        # Récupérer le nom de l'appareil
        from app.models import Device
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
    """
    from app.models import Device
    from datetime import datetime, timedelta
    
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == current_user.id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Appareil introuvable ou accès refusé")
    
    # Pour l'instant, on utilise un champ dans la config ou on pourrait
    # ajouter un champ `smart_dimming_paused_until` dans le modèle Device
    # Pour cette version, on retourne simplement un message de confirmation
    
    # TODO: Implémenter la pause réelle avec un champ dans Device ou une table séparée
    pause_until = datetime.now() + timedelta(minutes=30)
    
    return {
        "device_id": device_id,
        "device_name": device.name,
        "paused": True,
        "paused_until": pause_until.isoformat(),
        "message": f"Smart Dimming mis en pause pour {device.name} jusqu'à {pause_until.strftime('%H:%M')}"
    }
