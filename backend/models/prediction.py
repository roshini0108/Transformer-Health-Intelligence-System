# backend/models/prediction.py
from sqlalchemy import Column, BigInteger, String, Integer, Numeric, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from database import Base

class HealthPrediction(Base):
    __tablename__ = "health_predictions"

    id                      = Column(BigInteger, primary_key=True, index=True)
    transformer_id          = Column(String(20), index=True)   # no ForeignKey
    predicted_at            = Column(DateTime(timezone=True), server_default=func.now())
    health_score            = Column(Integer)
    failure_probability_30d = Column(Numeric(5, 4))
    risk_level              = Column(String(10))
    anomaly_detected        = Column(Boolean, default=False)
    anomaly_score           = Column(Numeric(8, 4))
    contributing_factors    = Column(JSON)