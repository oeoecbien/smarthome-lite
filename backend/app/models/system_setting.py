"""
Modèle ORM pour la table 'system_settings'.
Paramètres globaux persistés en BDD (ex. smart_dimming_enabled).
"""
from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.sql import func

from app.database import Base


class SystemSetting(Base):
    """
    Stocke un paramètre système clé/valeur.

    Permet de persister des options (ex. smart_dimming_enabled) au-delà
    du fichier .env, pour survivre aux redémarrages et être partagé entre workers.
    """
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<SystemSetting(key={self.key!r}, value={self.value!r})>"
