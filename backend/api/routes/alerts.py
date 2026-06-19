# backend/api/routes/alerts.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.dependencies import get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/")
def get_alerts(
    unacknowledged_only: bool = Query(default=False),
    severity: str = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """
    Returns alerts, optionally filtered.
    Used by: Alerts page, dashboard alert count.
    """
    where_clauses = []
    params        = {"limit": limit}

    if unacknowledged_only:
        where_clauses.append("acknowledged = false")
    if severity:
        where_clauses.append("severity = :severity")
        params["severity"] = severity.upper()

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    rows = db.execute(text(f"""
        SELECT
            a.id, a.transformer_id, a.alert_type, a.severity,
            a.message, a.triggered_at, a.acknowledged, a.acknowledged_by,
            t.name as transformer_name, t.district
        FROM alerts a
        JOIN transformers t ON t.transformer_id = a.transformer_id
        {where_sql}
        ORDER BY
            CASE a.severity WHEN 'CRITICAL' THEN 1 ELSE 2 END,
            a.triggered_at DESC
        LIMIT :limit
    """), params).fetchall()

    return [dict(r._mapping) for r in rows]


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    acknowledged_by: str = Query(default="Engineer"),
    db: Session = Depends(get_db)
):
    """
    Marks an alert as acknowledged.
    Used by: Acknowledge button on Alerts page.
    """
    result = db.execute(text("""
        UPDATE alerts
        SET acknowledged = true,
            acknowledged_by = :by
        WHERE id = :id
        RETURNING id, transformer_id, acknowledged
    """), {"id": alert_id, "by": acknowledged_by}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.commit()
    return {"message": "Alert acknowledged", "alert_id": alert_id}