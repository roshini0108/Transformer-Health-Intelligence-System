# ml/src/preprocessor.py
# Feature Engineering — transforms raw sensor readings into ML-ready features
#
# WHY this matters:
# Raw reading: "oil temp is 85°C today"  ← not very useful alone
# Engineered:  "oil temp has risen 1.8°C/day for 2 weeks"  ← extremely predictive
#
# Run from project root: python ml/src/preprocessor.py

import pandas as pd
import numpy as np
import os

# ── Configuration ──
RAW_PATH       = "ml/data/raw/transformer_readings.csv"
PROCESSED_DIR  = "ml/data/processed"
TRAIN_PATH     = f"{PROCESSED_DIR}/train_features.csv"
TEST_PATH      = f"{PROCESSED_DIR}/test_features.csv"

# These are the final features the ML model will train on
FEATURE_COLUMNS = [
    # Raw sensor readings
    "load_percentage",
    "oil_temperature_c",
    "ambient_temp_c",
    "power_factor",
    "harmonic_distortion",
    "age_years",
    "capacity_kva",
    # Engineered: rolling averages (captures recent trend)
    "load_24h_mean",       # average load over last 24 hours
    "load_7d_mean",        # average load over last 7 days
    "oil_temp_24h_mean",   # average oil temp over last 24 hours
    "oil_temp_24h_max",    # peak oil temp in last 24 hours
    "oil_temp_7d_mean",    # average oil temp over last 7 days
    # Engineered: trend features (rate of change — most predictive)
    "oil_temp_trend",      # is oil temp rising or falling week over week?
    "load_trend",          # is load increasing over the past week?
    "pf_trend",            # is power factor deteriorating?
    # Engineered: stress counters
    "overload_events_7d",  # how many hours above 100% load in last 7 days
    "high_temp_events_7d", # how many hours above 80°C oil temp in last 7 days
    "fault_events_7d",     # how many fault trips in last 7 days
    # Context
    "hour_of_day",         # time of day (0-23) — captures load patterns
    "month",               # month (1-12) — captures seasonal patterns
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes raw sensor readings and creates new columns that
    capture trends, rolling statistics, and stress counters.

    All calculations are grouped by transformer_id so each
    transformer's history is computed independently.
    """

    print("  Sorting by transformer and time...")
    df = df.sort_values(["transformer_id", "recorded_at"]).copy()
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])

    print("  Adding time features...")
    df["hour_of_day"] = df["recorded_at"].dt.hour
    df["month"]       = df["recorded_at"].dt.month

    print("  Computing rolling averages (this takes ~30 seconds)...")

    # Group by transformer — all rolling calculations are per-transformer
    grp = df.groupby("transformer_id", group_keys=False)

    # ── Load rolling features ──
    # 24h mean: what was the average load in the last 24 readings (hours)?
    df["load_24h_mean"] = grp["load_percentage"].transform(
        lambda x: x.rolling(window=24, min_periods=1).mean()
    )
    # 7d mean: what was the average load over the past 7 days?
    df["load_7d_mean"] = grp["load_percentage"].transform(
        lambda x: x.rolling(window=24 * 7, min_periods=1).mean()
    )

    # ── Oil temperature rolling features ──
    df["oil_temp_24h_mean"] = grp["oil_temperature_c"].transform(
        lambda x: x.rolling(window=24, min_periods=1).mean()
    )
    df["oil_temp_24h_max"] = grp["oil_temperature_c"].transform(
        lambda x: x.rolling(window=24, min_periods=1).max()
    )
    df["oil_temp_7d_mean"] = grp["oil_temperature_c"].transform(
        lambda x: x.rolling(window=24 * 7, min_periods=1).mean()
    )

    # ── Trend features (most important for prediction) ──
    #
    # oil_temp_trend = (7-day mean) - (30-day mean)
    # Positive value = oil temp is higher recently than monthly average = rising trend
    # Negative value = oil temp is cooling down = good sign
    #
    oil_temp_30d = grp["oil_temperature_c"].transform(
        lambda x: x.rolling(window=24 * 30, min_periods=1).mean()
    )
    df["oil_temp_trend"] = df["oil_temp_7d_mean"] - oil_temp_30d

    # load_trend = similar idea for load
    load_30d = grp["load_percentage"].transform(
        lambda x: x.rolling(window=24 * 30, min_periods=1).mean()
    )
    df["load_trend"] = df["load_7d_mean"] - load_30d

    # pf_trend = power factor 7d mean - 30d mean
    # Negative value = PF is deteriorating = bad sign
    pf_7d  = grp["power_factor"].transform(
        lambda x: x.rolling(window=24 * 7, min_periods=1).mean()
    )
    pf_30d = grp["power_factor"].transform(
        lambda x: x.rolling(window=24 * 30, min_periods=1).mean()
    )
    df["pf_trend"] = pf_7d - pf_30d

    # ── Stress event counters ──
    #
    # Count how many readings in the last 7 days exceeded thresholds
    # This captures "how often is this transformer stressed?" not just "is it stressed now?"

    print("  Computing stress event counters...")

    df["overload_events_7d"] = grp["load_percentage"].transform(
        lambda x: (x > 100).rolling(window=24 * 7, min_periods=1).sum()
    )
    df["high_temp_events_7d"] = grp["oil_temperature_c"].transform(
        lambda x: (x > 80).rolling(window=24 * 7, min_periods=1).sum()
    )
    df["fault_events_7d"] = grp["is_fault_event"].transform(
        lambda x: x.rolling(window=24 * 7, min_periods=1).sum()
    )

    return df


def split_by_transformer(df: pd.DataFrame):
    """
    Splits data into train and test sets BY TRANSFORMER — not randomly.

    WHY: If we split randomly, the model sees readings from the same
    transformer in both train and test — making the test score artificially
    high (data leakage). By splitting on transformer ID, test transformers
    are completely unseen during training — a realistic evaluation.

    Train: 40 transformers (80%)
    Test:  10 transformers (20%) — including some failing ones
    """

    all_ids     = df["transformer_id"].unique()
    failing_ids = df[df["will_fail_30d"] == 1]["transformer_id"].unique()
    normal_ids  = [tid for tid in all_ids if tid not in failing_ids]

    np.random.seed(42)

    # Put 2 failing transformers in test set (25% of 8)
    test_failing = np.random.choice(failing_ids, size=2, replace=False)
    # Put 8 normal transformers in test set
    test_normal  = np.random.choice(normal_ids, size=8, replace=False)
    test_ids     = list(test_failing) + list(test_normal)

    train_df = df[~df["transformer_id"].isin(test_ids)].copy()
    test_df  = df[df["transformer_id"].isin(test_ids)].copy()

    print(f"\n  Train set: {len(train_df):,} readings from {train_df['transformer_id'].nunique()} transformers")
    print(f"  Test set:  {len(test_df):,} readings from {test_df['transformer_id'].nunique()} transformers")
    print(f"  Test transformers include failing: {[t for t in test_ids if t in failing_ids]}")

    return train_df, test_df


if __name__ == "__main__":

    print("=" * 55)
    print("  APEPDCL Transformer Health — Feature Engineering")
    print("=" * 55)

    # ── Step 1: Load raw data ──
    print(f"\n[1/4] Loading raw data from {RAW_PATH}...")
    df = pd.read_csv(RAW_PATH)
    print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns")
    print(f"  Raw columns: {list(df.columns)}")

    # ── Step 2: Engineer features ──
    print("\n[2/4] Engineering features...")
    df = engineer_features(df)
    print(f"  New column count: {len(df.columns)}")
    print(f"  Engineered columns added: {[c for c in df.columns if c not in ['transformer_id','recorded_at','load_percentage','oil_temperature_c','ambient_temp_c','primary_voltage_kv','secondary_voltage_v','current_amps','power_factor','harmonic_distortion','is_fault_event','age_years','capacity_kva','will_fail_30d']]}")

    # ── Step 3: Split into train/test ──
    print("\n[3/4] Splitting into train and test sets by transformer...")
    train_df, test_df = split_by_transformer(df)

    # ── Step 4: Save ──
    print(f"\n[4/4] Saving processed files...")
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Save only the columns the model needs + label + identifier
    save_cols = ["transformer_id", "recorded_at"] + FEATURE_COLUMNS + ["will_fail_30d"]

    train_df[save_cols].to_csv(TRAIN_PATH, index=False)
    test_df[save_cols].to_csv(TEST_PATH,  index=False)

    print(f"  ✓ Train: {TRAIN_PATH}  ({len(train_df):,} rows)")
    print(f"  ✓ Test:  {TEST_PATH}   ({len(test_df):,} rows)")

    # ── Final report ──
    print("\n── Feature Engineering Report ──")
    print(f"Total features for model: {len(FEATURE_COLUMNS)}")
    print("\nClass distribution in TRAIN set:")
    train_counts = train_df["will_fail_30d"].value_counts()
    print(f"  Healthy (0): {train_counts.get(0, 0):,}  ({train_counts.get(0,0)/len(train_df)*100:.1f}%)")
    print(f"  Failing (1): {train_counts.get(1, 0):,}  ({train_counts.get(1,0)/len(train_df)*100:.1f}%)")
    neg = train_counts.get(0, 1)
    pos = train_counts.get(1, 1)
    print(f"  scale_pos_weight for XGBoost: {neg//pos}  ← use this value when training")

    print("\nClass distribution in TEST set:")
    test_counts = test_df["will_fail_30d"].value_counts()
    print(f"  Healthy (0): {test_counts.get(0, 0):,}  ({test_counts.get(0,0)/len(test_df)*100:.1f}%)")
    print(f"  Failing (1): {test_counts.get(1, 0):,}  ({test_counts.get(1,0)/len(test_df)*100:.1f}%)")

    print("\nSample feature values (failing transformer, last 5 readings):")
    sample = train_df[train_df["will_fail_30d"] == 1].tail(5)[
        ["transformer_id", "oil_temperature_c", "oil_temp_trend",
         "load_percentage", "overload_events_7d", "high_temp_events_7d"]
    ]
    print(sample.to_string())

    print("\n✓ Preprocessing complete. Ready for model training.")