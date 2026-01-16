"""
Modèle ORM pour la table 'users'.
Gère les utilisateurs de l'application avec authentification par mot de passe haché.
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    Représente un utilisateur du système SmartHome Lite.
    
    Attributes:
        id: Identifiant unique auto-incrémenté
        username: Nom d'utilisateur unique (50 caractères max)
        email: Adresse email unique optionnelle
        password_hash: Hash bcrypt du mot de passe (jamais stocké en clair)
        role: Rôle de l'utilisateur ('user' par défaut ou 'admin')
        created_at: Timestamp de création du compte (automatique)
        updated_at: Timestamp de dernière modification (automatique)
        
    Relations:
        preferences: Liste des préférences utilisateur pour smart dimming
    """
    __tablename__ = "users"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user", server_default="user")  # 'user' ou 'admin'
    
    # Timestamps automatiques
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, onupdate=func.now())
    
    # ========== Relations ==========
    devices = relationship(
        "Device",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    preferences = relationship(
        "UserPreference",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    bluetooth_devices = relationship(
        "BluetoothDevice",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
