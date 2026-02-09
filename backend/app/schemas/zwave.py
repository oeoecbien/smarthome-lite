"""
Schémas Pydantic pour les données Z-Wave (capteurs, appareils connus).
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ZwaveSensorData(BaseModel):
    """
    Données capteur d'un nœud Z-Wave (ex. Aeotec MultiSensor 7).
    Retourné par le RPi GET /api/nodes/{node_id}/sensor (lecture via getValue, cache driver).
    """
    success: bool = True
    device_id: Optional[int] = Field(None, description="ID de l'appareil en base (si appel via /api/devices/{id}/sensor)")
    node_id: int = Field(..., description="Node ID Z-Wave")
    motion: bool = Field(False, description="Mouvement détecté (CC 48)")
    temperature_c: Optional[float] = Field(None, description="Température (°C)")
    humidity: Optional[float] = Field(None, description="Humidité (%)")
    illuminance_lux: Optional[int] = Field(None, description="Luminosité (lux)")
    ultraviolet: Optional[float] = Field(None, description="Indice UV")
    battery_percent: Optional[int] = Field(None, description="Niveau batterie (%)")
    device_type: Optional[str] = Field(None, description="Ex: aeotec_multisensor7")
    device_name: Optional[str] = Field(None, description="Nom commercial")
    device_model: Optional[str] = Field(None, description="Modèle ex: ZWA024")
    cached: Optional[bool] = Field(None, description="True si valeur issue du cache (nœud non contacté)")
    unknown: Optional[bool] = Field(None, description="True si aucune donnée lue (nœud injoignable ou timeout)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "device_id": 18,
                "node_id": 5,
                "motion": False,
                "temperature_c": 23.5,
                "humidity": 38.0,
                "illuminance_lux": 26,
                "ultraviolet": 0.0,
                "battery_percent": 100,
                "device_type": "aeotec_multisensor7",
                "device_name": "Aeotec MultiSensor 7",
                "device_model": "ZWA024",
            }
        }


class ZwaveKnownDevice(BaseModel):
    """Appareil Z-Wave connu par le backend (registre)."""
    manufacturer_id: int
    manufacturer_name: str
    product_type: int
    product_id: int
    model: str
    name: str
    full_name: str
    sensor_capabilities: List[str] = Field(default_factory=list)
