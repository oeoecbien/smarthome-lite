"""
Modèle ORM pour la table 'rules'.
Définit les règles d'automatisation du système.
"""
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class Rule(Base):
    """
    Règle d'automatisation pour contrôler les appareils selon des conditions.
    
    Structure des champs JSON:
    
    condition (JSONB):
        {
            "type": "AND" | "OR",
            "conditions": [
                {"type": "time", "operator": "between", "value": ["08:00", "18:00"]},
                {"type": "presence", "value": true},
                {"type": "light", "operator": "<", "value": 100}
            ]
        }
    
    action (JSONB):
        {
            "device_id": 1,
            "action": "turn_on" | "turn_off" | "set_brightness",
            "brightness": 75  // optionnel pour set_brightness
        }
    
    Attributes:
        id: Identifiant unique
        name: Nom descriptif de la règle
        description: Description détaillée (optionnelle)
        condition: Condition d'activation (format JSONB)
        action: Action à effectuer (format JSONB)
        enabled: Statut actif/inactif
        priority: Priorité d'exécution (1-100, plus élevé = prioritaire)
        created_at: Date de création
        updated_at: Date de dernière modification
        
    Note:
        Le moteur de règles évalue les conditions dans l'ordre de priorité.
        En cas de conflit, la règle de priorité supérieure l'emporte.
    """
    __tablename__ = "rules"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    condition = Column(JSONB, nullable=False)
    action = Column(JSONB, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=50, nullable=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"<Rule(id={self.id}, name='{self.name}', priority={self.priority}, {status})>"
