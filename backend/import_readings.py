# backend/import_readings.py
# Bulk imports the generated CSV into the sensor_readings table.
# Run ONCE after seed.py.
# Takes 3-5 minutes for 423,000 rows.

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from database import SessionLocal
from models.reading import SensorReading

CSV_PATH   = "ml/data/raw/transformer_readings.csv"
BATCH_SIZE = 5000

def import_readings():

    print(f"Reading {CSV_PATH}...")

    # Build full path relative to project root
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    full_path    = os.path.join(project_root, CSV_PATH)

    if not os.path.exists(full_path):
        print(f"ERROR: File not found at {full_path}")
        print("Make sure you ran: python ml/src/data_generator.py first")
        return

    df = pd.read_csv(full_path)
    print(f"Loaded {len(df):,} rows")

    # Check if already imported
    db = SessionLocal()
    try:
        existing = db.query(SensorReading).count()
        if existing > 0:
            print(f"Already have {existing:,} readings in database.")
            print("Delete rows from sensor_readings in pgAdmin to re-import.")
            return
    finally:
        db.close()

    # Clean data types
    df["recorded_at"]    = pd.to_datetime(df["recorded_at"])
    df["is_fault_event"] = df["is_fault_event"].astype(bool)

    total   = len(df)
    batches = (total // BATCH_SIZE) + 1

    print(f"Importing {total:,} rows in {batches} batches of {BATCH_SIZE}...")
    print("Please wait — this takes 3-5 minutes...\n")

    imported = 0
    for i in range(batches):
        batch = df.iloc[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        if batch.empty:
            break

        db = SessionLocal()
        try:
            records = []
            for _, row in batch.iterrows():
                records.append(SensorReading(
                    transformer_id      = str(row["transformer_id"]),
                    recorded_at         = row["recorded_at"],
                    load_percentage     = float(row["load_percentage"]),
                    oil_temperature_c   = float(row["oil_temperature_c"]),
                    ambient_temp_c      = float(row["ambient_temp_c"]),
                    primary_voltage_kv  = float(row["primary_voltage_kv"]),
                    secondary_voltage_v = float(row["secondary_voltage_v"]),
                    current_amps        = float(row["current_amps"]),
                    power_factor        = float(row["power_factor"]),
                    harmonic_distortion = float(row["harmonic_distortion"]),
                    is_fault_event      = bool(row["is_fault_event"]),
                ))

            db.bulk_save_objects(records)
            db.commit()
            imported += len(records)

            pct = (imported / total) * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  [{bar}] {pct:5.1f}%  —  {imported:,} / {total:,} rows", end="\r")

        except Exception as e:
            db.rollback()
            print(f"\n  Error in batch {i+1}: {e}")
            raise
        finally:
            db.close()

    print(f"\n\n✓ Import complete — {imported:,} sensor readings saved to database")
    print("\nVerify in pgAdmin:")
    print("  Right-click sensor_readings → View/Edit Data → All Rows")
    print("  You should see ~423,000 rows")
    print("\nNext step: python backend/run_predictions.py")

if __name__ == "__main__":
    import_readings()