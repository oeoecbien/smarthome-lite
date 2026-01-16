"""
Modèle ORM pour la table 'raspberry_pis'.
Représente les Raspberry Pi connectés au système.
"""
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class RaspberryPi(Base):
    """
    Représente un Raspberry Pi dans le réseau SmartHome.
    
    Attributes:
        id: Identifiant unique
        name: Nom descriptif (ex: "RPi Salon")
        location: Pièce associée (ex: "Salon", "Chambre")
        ip_address: Adresse IPv4 unique
        api_key_hash: Hash bcrypt de la clé API (jamais stockée en clair)
        is_online: Statut de connectivité (TRUE si accessible)
        created_at: Date d'ajout au système
        updated_at: Date de dernière modification
        
    Relations:
        devices: Liste des appareils connectés à ce Raspberry Pi
        presence_detections: Historique des détections de présence via Bluetooth
        light_readings: Historique des mesures de luminosité
    """
    __tablename__ = "raspberry_pis"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(15), unique=True, nullable=True)
    api_key_hash = Column(String(255), unique=True, nullable=False, index=True)
    is_online = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    
    # ========== Relations ==========
    devices = relationship(
        "Device",
        back_populates="raspberry_pi",
        cascade="all, delete-orphan"
    )
    
    presence_detections = relationship(
        "Presence",
        back_populates="raspberry_pi",
        cascade="all, delete-orphan"
    )
    
    light_readings = relationship(
        "LightReading",
        back_populates="raspberry_pi",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        status = "online" if self.is_online else "offline"
        return f"<RaspberryPi(id={self.id}, name='{self.name}', location='{self.location}', {status})>"
