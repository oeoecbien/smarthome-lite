"""
Package contenant tous les modèles SQLAlchemy.
Import centralisé pour faciliter les migrations Alembic.
"""
from app.models.user import User
from app.models.raspberry_pi import RaspberryPi
from app.models.device import Device
from app.models.presence import Presence
from app.models.light_reading import LightReading
from app.models.event import Event
from app.models.rule import Rule
from app.models.training_data import TrainingData
from app.models.smart_dimming_adjustment import SmartDimmingAdjustment
from app.models.user_preference import UserPreference

__all__ = [
    "User",
    "RaspberryPi",
    "Device",
    "Presence",
    "LightReading",
    "Event",
    "Rule",
    "TrainingData",
    "SmartDimmingAdjustment",
    "UserPreference"
]
