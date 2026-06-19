# backend/models/reading.py
from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, Boolean
from database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id                  = Column(BigInteger, primary_key=True, index=True)
    transformer_id      = Column(String(20), index=True)   # no ForeignKey — keeps it simple
    recorded_at         = Column(DateTime, nullable=False, index=True)
    load_percentage     = Column(Numeric(5, 2))
    oil_temperature_c   = Column(Numeric(5, 2))
    ambient_temp_c      = Column(Numeric(5, 2))
    primary_voltage_kv  = Column(Numeric(8, 3))
    secondary_voltage_v = Column(Numeric(8, 2))
    current_amps        = Column(Numeric(8, 2))
    power_factor        = Column(Numeric(4, 3))
    harmonic_distortion = Column(Numeric(5, 2))
    is_fault_event      = Column(Boolean, default=False)