# backend/services/prediction_service.py
# Core service that:
# 1. Fetches latest sensor readings for a transformer from DB
# 2. Builds the feature dict the ML model needs
# 3. Calls health_scorer.compute_health_score()
# 4. Saves result to health_predictions table
# 5. Triggers alerts if thresholds crossed

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from models.prediction import HealthPrediction
from models.alert import Alert


def get_latest_features(transformer_id: str, db: Session) -> dict | None:
    """
    Fetches the last 30 days of sensor readings for a transformer
    and computes all engineered features needed by the ML model.
    """

    # Find the latest date available for this transformer
    # (handles synthetic/historical data that doesn't go up to today)
    latest_date_row = db.execute(text("""
        SELECT MAX(recorded_at)
        FROM sensor_readings
        WHERE transformer_id = :tid
    """), {"tid": transformer_id}).fetchone()

    if not latest_date_row or not latest_date_row[0]:
        return None

    latest_date     = latest_date_row[0]
    thirty_days_ago = latest_date - timedelta(days=30)
    result = db.execute(text("""
        SELECT
            load_percentage, oil_temperature_c, ambient_temp_c,
            power_factor, harmonic_distortion, primary_voltage_kv,
            secondary_voltage_v, current_amps, is_fault_event,
            recorded_at
        FROM sensor_readings
        WHERE transformer_id = :tid
          AND recorded_at >= :cutoff
        ORDER BY recorded_at ASC
    """), {"tid": transformer_id, "cutoff": thirty_days_ago})

    rows = result.fetchall()

    if len(rows) < 24:
        # Need at least 24 readings (1 day) for meaningful features
        return None

    df = pd.DataFrame(rows, columns=[
        "load_percentage", "oil_temperature_c", "ambient_temp_c",
        "power_factor", "harmonic_distortion", "primary_voltage_kv",
        "secondary_voltage_v", "current_amps", "is_fault_event",
        "recorded_at"
    ])

    df["recorded_at"]  = pd.to_datetime(df["recorded_at"])
    df                 = df.sort_values("recorded_at")

    # Get transformer metadata (age, capacity)
    meta = db.execute(text("""
        SELECT installation_year, capacity_kva
        FROM transformers
        WHERE transformer_id = :tid
    """), {"tid": transformer_id}).fetchone()

    age_years    = datetime.now().year - (meta[0] or 2015) if meta else 10
    capacity_kva = meta[1] if meta else 200

    # ── Compute engineered features from last window ──
    load   = df["load_percentage"]
    oil    = df["oil_temperature_c"]
    pf     = df["power_factor"]

    # Rolling features (last N readings)
    load_24h_mean  = float(load.tail(24).mean())
    load_7d_mean   = float(load.mean())             # all data = ~30d, tail = 7d
    oil_24h_mean   = float(oil.tail(24).mean())
    oil_24h_max    = float(oil.tail(24).max())
    oil_7d_mean    = float(oil.tail(24 * 7).mean()) if len(oil) >= 24*7 else float(oil.mean())

    # Trend features
    oil_recent     = float(oil.tail(24 * 7).mean())  if len(oil) >= 24*7 else float(oil.mean())
    oil_baseline   = float(oil.mean())
    oil_temp_trend = oil_recent - oil_baseline

    load_recent    = float(load.tail(24 * 7).mean()) if len(load) >= 24*7 else float(load.mean())
    load_baseline  = float(load.mean())
    load_trend     = load_recent - load_baseline

    pf_recent      = float(pf.tail(24 * 7).mean()) if len(pf) >= 24*7 else float(pf.mean())
    pf_baseline    = float(pf.mean())
    pf_trend       = pf_recent - pf_baseline

    # Stress event counters (last 7 days)
    last_7d             = df.tail(24 * 7)
    overload_events_7d  = float((last_7d["load_percentage"] > 100).sum())
    high_temp_events_7d = float((last_7d["oil_temperature_c"] > 80).sum())
    fault_events_7d     = float(last_7d["is_fault_event"].astype(bool).sum())

    # Latest reading values
    latest = df.iloc[-1]

    return {
        # Raw sensor values (latest reading)
        "load_percentage":     float(latest["load_percentage"]),
        "oil_temperature_c":   float(latest["oil_temperature_c"]),
        "ambient_temp_c":      float(latest["ambient_temp_c"]),
        "power_factor":        float(latest["power_factor"]),
        "harmonic_distortion": float(latest["harmonic_distortion"]),
        "age_years":           age_years,
        "capacity_kva":        capacity_kva,
        # Engineered features
        "load_24h_mean":       load_24h_mean,
        "load_7d_mean":        load_7d_mean,
        "oil_temp_24h_mean":   oil_24h_mean,
        "oil_temp_24h_max":    oil_24h_max,
        "oil_temp_7d_mean":    oil_7d_mean,
        "oil_temp_trend":      oil_temp_trend,
        "load_trend":          load_trend,
        "pf_trend":            pf_trend,
        "overload_events_7d":  overload_events_7d,
        "high_temp_events_7d": high_temp_events_7d,
        "fault_events_7d":     fault_events_7d,
        "hour_of_day":         latest["recorded_at"].hour,
        "month":               latest["recorded_at"].month,
    }


