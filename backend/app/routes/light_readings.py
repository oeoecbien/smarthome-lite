"""
Routes pour les mesures de luminosité (utilisées par Raspberry Pi).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models import LightReading, RaspberryPi
from app.dependencies import verify_raspberry_pi, get_current_user, require_admin, User, PaginationParams
from app.services.smart_dimming_service import SmartDimmingService

router = APIRouter()


class LightReadingCreate(BaseModel):
    """Schéma pour création d'une mesure de luminosité."""
    lux_value: float = Field(..., ge=0, description="Valeur en lux")
    sensor_type: str = Field(default="BH1750", description="Type de capteur")


class LightReadingResponse(BaseModel):
    """Schéma de réponse pour une mesure."""
    id: int
    raspberry_pi_id: int
    raspberry_pi_name: str
    lux_value: float
    sensor_type: str
    measured_at: datetime


@router.post("/", response_model=LightReadingResponse, status_code=status.HTTP_201_CREATED)
async def create_light_reading(
    reading_data: LightReadingCreate,
    rpi: RaspberryPi = Depends(verify_raspberry_pi),
    db: Session = Depends(get_db)
):
    """
    Enregistre une nouvelle mesure de luminosité (appelé par Raspberry Pi).
    
    Cette route déclenche automatiquement le Smart Dimming si activé.
    """
    # Créer la mesure
    reading = LightReading(
        raspberry_pi_id=rpi.id,
        lux_value=reading_data.lux_value,
        sensor_type=reading_data.sensor_type
    )
    
    db.add(reading)
    db.commit()
    db.refresh(reading)
    
    # Déclencher le Smart Dimming
    try:
        import logging
        logger = logging.getLogger(__name__)
        smart_dimming_service = SmartDimmingService(db)
        adjustments = await smart_dimming_service.process_light_reading(reading)
        
        if adjustments:
            logger.info(f"Smart Dimming: {len(adjustments)} ajustements effectués")
    except Exception as e:
        # Ne pas faire échouer l'enregistrement si le Smart Dimming échoue
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur Smart Dimming: {e}")
    
    return {
        "id": reading.id,
        "raspberry_pi_id": reading.raspberry_pi_id,
        "raspberry_pi_name": rpi.name,
        "lux_value": reading.lux_value,
        "sensor_type": reading.sensor_type,
        "measured_at": reading.measured_at
    }


@router.get("/", response_model=List[LightReadingResponse])
async def get_light_readings(
    raspberry_pi_id: Optional[int] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Récupère l'historique des mesures de luminosité (uniquement pour les admins).
    
    Les mesures de luminosité sont utilisées par le Smart Dimming en arrière-plan.
    Les utilisateurs normaux n'ont pas besoin d'accéder à ces données techniques.
    """
    query = db.query(LightReading)
    
    if raspberry_pi_id:
        query = query.filter(LightReading.raspberry_pi_id == raspberry_pi_id)
    
    readings = query.order_by(
        LightReading.measured_at.desc()
    ).offset(pagination.skip).limit(pagination.limit).all()
    
    result = []
    for reading in readings:
        rpi = db.query(RaspberryPi).filter(
            RaspberryPi.id == reading.raspberry_pi_id
        ).first()
        
        result.append({
            "id": reading.id,
            "raspberry_pi_id": reading.raspberry_pi_id,
            "raspberry_pi_name": rpi.name if rpi else "Unknown",
            "lux_value": reading.lux_value,
            "sensor_type": reading.sensor_type,
            "measured_at": reading.measured_at
        })
    
    return result

