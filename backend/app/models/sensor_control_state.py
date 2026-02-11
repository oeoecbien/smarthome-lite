"""
État du pilotage capteur → lampe (timer extinction après mouvement).
"""
from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class SensorControlState(Base):
    """
    Mémorise la dernière détection de mouvement et la dernière absence
    pour appliquer "éteindre après X secondes sans mouvement".
    """
    __tablename__ = "sensor_control_state"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sensor_device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    target_device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    last_motion_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_motion_off_at = Column(TIMESTAMP(timezone=True), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("sensor_device_id", "target_device_id", name="uq_sensor_control_sensor_target"),
    )
