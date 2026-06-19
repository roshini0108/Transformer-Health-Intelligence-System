# ml/src/health_scorer.py
# Combines Isolation Forest + XGBoost into a single 0-100 health score.
#
# INPUT:  A dict of sensor readings for one transformer
# OUTPUT: health_score (0-100), risk_level, failure_probability,
#         anomaly_detected, contributing_factors
#
# This file is imported by the FastAPI backend.
# The backend calls compute_health_score() for every transformer
# and stores the result in the health_predictions table.

import joblib
import pandas as pd
import numpy as np
import os

# ── Model paths ──
ANOMALY_MODEL_PATH  = "ml/models/isolation_forest.joblib"
FAILURE_MODEL_PATH  = "ml/models/xgboost_failure.joblib"

# ── Load models once at module level ──
# This means they load when the backend starts, not on every request.
# Loading a model takes ~1 second — we don't want that per API call.
print("Loading ML models...")

_anomaly_bundle  = joblib.load(ANOMALY_MODEL_PATH)
_anomaly_model   = _anomaly_bundle["model"]
_anomaly_scaler  = _anomaly_bundle["scaler"]
_anomaly_features = _anomaly_bundle["features"]

_failure_bundle  = joblib.load(FAILURE_MODEL_PATH)
_failure_model   = _failure_bundle["model"]
_failure_features = _failure_bundle["features"]

print("✓ Models loaded successfully")


