# ml/src/prediction_model.py
# Trains XGBoost to predict transformer failure 30 days in advance.
#
# WHAT IT DOES:
# Given current sensor readings + engineered features,
# predicts the probability (0-100%) that this transformer
# will fail within the next 30 days.
#
# WHY XGBoost:
# It handles class imbalance well (scale_pos_weight)
# It gives feature importances (we can explain WHY it flagged a transformer)
# It is fast, accurate, and industry-standard for tabular data
#
# Run from project root: python ml/src/prediction_model.py

import pandas as pd
import numpy as np
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    confusion_matrix,
    precision_recall_curve,
    average_precision_score
)
import xgboost as xgb
import joblib
import os
import warnings
warnings.filterwarnings("ignore")

# ── Paths ──
TRAIN_PATH = "ml/data/processed/train_features.csv"
TEST_PATH  = "ml/data/processed/test_features.csv"
MODEL_PATH = "ml/models/xgboost_failure.joblib"

# ── Features ── (same order every time — critical for consistency)
FEATURE_COLUMNS = [
    "load_percentage",
    "oil_temperature_c",
    "ambient_temp_c",
    "power_factor",
    "harmonic_distortion",
    "age_years",
    "capacity_kva",
    "load_24h_mean",
    "load_7d_mean",
    "oil_temp_24h_mean",
    "oil_temp_24h_max",
    "oil_temp_7d_mean",
    "oil_temp_trend",
    "load_trend",
    "pf_trend",
    "overload_events_7d",
    "high_temp_events_7d",
    "fault_events_7d",
    "hour_of_day",
    "month",
]


