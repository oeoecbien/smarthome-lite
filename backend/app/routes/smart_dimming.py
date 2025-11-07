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
from app.schemas.smart_dimming import SmartDimmingStatus, SmartDimmingAdjustmentResponse
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
    from app.models import SmartDimmingAdjustment
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(SmartDimmingAdjustment).filter(
        SmartDimmingAdjustment.adjusted_at >= today_start
    ).count()
    
    return {
        "enabled": stats["enabled"],
        "active_adjustments_count": stats["total_adjustments"],
        "total_adjustments_today": today_count
    }


@router.get("/adjustments", response_model=List[SmartDimmingAdjustmentResponse])
async def get_adjustments(
    device_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère l'historique des ajustements Smart Dimming.
    """
    service = SmartDimmingService(db)
    adjustments = service.get_adjustment_history(device_id=device_id, limit=limit)
    
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
            "previous_brightness": adj.previous_brightness,
            "target_brightness": adj.target_brightness,
            "applied_brightness": adj.applied_brightness,
            "reason": adj.reason,
            "light_level": light_level,
            "adjusted_at": adj.adjusted_at
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

