"""
Routes pour la détection de présence (utilisées par Raspberry Pi).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Presence, RaspberryPi
from app.dependencies import verify_raspberry_pi, get_current_user, User, PaginationParams
from app.services.rule_engine import RuleEngine

router = APIRouter()


class PresenceCreate(BaseModel):
    """Schéma pour création d'une détection de présence."""
    pass  # Pas de données supplémentaires nécessaires


class PresenceResponse(BaseModel):
    """Schéma de réponse pour une détection."""
    id: int
    raspberry_pi_id: int
    raspberry_pi_name: str
    location: str
    detected_at: datetime


@router.post("/", response_model=PresenceResponse, status_code=status.HTTP_201_CREATED)
async def create_presence(
    rpi: RaspberryPi = Depends(verify_raspberry_pi),
    db: Session = Depends(get_db)
):
    """
    Enregistre une nouvelle détection de présence (appelé par Raspberry Pi).
    
    Cette route déclenche automatiquement l'évaluation des règles.
    """
    # Vérifier qu'il n'y a pas eu de détection récente (anti-rebond 5 secondes)
    from datetime import timedelta
    five_seconds_ago = datetime.now() - timedelta(seconds=5)
    
    recent_presence = db.query(Presence).filter(
        Presence.raspberry_pi_id == rpi.id,
        Presence.detected_at >= five_seconds_ago
    ).first()
    
    if recent_presence:
        # Retourner la détection existante (anti-rebond)
        return {
            "id": recent_presence.id,
            "raspberry_pi_id": recent_presence.raspberry_pi_id,
            "raspberry_pi_name": rpi.name,
            "location": rpi.location,
            "detected_at": recent_presence.detected_at
        }
    
    # Créer la détection
    presence = Presence(
        raspberry_pi_id=rpi.id
    )
    
    db.add(presence)
    db.commit()
    db.refresh(presence)
    
    # Déclencher l'évaluation des règles
    try:
        rule_engine = RuleEngine(db)
        executed_rules = await rule_engine.evaluate_rules(
            trigger_event="presence_detected",
            trigger_data={"raspberry_pi_id": rpi.id, "location": rpi.location}
        )
        
        if executed_rules:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Règles exécutées après détection de présence: {len(executed_rules)}")
    except Exception as e:
        # Ne pas faire échouer l'enregistrement si les règles échouent
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de l'évaluation des règles: {e}")
    
    return {
        "id": presence.id,
        "raspberry_pi_id": presence.raspberry_pi_id,
        "raspberry_pi_name": rpi.name,
        "location": rpi.location,
        "detected_at": presence.detected_at
    }


@router.get("/", response_model=List[PresenceResponse])
async def get_presence_history(
    raspberry_pi_id: Optional[int] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère l'historique des détections de présence.
    """
    query = db.query(Presence)
    
    if raspberry_pi_id:
        query = query.filter(Presence.raspberry_pi_id == raspberry_pi_id)
    
    presences = query.order_by(
        Presence.detected_at.desc()
    ).offset(pagination.skip).limit(pagination.limit).all()
    
    result = []
    for presence in presences:
        rpi = db.query(RaspberryPi).filter(
            RaspberryPi.id == presence.raspberry_pi_id
        ).first()
        
        result.append({
            "id": presence.id,
            "raspberry_pi_id": presence.raspberry_pi_id,
            "raspberry_pi_name": rpi.name if rpi else "Unknown",
            "location": rpi.location if rpi else "Unknown",
            "detected_at": presence.detected_at
        })
    
    return result

