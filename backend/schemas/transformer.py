# backend/schemas/transformer.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TransformerBase(BaseModel):
    transformer_id: str
    name: str
    substation_name: Optional[str] = None
    district: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity_kva: Optional[int] = None
    installation_year: Optional[int] = None

class TransformerResponse(TransformerBase):
    id: int
    created_at: Optional[datetime] = None

    # Latest health prediction (joined in the route)
    health_score: Optional[int] = None
    risk_level: Optional[str] = None
    failure_probability: Optional[float] = None

    class Config:
        from_attributes = True