"""
Modèle ORM pour la table 'presence'.
Enregistre les détections de mouvement des capteurs PIR.
"""
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Presence(Base):
    """
    Enregistre une détection de présence par capteur PIR.
    
    Attributes:
        id: Identifiant unique
        raspberry_pi_id: Clé étrangère vers le Raspberry Pi équipé du capteur
        detected_at: Timestamp de la détection (automatique)
        
    Relations:
        raspberry_pi: Instance du Raspberry Pi source
        
    Note:
        Chaque enregistrement représente UNE détection.
        L'absence de détection pendant X minutes peut déclencher un scénario "Away".
    """
    __tablename__ = "presence"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    raspberry_pi_id = Column(Integer, ForeignKey("raspberry_pis.id", ondelete="CASCADE"), nullable=False)
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # ========== Relations ==========
    raspberry_pi = relationship("RaspberryPi", back_populates="presence_detections")
    
    def __repr__(self) -> str:
        return f"<Presence(id={self.id}, raspberry_pi_id={self.raspberry_pi_id}, detected_at={self.detected_at})>"
