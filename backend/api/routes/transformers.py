# backend/api/routes/transformers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from api.dependencies import get_db

router = APIRouter(prefix="/transformers", tags=["transformers"])

@router.get("/")
def get_all_transformers(db: Session = Depends(get_db)):
    """
    Returns all transformers with their latest health score.
    Used by: Dashboard overview, Transformer map.
    """
    rows = db.execute(text("""
        SELECT
            t.transformer_id,
            t.name,
            t.district,
            t.substation_name,
            t.latitude,
            t.longitude,
            t.capacity_kva,
            t.installation_year,
            p.health_score,
            p.risk_level,
            p.failure_probability_30d,
            p.anomaly_detected,
            p.predicted_at
        FROM transformers t
        LEFT JOIN LATERAL (
            SELECT health_score, risk_level,
                   failure_probability_30d, anomaly_detected, predicted_at
            FROM health_predictions
            WHERE transformer_id = t.transformer_id
            ORDER BY predicted_at DESC
            LIMIT 1
        ) p ON true
        ORDER BY
            CASE p.risk_level
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH'     THEN 2
                WHEN 'MEDIUM'   THEN 3
                WHEN 'LOW'      THEN 4
                ELSE 5
            END,
            p.health_score ASC NULLS LAST
    """)).fetchall()

    return [dict(r._mapping) for r in rows]


@router.get("/{transformer_id}")
def get_transformer_detail(
    transformer_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns full detail for one transformer.
    Used by: Transformer detail page.
    """
    transformer = db.execute(text("""
        SELECT * FROM transformers
        WHERE transformer_id = :tid
    """), {"tid": transformer_id}).fetchone()

    if not transformer:
        raise HTTPException(status_code=404, detail=f"Transformer {transformer_id} not found")

    # Latest prediction
    prediction = db.execute(text("""
        SELECT * FROM health_predictions
        WHERE transformer_id = :tid
        ORDER BY predicted_at DESC
        LIMIT 1
    """), {"tid": transformer_id}).fetchone()

    # Recent alerts (last 30 days)
    alerts = db.execute(text("""
        SELECT * FROM alerts
        WHERE transformer_id = :tid
          AND triggered_at >= NOW() - INTERVAL '30 days'
        ORDER BY triggered_at DESC
        LIMIT 10
    """), {"tid": transformer_id}).fetchall()

    return {
        "transformer": dict(transformer._mapping),
        "latest_prediction": dict(prediction._mapping) if prediction else None,
        "recent_alerts": [dict(a._mapping) for a in alerts],
    }