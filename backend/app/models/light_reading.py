"""
Modèle ORM pour la table 'light_readings'.
Enregistre les mesures de luminosité ambiante (en lux).
"""
from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class LightReading(Base):
    """
    Mesure de luminosité ambiante capturée par un capteur (LDR ou BH1750).
    
    Attributes:
        id: Identifiant unique
        raspberry_pi_id: Clé étrangère vers le Raspberry Pi équipé du capteur
        lux: Valeur de luminosité en lux (0-65535)
        measured_at: Timestamp de la mesure (automatique)
        
    Relations:
        raspberry_pi: Instance du Raspberry Pi source
        smart_dimming_adjustments: Ajustements déclenchés par cette mesure
        
    Note:
        Valeurs typiques:
        - 0-50 lux: Obscurité/nuit
        - 50-200 lux: Éclairage faible
        - 200-500 lux: Éclairage moyen
        - 500+ lux: Forte luminosité naturelle
    """
    __tablename__ = "light_readings"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    raspberry_pi_id = Column(Integer, ForeignKey("raspberry_pis.id", ondelete="CASCADE"), nullable=False)
    lux = Column(Float, nullable=False)
    measured_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # ========== Relations ==========
    raspberry_pi = relationship("RaspberryPi", back_populates="light_readings")
    
    smart_dimming_adjustments = relationship(
        "SmartDimmingAdjustment",
        back_populates="light_reading"
    )
    
    def __repr__(self) -> str:
        return f"<LightReading(id={self.id}, lux={self.lux:.2f}, measured_at={self.measured_at})>"