def train_failure_model():

    print("=" * 55)
    print("  XGBoost — Failure Prediction Model Training")
    print("=" * 55)

    # ── Step 1: Load data ──
    print("\n[1/6] Loading processed data...")
    train_df = pd.read_csv(TRAIN_PATH)
    test_df  = pd.read_csv(TEST_PATH)
    print(f"  Train: {len(train_df):,} rows")
    print(f"  Test:  {len(test_df):,} rows")

    # ── Step 2: Prepare X and y ──
    print("\n[2/6] Preparing features and labels...")
    X_train = train_df[FEATURE_COLUMNS].fillna(train_df[FEATURE_COLUMNS].median())
    y_train = train_df["will_fail_30d"]
    X_test  = test_df[FEATURE_COLUMNS].fillna(test_df[FEATURE_COLUMNS].median())
    y_test  = test_df["will_fail_30d"]

    # Class imbalance: how many healthy per 1 failing?
    # From preprocessor output: scale_pos_weight = 77
    n_negative = int((y_train == 0).sum())
    n_positive = int((y_train == 1).sum())
    spw        = n_negative // n_positive
    print(f"  Healthy readings: {n_negative:,}")
    print(f"  Failing readings: {n_positive:,}")
    print(f"  scale_pos_weight: {spw}  (tells XGBoost to weight failures {spw}x more)")

    # ── Step 3: Train XGBoost ──
    print("\n[3/6] Training XGBoost classifier...")
    print("  n_estimators=500, max_depth=6, learning_rate=0.05")
    print("  (This takes 1-3 minutes...)")

    model = xgb.XGBClassifier(
        n_estimators=500,           # number of trees
        max_depth=6,                # how deep each tree can go
        learning_rate=0.05,         # how much each tree contributes
        scale_pos_weight=spw,       # handles class imbalance — critical
        subsample=0.8,              # use 80% of data per tree (prevents overfitting)
        colsample_bytree=0.8,       # use 80% of features per tree
        min_child_weight=5,         # minimum samples in a leaf node
        gamma=1,                    # minimum loss reduction for a split
        reg_alpha=0.1,              # L1 regularisation
        reg_lambda=1.0,             # L2 regularisation
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=100,                # print loss every 100 trees
    )
    print("  ✓ Training complete")

    # ── Step 4: Evaluate ──
    print("\n[4/6] Evaluating on test set...")

    y_pred      = model.predict(X_test)
    y_prob      = model.predict_proba(X_test)[:, 1]  # probability of failure
    roc_auc     = roc_auc_score(y_test, y_prob)
    avg_prec    = average_precision_score(y_test, y_prob)

    print("\n  ── Classification Report ──")
    print(classification_report(y_test, y_pred,
                                target_names=["Healthy", "Will Fail"],
                                zero_division=0))

    print(f"  ROC-AUC Score:          {roc_auc:.4f}  (target: > 0.85)")
    print(f"  Average Precision:      {avg_prec:.4f}")

    cm = confusion_matrix(y_test, y_pred)
    print(f"\n  Confusion Matrix:")
    print(f"  ┌─────────────────────────────────────┐")
    print(f"  │              Predicted               │")
    print(f"  │           Healthy    Will Fail       │")
    print(f"  │ Actual                               │")
    print(f"  │ Healthy    {cm[0][0]:6,}      {cm[0][1]:6,}       │")
    print(f"  │ Will Fail  {cm[1][0]:6,}      {cm[1][1]:6,}       │")
    print(f"  └─────────────────────────────────────┘")

    tn, fp, fn, tp = cm.ravel()
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    print(f"\n  Of all actual failing readings:")
    print(f"  Caught (recall):  {recall*100:.1f}%  ← how many failures we detect")
    print(f"  Precision:        {precision*100:.1f}%  ← of our alerts, how many are real")
    print(f"  False alarms:     {fp:,}  ← healthy transformers incorrectly flagged")
    print(f"  Missed failures:  {fn:,}  ← failing transformers we missed")

    # ── Step 5: Feature importances ──
    print("\n[5/6] Feature importances (why does the model flag a transformer?):")
    importances = pd.Series(
        model.feature_importances_,
        index=FEATURE_COLUMNS
    ).sort_values(ascending=False)

    print("\n  Rank  Feature                    Importance")
    print("  " + "─" * 45)
    for rank, (feat, score) in enumerate(importances.items(), 1):
        bar     = "█" * int(score * 200)
        marker  = " ← #1 most predictive!" if rank == 1 else ""
        print(f"  {rank:2}.   {feat:<28} {score:.4f}  {bar}{marker}")

    # ── Step 6: Save ──
    print(f"\n[6/6] Saving model...")
    os.makedirs("ml/models", exist_ok=True)

    model_bundle = {
        "model":    model,
        "features": FEATURE_COLUMNS,
        "spw":      spw,
        "roc_auc":  roc_auc,
    }
    joblib.dump(model_bundle, MODEL_PATH)
    print(f"  ✓ Saved to {MODEL_PATH}")

    # ── Probability demo ──
    print("\n── Live Prediction Demo ──")
    print("  Testing on 3 known-failing readings vs 3 healthy readings:\n")

    # Grab actual readings from test set
    failing_samples = test_df[test_df["will_fail_30d"] == 1].head(3)
    healthy_samples = test_df[test_df["will_fail_30d"] == 0].head(3)
    demo_df         = pd.concat([failing_samples, healthy_samples])
    demo_X          = demo_df[FEATURE_COLUMNS].fillna(0)
    demo_probs      = model.predict_proba(demo_X)[:, 1]

    for i, (_, row) in enumerate(demo_df.iterrows()):
        prob    = demo_probs[i]
        label   = "FAILING" if row["will_fail_30d"] == 1 else "HEALTHY"
        verdict = "🔴 HIGH RISK" if prob > 0.5 else "🟢 LOW RISK"
        print(f"  {row['transformer_id']}  |  Actual: {label:<7}  |  "
              f"Failure prob: {prob*100:5.1f}%  |  {verdict}")

    return model


if __name__ == "__main__":
    train_failure_model()
    print("\n✓ Both models trained. Run health_scorer.py to test predictions.")