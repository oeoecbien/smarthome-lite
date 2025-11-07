"""
Schémas Pydantic pour le système de Smart Dimming.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SmartDimmingStatus(BaseModel):
    """
    Schéma pour l'état global du Smart Dimming.
    """
    enabled: bool = Field(..., description="Smart Dimming activé globalement")
    active_adjustments_count: int = Field(..., description="Nombre d'ajustements en cours")
    total_adjustments_today: int = Field(..., description="Nombre d'ajustements effectués aujourd'hui")
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "active_adjustments_count": 3,
                "total_adjustments_today": 47
            }
        }


class SmartDimmingAdjustmentResponse(BaseModel):
    """
    Schéma de réponse pour un ajustement de Smart Dimming.
    """
    id: int
    device_id: int
    device_name: str
    scenario: int
    previous_brightness: int
    target_brightness: int
    applied_brightness: int
    reason: Optional[str]
    light_level: Optional[float] = Field(None, description="Luminosité ambiante en lux")
    adjusted_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "device_id": 1,
                "device_name": "Lampe Salon",
                "scenario": 0,
                "previous_brightness": 100,
                "target_brightness": 50,
                "applied_brightness": 50,
                "reason": "High natural light (750 lux)",
                "light_level": 750.5,
                "adjusted_at": "2025-01-15T14:30:00Z"
            }
        }


class SmartDimmingConfig(BaseModel):
    """
    Schéma pour configuration du Smart Dimming.
    """
    enabled: bool = Field(..., description="Activer/désactiver le Smart Dimming")
    min_brightness: int = Field(default=10, ge=0, le=100, description="Intensité minimale (0-100)")
    max_brightness: int = Field(default=100, ge=0, le=100, description="Intensité maximale (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "min_brightness": 10,
                "max_brightness": 100
            }
        }
