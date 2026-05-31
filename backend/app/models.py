from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base

class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    # Важливо: для TimescaleDB поле мітки часу має підтримувати часові пояси (TIMESTAMPTZ)
    timestamp = Column(DateTime(timezone=True), primary_key=True, default=func.now())
    device_id = Column(String, default="Линия_1")
    product_weight_g = Column(Float, nullable=False)
    metal_signal = Column(Integer, nullable=False)
    threshold = Column(Integer, default=80)
    temperature = Column(Float, nullable=False)
    is_rejected = Column(Boolean, default=False)
    status = Column(String, default="normal")

class SystemAlert(Base):
    __tablename__ = "system_alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    alert_type = Column(String, nullable=False)  # "METAL_DETECTED" або "OVERHEATING"
    message = Column(String, nullable=False)
    value = Column(Float, nullable=False)