from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, text
from .database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    time = Column(DateTime(timezone=True), primary_key=True, server_default=text("NOW()"))
    device_id = Column(String, primary_key=True)
    metric = Column(String, primary_key=True)
    value = Column(Float, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    device_id = Column(String, nullable=False)
    metric = Column(String, nullable=False)
    severity = Column(String, nullable=False, server_default="warning")
    alert_type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    value = Column(Float)
    threshold = Column(Float)
    acknowledged = Column(Boolean, nullable=False, server_default="false")
    acknowledged_at = Column(DateTime(timezone=True))