def run_prediction_for_transformer(
    transformer_id: str,
    db: Session
) -> dict:
    """
    Runs the full prediction pipeline for one transformer.
    Saves result to DB and creates alerts if needed.
    Returns the prediction result dict.
    """

    # Import here to avoid circular imports
    from ml.src.health_scorer import compute_health_score

    # Get features
    features = get_latest_features(transformer_id, db)
    if features is None:
        return {"error": f"Not enough data for {transformer_id}"}

    # Run ML models
    result = compute_health_score(features)

    # Save to health_predictions table
    prediction = HealthPrediction(
        transformer_id          = transformer_id,
        health_score            = result["health_score"],
        failure_probability_30d = result["failure_probability"],
        risk_level              = result["risk_level"],
        anomaly_detected        = result["anomaly_detected"],
        anomaly_score           = result["anomaly_score"],
        contributing_factors    = result["contributing_factors"],
    )
    db.add(prediction)

    # Create alerts for WARNING and CRITICAL violations
    _create_alerts_if_needed(transformer_id, result, db)

    db.commit()

    return {
        "transformer_id": transformer_id,
        **result
    }


def _create_alerts_if_needed(
    transformer_id: str,
    result: dict,
    db: Session
):
    """Creates alert records for significant threshold violations."""

    violations = result.get("threshold_violations", [])
    risk_level = result["risk_level"]

    # Only create alerts for WARNING and CRITICAL (not WATCH)
    serious = [v for v in violations if v.startswith(("WARNING", "CRITICAL"))]

    if not serious:
        return

    severity = "CRITICAL" if risk_level in ["CRITICAL", "HIGH"] else "WARNING"

    # Check if we already created an alert for this transformer recently
    # (avoid spamming alerts every time prediction runs)
    from sqlalchemy import text as sql_text
    recent = db.execute(sql_text("""
        SELECT id FROM alerts
        WHERE transformer_id = :tid
          AND acknowledged = false
    """), {"tid": transformer_id}).fetchone()

    if recent:
        return   # Alert already exists, don't create duplicate

    # Determine alert type from violations
    violation_text = " | ".join(serious[:3])   # top 3 violations
    if "Oil temp" in violation_text and "Load" in violation_text:
        alert_type = "THERMAL_OVERLOAD"
    elif "Oil temp" in violation_text:
        alert_type = "OVERTEMP"
    elif "Load" in violation_text:
        alert_type = "OVERLOAD"
    elif "trend" in violation_text.lower():
        alert_type = "ANOMALY"
    else:
        alert_type = "THRESHOLD_BREACH"

    alert = Alert(
        transformer_id = transformer_id,
        alert_type     = alert_type,
        severity       = severity,
        message        = (
            f"Health score: {result['health_score']}/100 | "
            f"Failure risk: {result['failure_probability']*100:.1f}% | "
            f"{violation_text}"
        ),
    )
    db.add(alert)


def run_batch_predictions(db: Session) -> dict:
    """
    Runs predictions for ALL transformers that have recent sensor data.
    Called by the batch script and the scheduled job.
    """
    from sqlalchemy import text as sql_text

    transformers = db.execute(sql_text(
        "SELECT transformer_id FROM transformers ORDER BY transformer_id"
    )).fetchall()

    results = {"success": 0, "skipped": 0, "errors": 0, "summary": []}

    for (tid,) in transformers:
        try:
            result = run_prediction_for_transformer(tid, db)
            if "error" in result:
                results["skipped"] += 1
            else:
                results["success"] += 1
                results["summary"].append({
                    "transformer_id": tid,
                    "health_score":   result["health_score"],
                    "risk_level":     result["risk_level"],
                })
        except Exception as e:
            results["errors"] += 1
            print(f"  Error processing {tid}: {e}")

    return results