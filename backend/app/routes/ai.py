"""
Routes pour l'Intelligence Artificielle - Classification de scénarios.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user, User
from app.services.ai_service import get_ai_service
from app.services.regression_service import get_regression_service
from app.services.ollama_service import OllamaService
from app.schemas.ai import (
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    ScenarioDescriptionRequest,
    RuleParseRequest,
    RuleParseResponse,
    RecommendationsResponse
)
from app.config import settings

router = APIRouter()

# Instance globale du service Ollama
_ollama_service = None


def get_ollama_service() -> OllamaService:
    """Obtient l'instance globale du service Ollama (singleton)."""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service


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


class ModelMetricsResponse(BaseModel):
    """Réponse avec les métriques du modèle."""
    model_loaded: bool
    model_path: str
    accuracy: Optional[float] = None
    method: str
    features_count: int
    scenarios: dict


@router.get("/model-metrics", response_model=ModelMetricsResponse)
async def get_model_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtient les métriques du modèle IA (accuracy, etc.).
    
    Retourne des informations sur le modèle chargé et ses performances.
    """
    ai_service = get_ai_service()
    
    model_loaded = ai_service.model is not None
    model_path = settings.ml_model_path
    
    # Si le modèle est chargé, essayer d'obtenir des métriques
    accuracy = None
    method = "ml" if model_loaded else "fallback"
    
    if model_loaded:
        # Pour obtenir l'accuracy, il faudrait réentraîner ou charger depuis un fichier de métriques
        # Pour l'instant, on retourne None et on indique que le modèle est chargé
        try:
            # Essayer de charger les métriques depuis un fichier (si disponible)
            import os
            import json
            metrics_file = os.path.join(os.path.dirname(model_path), "metrics.json")
            if os.path.exists(metrics_file):
                with open(metrics_file, "r") as f:
                    metrics = json.load(f)
                    accuracy = metrics.get("accuracy")
        except Exception:
            pass
    
    return {
        "model_loaded": model_loaded,
        "model_path": model_path,
        "accuracy": accuracy,
        "method": method,
        "features_count": 4,  # hour, day_of_week, presence_detected, light_on
        "scenarios": {
            0: "Day",
            1: "Night",
            2: "Away",
            3: "Evening"
            }
    }


class PredictIntensityRequest(BaseModel):
    """Requête pour prédiction d'intensité."""
    hour: int
    day_of_week: int
    lux_value: float
    presence_detected: bool
    scenario: int


class PredictIntensityResponse(BaseModel):
    """Réponse avec l'intensité prédite."""
    intensity: int
    confidence: float
    method: str


@router.post("/predict-intensity", response_model=PredictIntensityResponse)
async def predict_intensity(
    request: PredictIntensityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Prédit l'intensité lumineuse optimale selon le contexte.
    
    Utilise un modèle de régression (Random Forest) pour prédire l'intensité
    optimale basée sur l'heure, la luminosité ambiante, la présence et le scénario.
    """
    # Validation des paramètres
    if not (0 <= request.hour <= 23):
        raise HTTPException(status_code=400, detail="hour doit être entre 0 et 23")
    
    if not (0 <= request.day_of_week <= 6):
        raise HTTPException(status_code=400, detail="day_of_week doit être entre 0 et 6")
    
    if request.lux_value < 0:
        raise HTTPException(status_code=400, detail="lux_value doit être >= 0")
    
    if not (0 <= request.scenario <= 3):
        raise HTTPException(status_code=400, detail="scenario doit être entre 0 et 3")
    
    regression_service = get_regression_service()
    result = regression_service.predict_intensity(
        request.hour,
        request.day_of_week,
        request.lux_value,
        request.presence_detected,
        request.scenario
    )
    
    return result


# ============================================================================
# ENDPOINTS OLLAMA (IA générative)
# ============================================================================

@router.post("/ollama/generate", response_model=OllamaGenerateResponse)
async def ollama_generate(
    request: OllamaGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Génère du texte via Ollama (endpoint générique).
    
    Authentification requise (JWT).
    """
    ollama_service = get_ollama_service()
    
    if not ollama_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Service Ollama non configuré (OLLAMA_BASE_URL non défini)"
        )
    
    model = request.model or ollama_service.model
    result = ollama_service.generate_text(request.prompt, model)
    
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="Erreur lors de la génération de texte via Ollama"
        )
    
    return {
        "response": result,
        "model": model,
        "done": True
    }


@router.post("/ollama/scenario-description")
async def ollama_scenario_description(
    request: ScenarioDescriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Génère une description intelligente d'un scénario détecté.
    """
    ollama_service = get_ollama_service()
    description = ollama_service.generate_scenario_description(request.scenario_data)
    
    return {"description": description}


@router.post("/ollama/parse-rule", response_model=RuleParseResponse)
async def ollama_parse_rule(
    request: RuleParseRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Convertit une règle en langage naturel → structure JSON.
    """
    ollama_service = get_ollama_service()
    
    if not ollama_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Service Ollama non configuré"
        )
    
    structured_rule = ollama_service.parse_rule_from_text(request.user_text)
    
    if structured_rule is None:
        raise HTTPException(
            status_code=400,
            detail="Impossible de parser la règle. Vérifiez le format du texte."
        )
    
    return {
        "structured_rule": structured_rule,
        "confidence": 0.8  # Confiance par défaut
    }


@router.get("/ollama/recommendations", response_model=RecommendationsResponse)
async def ollama_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Génère des recommandations personnalisées pour l'utilisateur connecté.
    """
    ollama_service = get_ollama_service()
    
    if not ollama_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="Service Ollama non configuré"
        )
    
    # Récupérer l'historique utilisateur depuis la base de données
    from app.models import Device, SmartDimmingAdjustment
    from sqlalchemy import func
    
    # Calculer quelques statistiques
    user_history = {}
    
    # Intensité moyenne
    avg_brightness = db.query(func.avg(Device.brightness)).filter(
        Device.state == True
    ).scalar() or 50
    user_history["average_brightness"] = float(avg_brightness)
    
    # Nombre d'ajustements
    adjustment_count = db.query(func.count(SmartDimmingAdjustment.id)).scalar() or 0
    user_history["adjustment_count"] = int(adjustment_count)
    
    recommendations = ollama_service.generate_recommendations(user_history)
    
    if not recommendations:
        # Recommandations par défaut si Ollama échoue
        recommendations = [
            "Vérifiez que les capteurs de luminosité sont bien calibrés",
            "Ajustez les seuils de smart dimming selon vos préférences"
        ]
    
    return {"recommendations": recommendations}
