"""
Modèle ORM pour la table 'presence'.
Enregistre les détections de présence via Bluetooth.
"""
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional

from app.database import Base


class Presence(Base):
    """
    Enregistre une détection de présence via Bluetooth.
    
    Attributes:
        id: Identifiant unique
        raspberry_pi_id: Clé étrangère vers le Raspberry Pi équipé du capteur
        detected_at: Timestamp de la détection (automatique)
        device_mac_address: Adresse MAC du device Bluetooth détecté (optionnel)
        signal_strength: Force du signal RSSI en dBm (optionnel)
        user_id: ID de l'utilisateur associé (optionnel, si MAC mappée)
        
    Relations:
        raspberry_pi: Instance du Raspberry Pi source
        user: Instance de l'utilisateur (si user_id défini)
        
    Note:
        Chaque enregistrement représente UNE détection.
        L'absence de détection pendant X minutes peut déclencher un scénario "Away".
        Le device_mac_address permet d'identifier et classifier les personnes.
    """
    __tablename__ = "presence"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    raspberry_pi_id = Column(Integer, ForeignKey("raspberry_pis.id", ondelete="CASCADE"), nullable=False)
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Colonnes Bluetooth
    device_mac_address = Column(String(17), nullable=True, index=True)  # Format: "AA:BB:CC:DD:EE:FF"
    signal_strength = Column(Integer, nullable=True)  # RSSI en dBm
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # ========== Relations ==========
    raspberry_pi = relationship("RaspberryPi", back_populates="presence_detections")
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        mac_info = f", mac={self.device_mac_address}" if self.device_mac_address else ""
        user_info = f", user_id={self.user_id}" if self.user_id else ""
        return f"<Presence(id={self.id}, raspberry_pi_id={self.raspberry_pi_id}{mac_info}{user_info}, detected_at={self.detected_at})>"
