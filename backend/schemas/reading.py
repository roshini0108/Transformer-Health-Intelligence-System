# backend/schemas/reading.py
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

class SensorReadingCreate(BaseModel):
    transformer_id: str
    recorded_at: datetime
    load_percentage: float
    oil_temperature_c: float
    ambient_temp_c: float
    primary_voltage_kv: Optional[float] = None
    secondary_voltage_v: Optional[float] = None
    current_amps: Optional[float] = None
    power_factor: float
    harmonic_distortion: float
    is_fault_event: Optional[bool] = False

    @field_validator("load_percentage")
    @classmethod
    def validate_load(cls, v):
        if not 0 <= v <= 200:
            raise ValueError("load_percentage must be 0-200")
        return v

    @field_validator("power_factor")
    @classmethod
    def validate_pf(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("power_factor must be 0-1")
        return v

class SensorReadingResponse(SensorReadingCreate):
    id: int

    class Config:
        from_attributes = True