# backend/schemas/prediction.py
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class PredictionResponse(BaseModel):
    id: int
    transformer_id: str
    predicted_at: datetime
    health_score: int
    failure_probability_30d: float
    risk_level: str
    anomaly_detected: bool
    anomaly_score: Optional[float] = None
    contributing_factors: Optional[Dict] = None

    class Config:
        from_attributes = True

class PredictionSummary(BaseModel):
    """Lightweight version for the dashboard overview."""
    transformer_id: str
    health_score: int
    risk_level: str
    failure_probability_30d: float
    anomaly_detected: bool
    predicted_at: datetime