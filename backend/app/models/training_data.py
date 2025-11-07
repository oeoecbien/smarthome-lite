"""
Modèle ORM pour la table 'training_data'.
Dataset pour entraînement du modèle de classification de scénarios (Decision Tree).
"""
from sqlalchemy import Column, Integer, Boolean, TIMESTAMP
from sqlalchemy.sql import func

from app.database import Base


class TrainingData(Base):
    """
    Données d'entraînement pour le modèle d'IA de classification de scénarios.
    
    Features (variables d'entrée):
        - hour: Heure de la journée (0-23)
        - day_of_week: Jour de la semaine (0=lundi, 6=dimanche)
        - presence_detected: Présence détectée (booléen)
        - light_on: Lumière allumée (booléen)
        
    Target (variable de sortie):
        - scenario: Scénario classifié (0-3)
            0: Day (journée active)
            1: Night (nuit)
            2: Away (absence)
            3: Evening (soirée)
    
    Attributes:
        id: Identifiant unique
        hour: Heure (0-23)
        day_of_week: Jour (0-6)
        presence_detected: Booléen présence
        light_on: Booléen état lumière
        scenario: Label du scénario (0-3)
        created_at: Date d'ajout (automatique)
    """
    __tablename__ = "training_data"
    
    # ========== Colonnes (Features) ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hour = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    presence_detected = Column(Boolean, nullable=False)
    light_on = Column(Boolean, nullable=False)
    
    # ========== Colonne (Target) ==========
    scenario = Column(Integer, nullable=False, index=True)
    
    # Timestamp
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        return f"<TrainingData(id={self.id}, hour={self.hour}, scenario={self.scenario})>"
