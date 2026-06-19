# backend/api/routes/predictions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.dependencies import get_db
from services.prediction_service import (
    run_prediction_for_transformer,
    run_batch_predictions
)

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.get("/")
def get_all_predictions(db: Session = Depends(get_db)):
    """
    Returns latest health score for every transformer.
    Used by: Dashboard overview cards and health ranking.
    """
    rows = db.execute(text("""
        SELECT DISTINCT ON (transformer_id)
            transformer_id,
            health_score,
            risk_level,
            failure_probability_30d,
            anomaly_detected,
            predicted_at
        FROM health_predictions
        ORDER BY transformer_id, predicted_at DESC
    """)).fetchall()

    return [dict(r._mapping) for r in rows]


@router.get("/summary")
def get_predictions_summary(db: Session = Depends(get_db)):
    """
    Returns counts by risk level for dashboard metric cards.
    e.g. { "LOW": 31, "MEDIUM": 14, "HIGH": 3, "CRITICAL": 2 }
    """
    rows = db.execute(text("""
        SELECT risk_level, COUNT(*) as count
        FROM (
            SELECT DISTINCT ON (transformer_id)
                transformer_id, risk_level
            FROM health_predictions
            ORDER BY transformer_id, predicted_at DESC
        ) latest
        GROUP BY risk_level
    """)).fetchall()

    summary = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0, "UNKNOWN": 0}
    for row in rows:
        summary[row[0]] = row[1]
    summary["total"] = sum(summary.values())
    return summary


@router.get("/{transformer_id}")
def get_transformer_predictions(
    transformer_id: str,
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Returns prediction history for one transformer.
    Used by: Transformer detail page health trend chart.
    """
    rows = db.execute(text("""
        SELECT
            transformer_id, health_score, risk_level,
            failure_probability_30d, anomaly_detected,
            anomaly_score, contributing_factors, predicted_at
        FROM health_predictions
        WHERE transformer_id = :tid
          AND predicted_at >= NOW() - INTERVAL ':days days'
        ORDER BY predicted_at ASC
    """.replace(":days", str(days))), {"tid": transformer_id}).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for {transformer_id}"
        )

    return [dict(r._mapping) for r in rows]


@router.post("/run/{transformer_id}")
def trigger_prediction(
    transformer_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually triggers a fresh ML prediction for one transformer.
    Used by: "Refresh prediction" button on detail page.
    """
    result = run_prediction_for_transformer(transformer_id, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/run-all")
def trigger_all_predictions(db: Session = Depends(get_db)):
    """
    Runs predictions for all transformers.
    Used by: batch script, manual refresh button on dashboard.
    """
    results = run_batch_predictions(db)
    return results