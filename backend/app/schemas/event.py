"""
Schémas Pydantic pour les événements système.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class EventCreate(BaseModel):
    """
    Schéma pour création d'un événement (utilisé par Raspberry Pi).
    """
    device_id: Optional[int] = Field(None, description="ID de l'appareil concerné")
    event_type: str = Field(..., max_length=50, description="Type d'événement")
    value: Optional[str] = Field(None, max_length=100, description="Valeur associée")
    source: Literal["manual", "automatic", "ai", "system", "smart_dimming"] = Field(
        ...,
        description="Source de l'événement"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "event_type": "brightness_changed",
                "value": "75",
                "source": "smart_dimming"
            }
        }


class EventResponse(BaseModel):
    """
    Schéma de réponse pour un événement.
    """
    id: int
    device_id: Optional[int]
    device_name: Optional[str] = Field(None, description="Nom de l'appareil")
    event_type: str
    value: Optional[str]
    source: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 456,
                "device_id": 1,
                "device_name": "Lampe Salon",
                "event_type": "brightness_changed",
                "value": "75",
                "source": "smart_dimming",
                "timestamp": "2025-01-15T14:30:00Z"
            }
        }
