# backend/run_predictions.py
# Runs ML health predictions for all 50 transformers.
# Saves results to health_predictions table.
# Creates alerts for at-risk transformers.
# Run AFTER import_readings.py completes.

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import SessionLocal
from services.prediction_service import run_prediction_for_transformer
from sqlalchemy import text

def run_all_predictions():
    db = SessionLocal()

    print("=" * 55)
    print("  Running batch predictions for all transformers")
    print("=" * 55)

    # Get all transformer IDs
    # Only process transformers that have sensor readings in the database
    transformers = db.execute(text("""
        SELECT DISTINCT transformer_id
        FROM sensor_readings
        ORDER BY transformer_id
    """)).fetchall()

    print(f"\nFound {len(transformers)} transformers\n")

    results = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0, "skipped": 0}

    for i, (tid,) in enumerate(transformers, 1):
        try:
            result = run_prediction_for_transformer(tid, db)

            if "error" in result:
                results["skipped"] += 1
                print(f"  [{i:2}/50] {tid} — SKIPPED (not enough data)")
            else:
                risk  = result["risk_level"]
                score = result["health_score"]
                prob  = result["failure_probability"] * 100
                results[risk] = results.get(risk, 0) + 1

                # Icon based on risk
                icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}.get(risk, "⚪")
                print(f"  [{i:2}/50] {tid} — Score: {score:3}/100  Risk: {risk:<8}  Fail prob: {prob:5.1f}%  {icon}")

        except Exception as e:
            results["skipped"] += 1
            print(f"  [{i:2}/50] {tid} — ERROR: {e}")

    db.close()

    print("\n" + "=" * 55)
    print("  PREDICTION SUMMARY")
    print("=" * 55)
    print(f"  🟢 LOW:      {results['LOW']:2} transformers — healthy, no action needed")
    print(f"  🟡 MEDIUM:   {results['MEDIUM']:2} transformers — monitor closely")
    print(f"  🟠 HIGH:     {results['HIGH']:2} transformers — schedule inspection")
    print(f"  🔴 CRITICAL: {results['CRITICAL']:2} transformers — immediate action required")
    print(f"  ⚪ Skipped:  {results['skipped']:2} transformers — insufficient data")
    print(f"\n  Total processed: {sum(results.values())}")

    # Show critical transformers
    db = SessionLocal()
    critical = db.execute(text("""
        SELECT DISTINCT ON (transformer_id)
            h.transformer_id, t.name, t.district,
            h.health_score, h.failure_probability_30d
        FROM health_predictions h
        JOIN transformers t ON t.transformer_id = h.transformer_id
        WHERE h.risk_level IN ('CRITICAL', 'HIGH')
        ORDER BY h.transformer_id, h.predicted_at DESC
    """)).fetchall()
    db.close()

    if critical:
        print(f"\n  ⚠ Transformers needing immediate attention:")
        print(f"  {'ID':<15} {'Name':<30} {'District':<15} {'Score':>5}  {'Fail%':>6}")
        print("  " + "─" * 75)
        for row in critical:
            print(f"  {row[0]:<15} {row[1]:<30} {row[2]:<15} {row[3]:>5}  {row[4]*100:>5.1f}%")

    print("\n✓ Predictions complete.")
    print("  Check pgAdmin → health_predictions table for all results.")
    print("  Check pgAdmin → alerts table for generated alerts.")
    print("\n  Next step: build the React frontend dashboard!")

if __name__ == "__main__":
    run_all_predictions()