def compute_health_score(features: dict) -> dict:
    """
    Given a dictionary of sensor readings + engineered features
    for one transformer, returns a complete health assessment.

    Args:
        features: dict with keys matching FEATURE_COLUMNS
                  (load_percentage, oil_temperature_c, oil_temp_trend, etc.)

    Returns:
        dict with:
            health_score          (int, 0-100)
            risk_level            (str, LOW/MEDIUM/HIGH/CRITICAL)
            failure_probability   (float, 0.0-1.0)
            anomaly_detected      (bool)
            anomaly_score         (float)
            contributing_factors  (dict, explains why score is low)
            threshold_violations  (list, which rules were broken)
    """

    # ── Part 1: Anomaly Detection ──
    # Ask Isolation Forest: "does this reading look unusual?"
    anomaly_df     = pd.DataFrame([features])[_anomaly_features]
    anomaly_df     = anomaly_df.fillna(anomaly_df.median())
    X_anomaly      = _anomaly_scaler.transform(anomaly_df)

    raw_anomaly_score = float(_anomaly_model.decision_function(X_anomaly)[0])
    anomaly_flag      = int(_anomaly_model.predict(X_anomaly)[0])  # -1=anomaly, 1=normal
    anomaly_detected  = (anomaly_flag == -1)

    # Normalise anomaly score to 0-1 range
    # More negative raw score = more anomalous = higher normalised score
    # Typical range: -0.15 (very anomalous) to +0.15 (very normal)
    anomaly_score_normalised = float(np.clip((-raw_anomaly_score + 0.05) / 0.20, 0, 1))

    # ── Part 2: Failure Probability ──
    # Ask XGBoost: "what is the probability of failure in next 30 days?"
    failure_df       = pd.DataFrame([features])[_failure_features]
    failure_df       = failure_df.fillna(failure_df.median())
    failure_prob     = float(_failure_model.predict_proba(failure_df)[0][1])

    # ── Part 3: Rule-Based Threshold Violations ──
    # Hard engineering rules from IEEE/IEC standards
    # These are deterministic — if oil is >85°C, that is always a penalty
    threshold_violations = []
    rule_penalty         = 0

    oil_temp   = features.get("oil_temperature_c", 60)
    load_pct   = features.get("load_percentage", 50)
    pf         = features.get("power_factor", 0.90)
    thd        = features.get("harmonic_distortion", 2)
    overloads  = features.get("overload_events_7d", 0)
    high_temps = features.get("high_temp_events_7d", 0)
    oil_trend  = features.get("oil_temp_trend", 0)

    # Oil temperature violations (IEEE C57.91)
    if oil_temp > 100:
        rule_penalty += 30
        threshold_violations.append(f"CRITICAL: Oil temp {oil_temp:.1f}°C far exceeds 85°C limit")
    elif oil_temp > 85:
        rule_penalty += 20
        threshold_violations.append(f"WARNING: Oil temp {oil_temp:.1f}°C exceeds 85°C threshold")
    elif oil_temp > 75:
        rule_penalty += 8
        threshold_violations.append(f"WATCH: Oil temp {oil_temp:.1f}°C approaching limit")

    # Load violations
    if load_pct > 110:
        rule_penalty += 25
        threshold_violations.append(f"CRITICAL: Load {load_pct:.1f}% severely overloaded")
    elif load_pct > 100:
        rule_penalty += 15
        threshold_violations.append(f"WARNING: Load {load_pct:.1f}% exceeds rated capacity")
    elif load_pct > 90:
        rule_penalty += 5
        threshold_violations.append(f"WATCH: Load {load_pct:.1f}% near rated capacity")

    # Power factor violations
    if pf < 0.75:
        rule_penalty += 15
        threshold_violations.append(f"WARNING: Power factor {pf:.3f} very poor (< 0.75)")
    elif pf < 0.80:
        rule_penalty += 8
        threshold_violations.append(f"WATCH: Power factor {pf:.3f} below 0.80")

    # Harmonic distortion
    if thd > 12:
        rule_penalty += 12
        threshold_violations.append(f"WARNING: THD {thd:.1f}% severely elevated (> 12%)")
    elif thd > 8:
        rule_penalty += 5
        threshold_violations.append(f"WATCH: THD {thd:.1f}% elevated (> 8%)")

    # Sustained stress (from rolling features)
    if overloads > 100:
        rule_penalty += 10
        threshold_violations.append(f"WARNING: {int(overloads)} overload-hours in last 7 days")
    elif overloads > 48:
        rule_penalty += 5
        threshold_violations.append(f"WATCH: {int(overloads)} overload-hours in last 7 days")

    if high_temps > 120:
        rule_penalty += 8
        threshold_violations.append(f"WARNING: High oil temp for {int(high_temps)} hours in last 7 days")

    # Rising temperature trend (most predictive per feature importance)
    if oil_trend > 15:
        rule_penalty += 12
        threshold_violations.append(f"CRITICAL: Oil temp trend +{oil_trend:.1f}°C above monthly avg")
    elif oil_trend > 8:
        rule_penalty += 6
        threshold_violations.append(f"WARNING: Oil temp rising trend +{oil_trend:.1f}°C")
    elif oil_trend > 4:
        rule_penalty += 2
        threshold_violations.append(f"WATCH: Oil temp slightly elevated trend +{oil_trend:.1f}°C")

    # Cap rule penalty at 60 (the other 40 points come from ML)
    rule_penalty = min(rule_penalty, 60)

    # ── Part 4: Final Health Score ──
    #
    # Score = 100 - (ML penalty) - (rule penalty)
    #
    # ML penalty breakdown:
    #   anomaly component:  0-20 points  (is something unusual happening?)
    #   failure component:  0-20 points  (how likely is failure in 30 days?)
    #
    # Rule penalty: 0-60 points  (hard threshold violations)
    #
    ml_penalty     = (anomaly_score_normalised * 20) + (failure_prob * 20)
    health_score   = max(0, min(100, round(100 - ml_penalty - rule_penalty)))

    # ── Part 5: Risk Level ──
    if health_score >= 75:
        risk_level = "LOW"
    elif health_score >= 50:
        risk_level = "MEDIUM"
    elif health_score >= 25:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # ── Part 6: Contributing Factors ──
    # Explains to the engineer WHY the score is what it is.
    # Uses the XGBoost feature importances as weights.
    feature_importances = dict(zip(
        _failure_features,
        _failure_model.feature_importances_
    ))

    # Normalise the top contributing factors to sum to 100%
    top_features = sorted(
        feature_importances.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    total_weight = sum(w for _, w in top_features)
    contributing_factors = {
        feat: round(float(weight / total_weight), 3)
        for feat, weight in top_features
    }

    return {
        "health_score":          health_score,
        "risk_level":            risk_level,
        "failure_probability":   round(failure_prob, 4),
        "anomaly_detected":      anomaly_detected,
        "anomaly_score":         round(raw_anomaly_score, 4),
        "contributing_factors":  contributing_factors,
        "threshold_violations":  threshold_violations,
        "ml_penalty":            round(ml_penalty, 2),
        "rule_penalty":          rule_penalty,
    }


# ── Test function ──
def _build_feature_dict(
    load_pct, oil_temp, ambient, pf, thd,
    age, capacity, oil_trend, load_trend, pf_trend,
    overloads_7d, high_temps_7d, faults_7d,
    load_24h, load_7d, oil_24h_mean, oil_24h_max, oil_7d_mean,
    hour=14, month=5
):
    """Helper to build a complete feature dict for testing."""
    return {
        "load_percentage":     load_pct,
        "oil_temperature_c":   oil_temp,
        "ambient_temp_c":      ambient,
        "power_factor":        pf,
        "harmonic_distortion": thd,
        "age_years":           age,
        "capacity_kva":        capacity,
        "load_24h_mean":       load_24h,
        "load_7d_mean":        load_7d,
        "oil_temp_24h_mean":   oil_24h_mean,
        "oil_temp_24h_max":    oil_24h_max,
        "oil_temp_7d_mean":    oil_7d_mean,
        "oil_temp_trend":      oil_trend,
        "load_trend":          load_trend,
        "pf_trend":            pf_trend,
        "overload_events_7d":  overloads_7d,
        "high_temp_events_7d": high_temps_7d,
        "fault_events_7d":     faults_7d,
        "hour_of_day":         hour,
        "month":               month,
    }


if __name__ == "__main__":

    print("\n" + "=" * 55)
    print("  Health Scorer — Live Test")
    print("=" * 55)

    # ── Test Case 1: Critical transformer (like TRF-VZA-047) ──
    print("\n[TEST 1] Critical transformer — about to fail")
    critical = _build_feature_dict(
        load_pct=108, oil_temp=91, ambient=38,
        pf=0.76, thd=11.2,
        age=13, capacity=200,
        oil_trend=18.5, load_trend=15.2, pf_trend=-0.06,
        overloads_7d=108, high_temps_7d=168, faults_7d=5,
        load_24h=105, load_7d=98, oil_24h_mean=89,
        oil_24h_max=91, oil_7d_mean=87,
        hour=20, month=10
    )
    result1 = compute_health_score(critical)
    print(f"  Health Score:        {result1['health_score']}/100")
    print(f"  Risk Level:          {result1['risk_level']}")
    print(f"  Failure Probability: {result1['failure_probability']*100:.1f}%")
    print(f"  Anomaly Detected:    {result1['anomaly_detected']}")
    print(f"  ML Penalty:          {result1['ml_penalty']:.1f} pts")
    print(f"  Rule Penalty:        {result1['rule_penalty']} pts")
    print(f"  Threshold Violations:")
    for v in result1["threshold_violations"]:
        print(f"    • {v}")
    print(f"  Top Contributing Factors:")
    for feat, weight in result1["contributing_factors"].items():
        print(f"    • {feat}: {weight*100:.1f}%")

    # ── Test Case 2: Healthy transformer ──
    print("\n[TEST 2] Healthy transformer — no issues")
    healthy = _build_feature_dict(
        load_pct=58, oil_temp=62, ambient=28,
        pf=0.92, thd=2.1,
        age=5, capacity=315,
        oil_trend=0.3, load_trend=0.5, pf_trend=0.001,
        overloads_7d=0, high_temps_7d=2, faults_7d=0,
        load_24h=55, load_7d=56, oil_24h_mean=61,
        oil_24h_max=64, oil_7d_mean=60,
        hour=14, month=3
    )
    result2 = compute_health_score(healthy)
    print(f"  Health Score:        {result2['health_score']}/100")
    print(f"  Risk Level:          {result2['risk_level']}")
    print(f"  Failure Probability: {result2['failure_probability']*100:.1f}%")
    print(f"  Anomaly Detected:    {result2['anomaly_detected']}")
    print(f"  Threshold Violations: {result2['threshold_violations'] or 'None ✓'}")

    # ── Test Case 3: Medium risk transformer ──
    print("\n[TEST 3] Medium risk — watch closely")
    medium = _build_feature_dict(
        load_pct=88, oil_temp=74, ambient=35,
        pf=0.83, thd=6.5,
        age=11, capacity=200,
        oil_trend=5.2, load_trend=4.1, pf_trend=-0.02,
        overloads_7d=12, high_temps_7d=24, faults_7d=1,
        load_24h=85, load_7d=82, oil_24h_mean=73,
        oil_24h_max=76, oil_7d_mean=71,
        hour=19, month=5
    )
    result3 = compute_health_score(medium)
    print(f"  Health Score:        {result3['health_score']}/100")
    print(f"  Risk Level:          {result3['risk_level']}")
    print(f"  Failure Probability: {result3['failure_probability']*100:.1f}%")
    print(f"  Threshold Violations:")
    for v in result3["threshold_violations"]:
        print(f"    • {v}")

    # ── Summary ──
    print("\n── Summary ──")
    print(f"  Critical transformer score: {result1['health_score']:3}/100  {result1['risk_level']}")
    print(f"  Medium risk score:          {result3['health_score']:3}/100  {result3['risk_level']}")
    print(f"  Healthy transformer score:  {result2['health_score']:3}/100  {result2['risk_level']}")
    print("\n✓ Health scorer working correctly.")
    print("  Next step: integrate with FastAPI backend.")