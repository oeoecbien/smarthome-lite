"""
Schémas Pydantic pour gestion des appareils.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class DeviceBase(BaseModel):
    """
    Schéma de base pour un appareil.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Nom de l'appareil")
    type: Literal["light", "dimmer", "socket"] = Field(..., description="Type d'appareil")
    gpio_pin: int = Field(..., ge=1, le=40, description="Numéro GPIO (1-40)")
    raspberry_pi_id: int = Field(..., description="ID du Raspberry Pi contrôleur")


class DeviceCreate(DeviceBase):
    """
    Schéma pour création d'un nouvel appareil.
    """
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Lampe Bureau",
                "type": "dimmer",
                "gpio_pin": 18,
                "raspberry_pi_id": 1
            }
        }


class DeviceUpdate(BaseModel):
    """
    Schéma pour mise à jour d'un appareil.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[Literal["light", "dimmer", "socket"]] = None
    gpio_pin: Optional[int] = Field(None, ge=1, le=40)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Lampe Bureau Modifiée"
            }
        }


class Device(BaseModel):
    """
    Schéma de réponse pour un appareil.
    """
    id: int
    name: str
    type: str
    gpio_pin: int
    state: bool
    brightness: int
    raspberry_pi_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Lampe Bureau",
                "type": "dimmer",
                "gpio_pin": 18,
                "state": True,
                "brightness": 75,
                "raspberry_pi_id": 1,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T14:30:00Z"
            }
        }


class DeviceState(BaseModel):
    """
    Schéma pour changement d'état d'un appareil.
    """
    state: bool = Field(..., description="État ON/OFF")
    brightness: Optional[int] = Field(None, ge=0, le=100, description="Intensité lumineuse (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "state": True,
                "brightness": 80
            }
        }


class DeviceBrightness(BaseModel):
    """
    Schéma pour changement d'intensité lumineuse.
    """
    brightness: int = Field(..., ge=0, le=100, description="Intensité lumineuse (0-100)")
    transition: Optional[int] = Field(None, ge=0, description="Durée de transition en secondes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brightness": 75,
                "transition": 2
            }
        }


class DeviceWithLocation(BaseModel):
    """
    Schéma de réponse pour un appareil avec informations de localisation.
    """
    id: int
    name: str
    type: str
    state: bool
    brightness: int
    raspberry_pi_name: str
    location: str
    raspberry_pi_online: bool
    gpio_pin: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Lampe Bureau",
                "type": "dimmer",
                "state": True,
                "brightness": 75,
                "raspberry_pi_name": "RPi Salon",
                "location": "Salon",
                "raspberry_pi_online": True,
                "gpio_pin": 18,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T14:30:00Z"
            }
        }

