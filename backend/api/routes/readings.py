# backend/api/routes/readings.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from api.dependencies import get_db
from models.reading import SensorReading
from schemas.reading import SensorReadingCreate

router = APIRouter(prefix="/readings", tags=["readings"])

@router.get("/{transformer_id}")
def get_readings(
    transformer_id: str,
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Returns time-series sensor readings for one transformer.
    Used by: Transformer detail page charts.
    """
    cutoff = datetime.now() - timedelta(days=days)

    rows = db.execute(text("""
        SELECT
            recorded_at,
            load_percentage,
            oil_temperature_c,
            ambient_temp_c,
            power_factor,
            harmonic_distortion,
            secondary_voltage_v,
            is_fault_event
        FROM sensor_readings
        WHERE transformer_id = :tid
          AND recorded_at >= :cutoff
        ORDER BY recorded_at ASC
    """), {"tid": transformer_id, "cutoff": cutoff}).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No readings found for {transformer_id} in last {days} days"
        )

    return [dict(r._mapping) for r in rows]


@router.post("/")
def create_reading(
    reading: SensorReadingCreate,
    db: Session = Depends(get_db)
):
    """
    Inserts a new sensor reading.
    Called by SCADA system or CSV importer.
    """
    db_reading = SensorReading(**reading.model_dump())
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return {"id": db_reading.id, "message": "Reading saved"}
