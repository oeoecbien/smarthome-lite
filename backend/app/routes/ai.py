"""
Routes pour l'Intelligence Artificielle - Classification de scénarios.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user, User
from app.services.ai_service import get_ai_service

router = APIRouter()


class ClassifyRequest(BaseModel):
    """Requête pour classification manuelle."""
    hour: int
    day_of_week: int
    presence_detected: bool
    light_on: bool


class ScenarioResponse(BaseModel):
    """Réponse avec le scénario classifié."""
    scenario: int
    scenario_name: str
    confidence: float
    method: str
    context: dict


@router.get("/current-scenario", response_model=ScenarioResponse)
async def get_current_scenario(
    raspberry_pi_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtient le scénario actuel classifié par l'IA.
    
    Args:
        raspberry_pi_id: ID du Raspberry Pi (optionnel, pour filtrer par localisation)
    """
    ai_service = get_ai_service()
    result = ai_service.get_current_scenario(db, raspberry_pi_id=raspberry_pi_id)
    return result


@router.post("/classify", response_model=ScenarioResponse)
async def classify_scenario(
    request: ClassifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Classification manuelle d'un scénario avec des paramètres spécifiques.
    
    Utile pour tester le modèle ou obtenir une classification pour un contexte donné.
    """
    # Validation des paramètres
    if not (0 <= request.hour <= 23):
        raise HTTPException(status_code=400, detail="hour doit être entre 0 et 23")
    
    if not (0 <= request.day_of_week <= 6):
        raise HTTPException(status_code=400, detail="day_of_week doit être entre 0 et 6")
    
    ai_service = get_ai_service()
    result = ai_service.classify(
        request.hour,
        request.day_of_week,
        request.presence_detected,
        request.light_on
    )
    
    # Ajouter le contexte
    result["context"] = {
        "hour": request.hour,
        "day_of_week": request.day_of_week,
        "presence_detected": request.presence_detected,
        "light_on": request.light_on
    }
    
    return result

