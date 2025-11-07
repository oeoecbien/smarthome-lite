"""
Schémas Pydantic pour règles d'automatisation.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class RuleCondition(BaseModel):
    """
    Structure d'une condition de règle.
    
    Exemple:
        {
            "type": "AND",
            "conditions": [
                {"type": "time", "operator": "between", "value": ["08:00", "18:00"]},
                {"type": "presence", "value": true}
            ]
        }
    """
    type: str = Field(..., description="Type de condition (AND, OR, time, presence, light)")
    operator: Optional[str] = Field(None, description="Opérateur de comparaison (<, >, =, between)")
    value: Any = Field(..., description="Valeur de comparaison (flexible)")
    conditions: Optional[List[Dict[str, Any]]] = Field(None, description="Sous-conditions pour AND/OR")


class RuleAction(BaseModel):
    """
    Structure d'une action de règle.
    
    Exemple:
        {
            "device_id": 1,
            "action": "set_brightness",
            "brightness": 75
        }
    """
    device_id: int = Field(..., gt=0, description="ID de l'appareil cible")
    action: str = Field(..., description="Action à effectuer (turn_on, turn_off, set_brightness)")
    brightness: Optional[int] = Field(None, ge=0, le=100, description="Intensité (pour set_brightness)")
    
    @validator("action")
    def validate_action(cls, v):
        """Vérifie que l'action est valide."""
        allowed_actions = ["turn_on", "turn_off", "set_brightness"]
        if v not in allowed_actions:
            raise ValueError(f"Action doit être parmi: {', '.join(allowed_actions)}")
        return v


class RuleBase(BaseModel):
    """
    Schéma de base pour les règles.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Nom de la règle")
    description: Optional[str] = Field(None, description="Description détaillée")
    enabled: bool = Field(default=True, description="Statut actif/inactif")
    priority: int = Field(default=5, ge=1, le=10, description="Priorité (1-10)")


class RuleCreate(RuleBase):
    """
    Schéma pour création d'une nouvelle règle.
    """
    condition: Dict[str, Any] = Field(..., description="Condition d'activation (JSON)")
    action: Dict[str, Any] = Field(..., description="Action à effectuer (JSON)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Lumière automatique jour",
                "description": "Allume la lampe du salon à 50% entre 8h et 18h si présence détectée",
                "condition": {
                    "type": "AND",
                    "conditions": [
                        {"type": "time", "operator": "between", "value": ["08:00", "18:00"]},
                        {"type": "presence", "value": True}
                    ]
                },
                "action": {
                    "device_id": 1,
                    "action": "set_brightness",
                    "brightness": 50
                },
                "enabled": True,
                "priority": 60
            }
        }


class RuleUpdate(BaseModel):
    """
    Schéma pour mise à jour partielle d'une règle.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled": False
            }
        }


class RuleResponse(RuleBase):
    """
    Schéma de réponse pour une règle.
    """
    id: int
    condition: Dict[str, Any]
    action: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Lumière automatique jour",
                "description": "Allume la lampe du salon à 50% entre 8h et 18h si présence détectée",
                "condition": {
                    "type": "AND",
                    "conditions": [
                        {"type": "time", "operator": "between", "value": ["08:00", "18:00"]},
                        {"type": "presence", "value": True}
                    ]
                },
                "action": {
                    "device_id": 1,
                    "action": "set_brightness",
                    "brightness": 50
                },
                "enabled": True,
                "priority": 8,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z"
            }
        }
