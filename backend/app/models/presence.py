"""
Modèle ORM pour la table 'presence'.
Enregistre les détections de présence via capteur de mouvement (MultiSensor7 Z-Wave).
"""
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Presence(Base):
    """
    Enregistre une détection de mouvement (MultiSensor7 ou autre capteur Z-Wave).
    
    Attributes:
        id: Identifiant unique
        raspberry_pi_id: Clé étrangère vers le Raspberry Pi qui reçoit les événements Z-Wave
        detected_at: Timestamp de la détection (automatique)
        sensor_node_id: Node ID Z-Wave du capteur (ex: MultiSensor7), optionnel
        
    Relations:
        raspberry_pi: Instance du Raspberry Pi source
        
    Note:
        Chaque enregistrement représente UNE détection de mouvement.
        L'absence de détection pendant X minutes peut déclencher un scénario "Away".
    """
    __tablename__ = "presence"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    raspberry_pi_id = Column(Integer, ForeignKey("raspberry_pis.id", ondelete="RESTRICT"), nullable=False)
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    sensor_node_id = Column(Integer, nullable=True)
    
    raspberry_pi = relationship("RaspberryPi", back_populates="presence_detections")
    
    def __repr__(self) -> str:
        node = f", node={self.sensor_node_id}" if self.sensor_node_id else ""
        return f"<Presence(id={self.id}, raspberry_pi_id={self.raspberry_pi_id}{node}, detected_at={self.detected_at})>"
