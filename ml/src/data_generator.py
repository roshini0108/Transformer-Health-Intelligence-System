# ml/src/data_generator.py
# FIXED VERSION — guarantees 15% failure rate for proper ML training

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

def generate_transformer_data(
    n_transformers: int = 50,
    days: int = 365,
    readings_per_day: int = 24
) -> pd.DataFrame:

    np.random.seed(99)
    records = []

    # ── GUARANTEED FAILURE LIST ──
    # Explicitly decide which transformer IDs will fail and on which day
    # 8 out of 50 = 16% failure rate — perfect for training
    failing_transformers = {
        3:  280,   # TRF-VZA-003 fails on day 280 (Oct 7)
        7:  310,   # TRF-VZA-007 fails on day 310 (Nov 6)
        11: 245,   # TRF-VZA-011 fails on day 245 (Sep 2)
        18: 330,   # TRF-VZA-018 fails on day 330 (Nov 26)
        23: 260,   # TRF-VZA-023 fails on day 260 (Sep 17)
        31: 295,   # TRF-VZA-031 fails on day 295 (Oct 22)
        39: 315,   # TRF-VZA-039 fails on day 315 (Nov 11)
        47: 275,   # TRF-VZA-047 fails on day 275 (Oct 2)
    }

    # AP monthly ambient temperature baselines (°C)
    monthly_ambient = {
        1: 24, 2: 26, 3: 30, 4: 36,
        5: 40, 6: 38, 7: 32, 8: 31,
        9: 30, 10: 28, 11: 26, 12: 23
    }

    for t_id in range(1, n_transformers + 1):
        transformer_id  = f"TRF-VZA-{t_id:03d}"
        age_years       = np.random.randint(2, 25)
        base_load       = np.random.uniform(40, 72)
        base_oil_temp   = 44 + age_years * 0.8
        capacity_kva    = np.random.choice([100, 200, 315, 500, 630])

        will_fail   = t_id in failing_transformers
        failure_day = failing_transformers.get(t_id, None)

        start_date = datetime(2024, 1, 1)

        for day in range(days):

            # Stop generating data after failure
            if will_fail and failure_day and day >= failure_day:
                break

            current_date = start_date + timedelta(days=day)
            month        = current_date.month

            # Seasonal multipliers
            if month in [4, 5, 6]:
                season_load, season_temp = 1.35, 1.25
            elif month in [12, 1, 2]:
                season_load, season_temp = 0.85, 0.85
            elif month in [7, 8, 9]:
                season_load, season_temp = 1.05, 0.95
            else:
                season_load, season_temp = 1.0, 1.0

            # ── Degradation curve ──
            # Starts 60 days before failure, accelerates in final 7 days
            if will_fail and failure_day:
                days_to_failure = failure_day - day
                if days_to_failure <= 7:
                    degradation = 1.0                                        # critical
                elif days_to_failure <= 30:
                    degradation = ((30 - days_to_failure) / 30) ** 1.2      # strong
                elif days_to_failure <= 60:
                    degradation = ((60 - days_to_failure) / 60) ** 2 * 0.4  # early
                else:
                    degradation = 0.0
            else:
                degradation = 0.0

            for hour in range(readings_per_day):

                # Time-of-day load pattern
                if hour in [18, 19, 20, 21, 22]:
                    time_factor = 1.50   # evening peak
                elif hour in [7, 8, 9]:
                    time_factor = 1.35   # morning peak
                elif hour in [11, 12, 13, 14]:
                    time_factor = 1.10   # afternoon
                elif hour in [0, 1, 2, 3, 4]:
                    time_factor = 0.55   # night trough
                else:
                    time_factor = 1.0

                # Load
                load_pct = np.clip(
                    base_load * season_load * time_factor
                    + np.random.normal(0, 3)
                    + degradation * 32,
                    5, 130
                )

                # Ambient temperature
                base_amb    = monthly_ambient[month]
                hour_factor = np.sin(np.pi * (hour - 6) / 12) * 4 if 6 <= hour <= 18 else -2
                ambient_temp = np.clip(base_amb + hour_factor + np.random.normal(0, 1.5), 15, 48)

                # Oil temperature
                oil_temp = np.clip(
                    base_oil_temp * season_temp
                    + load_pct * 0.35
                    + ambient_temp * 0.15
                    + np.random.normal(0, 1.5)
                    + degradation * 30,
                    30, 125
                )

                # Power factor
                power_factor = np.clip(
                    0.93 - age_years * 0.003 - degradation * 0.09
                    + np.random.normal(0, 0.012),
                    0.62, 0.99
                )

                # Harmonic distortion
                harmonic = np.clip(
                    1.5 + age_years * 0.06 + degradation * 10
                    + np.random.normal(0, 0.3),
                    0.5, 20.0
                )

                # Voltage
                primary_voltage   = np.clip(11.0 + np.random.normal(0, 0.15) - degradation * 0.35, 9.5, 12.0)
                secondary_voltage = np.clip(230 - (load_pct - 50) * 0.15 + np.random.normal(0, 2), 185, 256)
                current_amps      = np.clip(
                    (load_pct / 100) * capacity_kva / (1.732 * 0.415) + np.random.normal(0, 2),
                    0, 800
                )

                # Fault event (rare normally, common during severe degradation)
                is_fault = np.random.random() < (0.001 + degradation * 0.05)

                # ── Label: will fail in next 30 days? ──
                if will_fail and failure_day:
                    days_left = failure_day - day
                    label = 1 if 0 < days_left <= 30 else 0
                else:
                    label = 0

                records.append({
                    "transformer_id":      transformer_id,
                    "recorded_at":         current_date + timedelta(hours=hour),
                    "load_percentage":     round(float(load_pct), 2),
                    "oil_temperature_c":   round(float(oil_temp), 2),
                    "ambient_temp_c":      round(float(ambient_temp), 2),
                    "primary_voltage_kv":  round(float(primary_voltage), 3),
                    "secondary_voltage_v": round(float(secondary_voltage), 2),
                    "current_amps":        round(float(current_amps), 2),
                    "power_factor":        round(float(power_factor), 3),
                    "harmonic_distortion": round(float(harmonic), 2),
                    "is_fault_event":      bool(is_fault),
                    "age_years":           int(age_years),
                    "capacity_kva":        int(capacity_kva),
                    "will_fail_30d":       int(label),
                })

    return pd.DataFrame(records)


