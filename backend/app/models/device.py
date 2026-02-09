"""
Modèle ORM pour la table 'devices'.
Représente les appareils connectés (lampes, prises, capteurs).
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Device(Base):
    """
    Représente un appareil électrique connecté.
    
    Types supportés:
        - 'light': Lampe simple ON/OFF
        - 'dimmer': Lampe dimmable avec contrôle d'intensité (0-100%)
        - 'socket': Prise connectée ON/OFF
        - 'sensor': Capteur Z-Wave (ex. Aeotec MultiSensor 7) ; gpio_pin = node_id Z-Wave
    
    Attributes:
        id: Identifiant unique
        raspberry_pi_id: Clé étrangère vers le Raspberry Pi contrôleur
        name: Nom descriptif (ex: "Lampe Bureau")
        type: Type d'appareil ('light', 'dimmer', 'socket', 'sensor')
        gpio_pin: Numéro GPIO (1-40) ou node_id Z-Wave (1-255) pour type 'sensor'
        state: État actuel (TRUE=ON, FALSE=OFF)
        brightness: Intensité lumineuse (0-100, toujours défini)
        created_at: Date d'ajout
        updated_at: Date de dernière modification
        
    Relations:
        raspberry_pi: Instance du Raspberry Pi contrôleur
        events: Historique des événements liés à cet appareil
        smart_dimming_adjustments: Historique des ajustements automatiques
        user_preferences: Préférences utilisateur associées
    """
    __tablename__ = "devices"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    raspberry_pi_id = Column(Integer, ForeignKey("raspberry_pis.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    gpio_pin = Column(Integer, nullable=False)
    state = Column(Boolean, default=False, nullable=False)
    brightness = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    
    # ========== Contraintes ==========
    __table_args__ = (
        # Vérification du type d'appareil
        CheckConstraint(
            "type IN ('light', 'dimmer', 'socket', 'sensor')",
            name="check_device_type"
        ),
        # GPIO 1-40 (RPi) ou node_id Z-Wave 1-255 (capteurs)
        CheckConstraint(
            "gpio_pin >= 1 AND gpio_pin <= 255",
            name="check_gpio_pin_range"
        ),
        # Vérification de la plage de brightness
        CheckConstraint(
            "brightness >= 0 AND brightness <= 100",
            name="check_brightness_range"
        ),
        # Contrainte unique: un GPIO par Raspberry Pi
        UniqueConstraint('raspberry_pi_id', 'gpio_pin', name='uq_device_raspberry_pi_gpio'),
    )
    
    # ========== Relations ==========
    user = relationship("User", back_populates="devices")
    raspberry_pi = relationship("RaspberryPi", back_populates="devices")
    
    events = relationship(
        "Event",
        back_populates="device",
        cascade="all, delete-orphan"
    )
    
    smart_dimming_adjustments = relationship(
        "SmartDimmingAdjustment",
        back_populates="device",
        cascade="all, delete-orphan"
    )
    
    user_preferences = relationship(
        "UserPreference",
        back_populates="device",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        state_str = "ON" if self.state else "OFF"
        brightness_str = f", {self.brightness}%"
        return f"<Device(id={self.id}, name='{self.name}', type='{self.type}', {state_str}{brightness_str})>"
