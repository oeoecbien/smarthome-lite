"""
Modèle ORM pour la table 'smart_dimming_adjustments'.
Enregistre les ajustements automatiques d'intensité lumineuse.
"""
from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class SmartDimmingAdjustment(Base):
    """
    Enregistre un ajustement automatique d'intensité lumineuse.
    
    Permet d'analyser:
        - L'efficacité de l'algorithme de smart dimming
        - Les patterns d'adaptation à la luminosité ambiante
        - Les écarts entre intensité calculée et appliquée
        
    Attributes:
        id: Identifiant unique
        device_id: Clé étrangère vers l'appareil ajusté
        light_reading_id: Clé étrangère vers la mesure de luminosité déclenchante
        scenario: Scénario actif au moment de l'ajustement (0-3)
        previous_brightness: Intensité avant ajustement (0-100)
        target_brightness: Intensité calculée par l'algorithme (0-100)
        applied_brightness: Intensité réellement appliquée (0-100)
        reason: Justification textuelle (ex: "High natural light")
        adjusted_at: Timestamp de l'ajustement (automatique)
        
    Relations:
        device: Instance de l'appareil ajusté
        light_reading: Mesure de luminosité ayant déclenché l'ajustement
    """
    __tablename__ = "smart_dimming_adjustments"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    light_reading_id = Column(Integer, ForeignKey("light_readings.id", ondelete="SET NULL"), nullable=True)
    scenario = Column(Integer, nullable=False)
    previous_brightness = Column(Integer, nullable=False)
    target_brightness = Column(Integer, nullable=False)
    applied_brightness = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    adjusted_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # ========== Relations ==========
    device = relationship("Device", back_populates="smart_dimming_adjustments")
    light_reading = relationship("LightReading", back_populates="smart_dimming_adjustments")
    
    def __repr__(self) -> str:
        return f"<SmartDimmingAdjustment(id={self.id}, device_id={self.device_id}, {self.previous_brightness}→{self.applied_brightness}%)>"
