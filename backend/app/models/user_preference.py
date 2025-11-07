"""
Modèle ORM pour la table 'user_preferences'.
Enregistre les ajustements manuels pour apprentissage personnalisé.
"""
from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class UserPreference(Base):
    """
    Enregistre un ajustement manuel après un smart dimming automatique.
    
    Utilisation future:
        Ces données peuvent alimenter un modèle de régression pour personnaliser
        le comportement du smart dimming selon les préférences de chaque utilisateur.
    
    Exemple de scénario:
        1. Le système propose 50% d'intensité (auto_brightness)
        2. L'utilisateur ajuste à 70% (manual_brightness)
        3. L'enregistrement capture ce feedback
        4. Après 100+ enregistrements, un modèle peut apprendre les préférences
        
    Attributes:
        id: Identifiant unique
        user_id: Clé étrangère vers l'utilisateur
        device_id: Clé étrangère vers l'appareil ajusté
        light_level: Niveau de luminosité ambiante (lux)
        scenario: Scénario actif (0-3)
        auto_brightness: Intensité proposée par le système (0-100)
        manual_brightness: Intensité choisie par l'utilisateur (0-100)
        time_of_day: Heure de l'ajustement (0-23)
        recorded_at: Timestamp de l'enregistrement (automatique)
        
    Relations:
        user: Instance de l'utilisateur
        device: Instance de l'appareil
    """
    __tablename__ = "user_preferences"
    
    # ========== Colonnes ==========
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    light_level = Column(Float, nullable=False)
    scenario = Column(Integer, nullable=False, index=True)
    auto_brightness = Column(Integer, nullable=False)
    manual_brightness = Column(Integer, nullable=False)
    time_of_day = Column(Integer, nullable=False)
    recorded_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # ========== Contraintes ==========
    __table_args__ = (
        # Vérification de la plage de luminosité
        CheckConstraint(
            "light_level >= 0",
            name="check_light_level_range"
        ),
        # Vérification du scénario
        CheckConstraint(
            "scenario >= 0 AND scenario <= 3",
            name="check_scenario_range"
        ),
        # Vérification de la plage de brightness
        CheckConstraint(
            "auto_brightness >= 0 AND auto_brightness <= 100",
            name="check_auto_brightness_range"
        ),
        CheckConstraint(
            "manual_brightness >= 0 AND manual_brightness <= 100",
            name="check_manual_brightness_range"
        ),
        # Vérification de l'heure
        CheckConstraint(
            "time_of_day >= 0 AND time_of_day <= 23",
            name="check_time_of_day_range"
        ),
    )
    
    # ========== Relations ==========
    user = relationship("User", back_populates="preferences")
    device = relationship("Device", back_populates="user_preferences")
    
    def __repr__(self) -> str:
        diff = self.manual_brightness - self.auto_brightness
        sign = "+" if diff > 0 else ""
        return f"<UserPreference(id={self.id}, user_id={self.user_id}, {self.auto_brightness}→{self.manual_brightness} ({sign}{diff}))>"
