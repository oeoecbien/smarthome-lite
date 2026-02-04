"""
Modèle ORM pour la table 'bluetooth_devices'.
Associe les adresses MAC Bluetooth aux utilisateurs.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class BluetoothDevice(Base):
    """
    Associe une adresse MAC Bluetooth à un utilisateur.
    
    Permet d'identifier les personnes via leurs devices Bluetooth (téléphone, montre, etc.)
    et d'enrichir les détections de présence avec l'identité de l'utilisateur.
    
    Attributes:
        id: Identifiant unique
        user_id: Clé étrangère vers l'utilisateur
        mac_address: Adresse MAC du device (format: AA:BB:CC:DD:EE:FF)
        device_name: Nom du device (ex: "iPhone de Jean")
        device_type: Type de device (phone, watch, headphones, etc.)
        is_active: Si le device est actif (peut être désactivé sans suppression)
        created_at: Date de création
        updated_at: Date de dernière modification
        
    Relations:
        user: Instance de l'utilisateur
    """
    __tablename__ = "bluetooth_devices"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # 'phone', 'watch', 'headphones', etc.
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, onupdate=func.now())
    
    # ========== Relations ==========
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<BluetoothDevice(id={self.id}, user_id={self.user_id}, mac={self.mac_address}, name={self.device_name})>"
