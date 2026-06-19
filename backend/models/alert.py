# backend/models/alert.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id              = Column(Integer, primary_key=True, index=True)
    transformer_id  = Column(String(20), index=True)   # no ForeignKey
    alert_type      = Column(String(50))
    severity        = Column(String(10))
    message         = Column(Text)
    triggered_at    = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged    = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))