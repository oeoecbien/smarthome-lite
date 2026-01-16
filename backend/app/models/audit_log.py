"""
Modèle ORM pour la table 'audit_log'.
Journal d'audit pour traçabilité des modifications sensibles.
"""

from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class AuditLog(Base):
    """
    Représente une entrée dans le journal d'audit.
    
    Attributes:
        id: Identifiant unique
        user_id: ID de l'utilisateur ayant effectué l'action (peut être NULL)
        action_type: Type d'action (INSERT, UPDATE, DELETE, LOGIN, LOGOUT, FAILED_LOGIN)
        table_name: Nom de la table modifiée
        record_id: ID de l'enregistrement modifié
        old_values: Valeurs avant modification (JSON)
        new_values: Valeurs après modification (JSON)
        ip_address: Adresse IP de la requête
        user_agent: User-Agent de la requête
        created_at: Timestamp de l'action
    """
    __tablename__ = "audit_log"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(Integer, nullable=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action_type}, table={self.table_name}, user_id={self.user_id})>"
