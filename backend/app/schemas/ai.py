"""
Schémas Pydantic pour les requêtes/réponses IA (classification et Ollama).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# Schémas pour Ollama
class OllamaGenerateRequest(BaseModel):
    """Requête pour génération de texte via Ollama."""
    prompt: str = Field(..., description="Prompt à envoyer au modèle")
    model: Optional[str] = Field(None, description="Modèle à utiliser (optionnel)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Température pour la génération")


class OllamaGenerateResponse(BaseModel):
    """Réponse avec le texte généré par Ollama."""
    response: str = Field(..., description="Texte généré")
    model: str = Field(..., description="Modèle utilisé")
    done: bool = Field(..., description="Indique si la génération est terminée")


class ScenarioDescriptionRequest(BaseModel):
    """Requête pour génération de description de scénario."""
    scenario_data: Dict[str, Any] = Field(
        ...,
        description="Métadonnées du scénario (heure, luminosité, présence, scénario, etc.)"
    )


class RuleParseRequest(BaseModel):
    """Requête pour parsing de règle en langage naturel."""
    user_text: str = Field(..., min_length=1, description="Règle en langage naturel")


class RuleParseResponse(BaseModel):
    """Réponse avec la règle structurée."""
    structured_rule: Dict[str, Any] = Field(..., description="Règle structurée en JSON")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confiance du parsing")


class RecommendationsResponse(BaseModel):
    """Réponse avec les recommandations générées."""
    recommendations: List[str] = Field(..., description="Liste de recommandations textuelles")
