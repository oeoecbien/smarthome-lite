"""
Schémas Pydantic pour gestion des appareils.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Literal
from datetime import datetime


class DeviceBase(BaseModel):
    """
    Schéma de base pour un appareil.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Nom de l'appareil")
    type: Literal["light", "dimmer", "socket", "sensor"] = Field(..., description="Type d'appareil")
    gpio_pin: int = Field(..., ge=1, le=255, description="Numéro GPIO (1-40) ou node_id Z-Wave (1-255) pour sensor")
    raspberry_pi_id: int = Field(..., description="ID du Raspberry Pi contrôleur")
    # Note: user_id est automatiquement défini depuis le token JWT, pas besoin de le passer


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
    type: Optional[Literal["light", "dimmer", "socket", "sensor"]] = None
    gpio_pin: Optional[int] = Field(None, ge=1, le=255)
    controlled_by_sensor_id: Optional[int] = Field(None, description="ID du capteur qui pilote cette lampe (null = désactivé)")
    sensor_rules: Optional[Dict[str, Any]] = Field(
        None,
        description='Règles: motion { on_brightness, off_after_seconds }, illuminance { below_lux, brightness, above_lux }',
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Lampe Bureau Modifiée",
                "sensor_rules": {
                    "motion": {"on_brightness": 80, "off_after_seconds": 300},
                    "illuminance": {"below_lux": 100, "brightness": 60, "above_lux": 2000},
                },
            }
        }


class Device(BaseModel):
    """
    Schéma de réponse pour un appareil.
    """
    id: int
    user_id: int
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
    brightness: Optional[int] = Field(None, ge=0, le=100, description="Intensité lumineuse (0-100), pour reprendre la valeur à l'allumage")
    
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
    Le frontend envoie 0-100 ; le backend envoie 0-99 au RPi (compatibilité Z-Wave).
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
    Inclut des champs debug (raspberry_pi_id, user_id, created_at, updated_at) utiles pour l'admin.
    """
    id: int
    name: str
    type: str
    state: bool
    brightness: int
    raspberry_pi_id: int
    raspberry_pi_name: str
    location: str
    raspberry_pi_online: bool
    gpio_pin: Optional[int] = None
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    controlled_by_sensor_id: Optional[int] = None
    sensor_rules: Optional[Dict[str, Any]] = None
    controlled_by_sensor_name: Optional[str] = None
    
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

