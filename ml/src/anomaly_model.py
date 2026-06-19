# ml/src/anomaly_model.py
# Trains an Isolation Forest for unsupervised anomaly detection.
#
# WHAT IT DOES:
# Learns what "normal" transformer readings look like.
# When a new reading doesn't fit that normal pattern, it raises a flag.
# No labels needed — it figures out anomalies on its own.
#
# WHY Isolation Forest:
# It works by randomly splitting data. Normal readings are hard to isolate
# (they cluster together). Anomalous readings are easy to isolate
# (they sit far from the cluster). Fewer splits needed = more anomalous.
#
# Run from project root: python ml/src/anomaly_model.py

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib
import os

# ── Paths ──
TRAIN_PATH  = "ml/data/processed/train_features.csv"
MODEL_PATH  = "ml/models/isolation_forest.joblib"

# ── Features used for anomaly detection ──
# We use only the core sensor readings + engineered trends
# NOT the label — this is unsupervised
ANOMALY_FEATURES = [
    "load_percentage",
    "oil_temperature_c",
    "ambient_temp_c",
    "power_factor",
    "harmonic_distortion",
    "load_24h_mean",
    "oil_temp_24h_mean",
    "oil_temp_24h_max",
    "oil_temp_trend",
    "load_trend",
    "pf_trend",
    "overload_events_7d",
    "high_temp_events_7d",
]


def train_anomaly_model():

    print("=" * 55)
    print("  Isolation Forest — Anomaly Detection Training")
    print("=" * 55)

    # ── Step 1: Load training data ──
    print("\n[1/5] Loading training data...")
    df = pd.read_csv(TRAIN_PATH)
    print(f"  Total rows: {len(df):,}")

    # ── Step 2: Train ONLY on healthy (normal) readings ──
    # This is the key idea: show the model what NORMAL looks like
    # so it can flag anything that deviates from normal
    normal_df = df[df["will_fail_30d"] == 0][ANOMALY_FEATURES].dropna()
    print(f"\n[2/5] Using {len(normal_df):,} healthy readings for training")
    print(f"  (Excluding {len(df) - len(normal_df):,} failure-window readings)")

    # ── Step 3: Scale features ──
    # Isolation Forest works on distances — features must be on same scale
    # StandardScaler makes every feature have mean=0 and std=1
    print("\n[3/5] Scaling features...")
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(normal_df)
    print(f"  Features scaled: {len(ANOMALY_FEATURES)}")

    # ── Step 4: Train Isolation Forest ──
    # contamination = expected % of anomalies in the data
    # We set 0.02 (2%) because in real operation ~2% of readings are unusual
    print("\n[4/5] Training Isolation Forest...")
    print("  n_estimators=200, contamination=0.02")
    print("  (This may take 20-30 seconds...)")

    iso_model = IsolationForest(
        n_estimators=200,       # number of trees — more = more stable
        contamination=0.02,     # expected proportion of anomalies
        max_samples="auto",     # samples per tree
        random_state=42,
        n_jobs=-1               # use all CPU cores
    )
    iso_model.fit(X_train)
    print("  ✓ Training complete")

    # ── Step 5: Evaluate on full dataset ──
    print("\n[5/5] Evaluating on full training data...")
    all_data   = df[ANOMALY_FEATURES].fillna(df[ANOMALY_FEATURES].median())
    X_all      = scaler.transform(all_data)

    # Isolation Forest returns: -1 = anomaly, 1 = normal
    raw_predictions = iso_model.predict(X_all)

    # Convert to 0/1 to compare with our labels
    # -1 (anomaly) → 1, 1 (normal) → 0
    predictions = (raw_predictions == -1).astype(int)
    true_labels = df["will_fail_30d"].values

    # Anomaly scores: more negative = more anomalous
    anomaly_scores = iso_model.decision_function(X_all)

    print("\n  Classification Report (anomaly vs healthy):")
    print(classification_report(true_labels, predictions,
                                target_names=["Healthy", "Anomalous"],
                                zero_division=0))

    # Check if failing transformers get higher anomaly scores
    df["anomaly_score"]   = anomaly_scores
    df["anomaly_flag"]    = predictions

    print("  Average anomaly score by label:")
    score_summary = df.groupby("will_fail_30d")["anomaly_score"].mean()
    print(f"  Healthy (0): {score_summary.get(0, 0):.4f}  (higher = more normal)")
    print(f"  Failing (1): {score_summary.get(1, 0):.4f}  (lower = more anomalous)")
    print("  ✓ Failing transformers should have lower (more negative) scores")

    # ── Save model ──
    os.makedirs("ml/models", exist_ok=True)
    model_bundle = {
        "model":    iso_model,
        "scaler":   scaler,
        "features": ANOMALY_FEATURES,
    }
    joblib.dump(model_bundle, MODEL_PATH)
    print(f"\n  ✓ Model saved to {MODEL_PATH}")

    # ── Show example anomalies ──
    print("\n  Top 5 most anomalous readings detected:")
    df_copy = df.copy()
    df_copy["anomaly_score"] = anomaly_scores
    top_anomalies = df_copy.nsmallest(5, "anomaly_score")[
        ["transformer_id", "recorded_at",
         "oil_temperature_c", "load_percentage",
         "oil_temp_trend", "anomaly_score", "will_fail_30d"]
    ]
    print(top_anomalies.to_string())

    return iso_model, scaler


if __name__ == "__main__":
    train_anomaly_model()
    print("\n✓ Anomaly model ready. Run prediction_model.py next.")