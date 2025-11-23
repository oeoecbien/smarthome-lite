"""
Schémas Pydantic pour gestion des Raspberry Pi.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class RaspberryPiBase(BaseModel):
    """
    Schéma de base pour Raspberry Pi.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Nom du Raspberry Pi")
    location: str = Field(..., min_length=1, max_length=100, description="Emplacement physique")
    ip_address: str = Field(..., description="Adresse IPv4")
    
    @validator("ip_address")
    def validate_ip_address(cls, v):
        """Vérifie le format de l'adresse IPv4."""
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, v):
            raise ValueError("Format d'adresse IPv4 invalide")
        
        # Vérification des octets (0-255)
        octets = v.split(".")
        if not all(0 <= int(octet) <= 255 for octet in octets):
            raise ValueError("Les octets doivent être entre 0 et 255")
        
        return v


class RaspberryPiCreate(RaspberryPiBase):
    """
    Schéma pour enregistrement d'un nouveau Raspberry Pi.
    """
    class Config:
        json_schema_extra = {
            "example": {
                "name": "RPi Salon",
                "location": "Salon",
                "ip_address": "192.168.1.100"
            }
        }


class RaspberryPiUpdate(BaseModel):
    """
    Schéma pour mise à jour d'un Raspberry Pi.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    ip_address: Optional[str] = None
    is_online: Optional[bool] = None
    
    @validator("ip_address")
    def validate_ip_address(cls, v):
        """Vérifie le format de l'adresse IPv4."""
        if v is None:
            return v
        
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, v):
            raise ValueError("Format d'adresse IPv4 invalide")
        
        octets = v.split(".")
        if not all(0 <= int(octet) <= 255 for octet in octets):
            raise ValueError("Les octets doivent être entre 0 et 255")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_online": False
            }
        }


class RaspberryPiResponse(RaspberryPiBase):
    """
    Schéma de réponse pour un Raspberry Pi.
    """
    id: int
    api_key: str
    is_online: bool
    created_at: datetime
    updated_at: datetime
    device_count: Optional[int] = Field(None, description="Nombre d'appareils connectés")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "RPi Salon",
                "location": "Salon",
                "ip_address": "192.168.1.100",
                "api_key": "a1b2c3d4e5f6...",
                "is_online": True,
                "created_at": "2025-01-10T08:00:00Z",
                "updated_at": "2025-01-15T14:30:00Z",
                "device_count": 3
            }
        }
