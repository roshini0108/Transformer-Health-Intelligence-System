# backend/schemas/alert.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertResponse(BaseModel):
    id: int
    transformer_id: str
    alert_type: str
    severity: str
    message: str
    triggered_at: datetime
    acknowledged: bool
    acknowledged_by: Optional[str] = None

    class Config:
        from_attributes = True