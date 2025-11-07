"""
Modèle ORM pour la table 'events'.
Historique de tous les événements système (changements d'état, ajustements, etc.).
"""
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Event(Base):
    """
    Enregistre un événement système pour traçabilité et analyse.
    
    Types d'événements:
        - 'state_changed': Changement ON/OFF d'un appareil
        - 'brightness_changed': Modification de l'intensité lumineuse
        - 'presence_detected': Détection de mouvement
        - 'rule_triggered': Activation d'une règle automatique
        
    Sources possibles:
        - 'manual': Action utilisateur via application mobile
        - 'automatic': Déclenchement par règle automatique
        - 'smart_dimming': Ajustement par algorithme de smart dimming
        - 'ai': Décision du système d'IA
        
    Attributes:
        id: Identifiant unique
        device_id: Clé étrangère vers l'appareil concerné (NULL pour événements système)
        event_type: Type d'événement (voir liste ci-dessus)
        value: Valeur associée (ex: "true", "75", "motion")
        source: Origine de l'événement (voir liste ci-dessus)
        timestamp: Horodatage de l'événement (automatique)
        
    Relations:
        device: Instance de l'appareil concerné
    """
    __tablename__ = "events"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    value = Column(Text, nullable=True)  # Format flexible (JSON, string, nombre)
    source = Column(String(50), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # ========== Relations ==========
    device = relationship("Device", back_populates="events")
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type='{self.event_type}', source='{self.source}', timestamp={self.timestamp})>"