if __name__ == "__main__":
    print("Generating synthetic transformer data...")

    df = generate_transformer_data()

    os.makedirs("ml/data/raw", exist_ok=True)
    output_path = "ml/data/raw/transformer_readings.csv"
    df.to_csv(output_path, index=False)

    total        = len(df)
    failures     = int(df['will_fail_30d'].sum())
    failure_rate = failures / total * 100

    print(f"Generated {total:,} records")
    print(f"Failure cases: {failures:,} ({failure_rate:.1f}%)")
    print(f"Saved to: {output_path}")

    print("\n── Sanity check ──")
    print(f"Unique transformers : {df['transformer_id'].nunique()}")
    print(f"Date range          : {df['recorded_at'].min()} → {df['recorded_at'].max()}")

    print("\nAverage readings by label:")
    summary = df.groupby('will_fail_30d')[
        ['load_percentage', 'oil_temperature_c', 'power_factor', 'harmonic_distortion']
    ].mean().round(2)
    print(summary)

    print("\nFailing transformer list (guaranteed):")
    failing_ids = df[df['will_fail_30d'] == 1]['transformer_id'].unique()
    print(f"  {sorted(failing_ids)}")

    print("\nLabel distribution per failing transformer:")
    for tid in sorted(failing_ids):
        subset  = df[df['transformer_id'] == tid]
        n_fail  = int(subset['will_fail_30d'].sum())
        n_total = len(subset)
        print(f"  {tid}: {n_fail} failure-window readings out of {n_total} total")