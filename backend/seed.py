# backend/seed.py
# Run this ONCE to populate your transformers table with 50 sample transformers
# Based on real areas in Visakhapatnam, Vizianagaram, and Srikakulam districts
# Run with: python seed.py  (from inside the backend folder, with venv active)

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from models.transformer import Transformer

# Real areas in APEPDCL's jurisdiction with approximate GPS coordinates
TRANSFORMERS = [
    # Visakhapatnam city
    {"transformer_id": "TRF-VZA-001", "name": "Gajuwaka Feeder 1",        "substation_name": "Gajuwaka SS",      "district": "Visakhapatnam", "latitude": 17.6868, "longitude": 83.2185, "capacity_kva": 200, "installation_year": 2012},
    {"transformer_id": "TRF-VZA-002", "name": "Gajuwaka Feeder 2",        "substation_name": "Gajuwaka SS",      "district": "Visakhapatnam", "latitude": 17.6900, "longitude": 83.2200, "capacity_kva": 315, "installation_year": 2010},
    {"transformer_id": "TRF-VZA-003", "name": "Gajuwaka Feeder 3",        "substation_name": "Gajuwaka SS",      "district": "Visakhapatnam", "latitude": 17.6850, "longitude": 83.2150, "capacity_kva": 200, "installation_year": 2008},
    {"transformer_id": "TRF-VZA-004", "name": "Pendurthi Colony",         "substation_name": "Pendurthi SS",     "district": "Visakhapatnam", "latitude": 17.8100, "longitude": 83.1500, "capacity_kva": 315, "installation_year": 2015},
    {"transformer_id": "TRF-VZA-005", "name": "Pendurthi Market",         "substation_name": "Pendurthi SS",     "district": "Visakhapatnam", "latitude": 17.8150, "longitude": 83.1550, "capacity_kva": 100, "installation_year": 2011},
    {"transformer_id": "TRF-VZA-006", "name": "Kommadi Residential",      "substation_name": "Kommadi SS",       "district": "Visakhapatnam", "latitude": 17.7900, "longitude": 83.3700, "capacity_kva": 100, "installation_year": 2016},
    {"transformer_id": "TRF-VZA-007", "name": "Kommadi Industrial",       "substation_name": "Kommadi SS",       "district": "Visakhapatnam", "latitude": 17.7850, "longitude": 83.3750, "capacity_kva": 500, "installation_year": 2014},
    {"transformer_id": "TRF-VZA-008", "name": "Bheemunipatnam Beach Rd",  "substation_name": "Bheemunipatnam SS","district": "Visakhapatnam", "latitude": 17.8900, "longitude": 83.4500, "capacity_kva": 200, "installation_year": 2009},
    {"transformer_id": "TRF-VZA-009", "name": "Bheemunipatnam Town",      "substation_name": "Bheemunipatnam SS","district": "Visakhapatnam", "latitude": 17.8950, "longitude": 83.4550, "capacity_kva": 315, "installation_year": 2013},
    {"transformer_id": "TRF-VZA-010", "name": "MVP Colony Sector 1",      "substation_name": "MVP SS",           "district": "Visakhapatnam", "latitude": 17.7280, "longitude": 83.3320, "capacity_kva": 630, "installation_year": 2007},
    {"transformer_id": "TRF-VZA-011", "name": "MVP Colony Sector 7",      "substation_name": "MVP SS",           "district": "Visakhapatnam", "latitude": 17.7300, "longitude": 83.3380, "capacity_kva": 200, "installation_year": 2006},
    {"transformer_id": "TRF-VZA-012", "name": "Dwaraka Nagar Main",       "substation_name": "Dwaraka Nagar SS", "district": "Visakhapatnam", "latitude": 17.7200, "longitude": 83.3100, "capacity_kva": 315, "installation_year": 2011},
    {"transformer_id": "TRF-VZA-013", "name": "Steel Plant Township 1",   "substation_name": "Steel Plant SS",   "district": "Visakhapatnam", "latitude": 17.6700, "longitude": 83.2000, "capacity_kva": 630, "installation_year": 2005},
    {"transformer_id": "TRF-VZA-014", "name": "Steel Plant Township 2",   "substation_name": "Steel Plant SS",   "district": "Visakhapatnam", "latitude": 17.6720, "longitude": 83.2020, "capacity_kva": 500, "installation_year": 2005},
    {"transformer_id": "TRF-VZA-015", "name": "Maddilapalem Feeder",      "substation_name": "Maddilapalem SS",  "district": "Visakhapatnam", "latitude": 17.7400, "longitude": 83.3000, "capacity_kva": 200, "installation_year": 2014},
    {"transformer_id": "TRF-VZA-016", "name": "Seethammadhara North",     "substation_name": "Seethammadhara SS","district": "Visakhapatnam", "latitude": 17.7450, "longitude": 83.3200, "capacity_kva": 315, "installation_year": 2012},
    {"transformer_id": "TRF-VZA-017", "name": "Rushikonda Beach",         "substation_name": "Rushikonda SS",    "district": "Visakhapatnam", "latitude": 17.7750, "longitude": 83.3900, "capacity_kva": 100, "installation_year": 2018},
    {"transformer_id": "TRF-VZA-018", "name": "NAD Junction",             "substation_name": "NAD SS",           "district": "Visakhapatnam", "latitude": 17.6950, "longitude": 83.2400, "capacity_kva": 200, "installation_year": 2010},
    {"transformer_id": "TRF-VZA-019", "name": "Simhachalam Temple Road",  "substation_name": "Simhachalam SS",   "district": "Visakhapatnam", "latitude": 17.7600, "longitude": 83.2700, "capacity_kva": 100, "installation_year": 2009},
    {"transformer_id": "TRF-VZA-020", "name": "Arilova Colony",           "substation_name": "Arilova SS",       "district": "Visakhapatnam", "latitude": 17.7100, "longitude": 83.2600, "capacity_kva": 315, "installation_year": 2016},

    # Anakapalle area
    {"transformer_id": "TRF-AKP-001", "name": "Anakapalle Town Centre",   "substation_name": "Anakapalle SS",    "district": "Anakapalle",    "latitude": 17.6910, "longitude": 82.9990, "capacity_kva": 200, "installation_year": 2011},
    {"transformer_id": "TRF-AKP-002", "name": "Anakapalle Industrial",    "substation_name": "Anakapalle SS",    "district": "Anakapalle",    "latitude": 17.6880, "longitude": 82.9950, "capacity_kva": 500, "installation_year": 2008},
    {"transformer_id": "TRF-AKP-003", "name": "Chodavaram Feeder",        "substation_name": "Chodavaram SS",    "district": "Anakapalle",    "latitude": 17.8300, "longitude": 82.9300, "capacity_kva": 100, "installation_year": 2013},
    {"transformer_id": "TRF-AKP-004", "name": "Yelamanchili Town",        "substation_name": "Yelamanchili SS",  "district": "Anakapalle",    "latitude": 17.5500, "longitude": 82.8700, "capacity_kva": 200, "installation_year": 2015},
    {"transformer_id": "TRF-AKP-005", "name": "Payakaraopeta Feeder",     "substation_name": "Payakaraopeta SS", "district": "Anakapalle",    "latitude": 17.3600, "longitude": 82.7600, "capacity_kva": 100, "installation_year": 2014},

    # Vizianagaram district
    {"transformer_id": "TRF-VZM-001", "name": "Vizianagaram Town 1",      "substation_name": "Vizianagaram SS",  "district": "Vizianagaram",  "latitude": 18.1066, "longitude": 83.3956, "capacity_kva": 315, "installation_year": 2010},
    {"transformer_id": "TRF-VZM-002", "name": "Vizianagaram Town 2",      "substation_name": "Vizianagaram SS",  "district": "Vizianagaram",  "latitude": 18.1100, "longitude": 83.4000, "capacity_kva": 200, "installation_year": 2012},
    {"transformer_id": "TRF-VZM-003", "name": "Bobbili Feeder",           "substation_name": "Bobbili SS",       "district": "Vizianagaram",  "latitude": 18.5733, "longitude": 83.3592, "capacity_kva": 100, "installation_year": 2011},
    {"transformer_id": "TRF-VZM-004", "name": "Parvathipuram Town",       "substation_name": "Parvathipuram SS", "district": "Vizianagaram",  "latitude": 18.7833, "longitude": 83.4333, "capacity_kva": 200, "installation_year": 2009},
    {"transformer_id": "TRF-VZM-005", "name": "Salur Colony",             "substation_name": "Salur SS",         "district": "Vizianagaram",  "latitude": 18.5200, "longitude": 83.2000, "capacity_kva": 100, "installation_year": 2015},

    # Srikakulam district
    {"transformer_id": "TRF-SKL-001", "name": "Srikakulam Town Main",     "substation_name": "Srikakulam SS",    "district": "Srikakulam",    "latitude": 18.2949, "longitude": 83.8938, "capacity_kva": 315, "installation_year": 2008},
    {"transformer_id": "TRF-SKL-002", "name": "Srikakulam Industrial",    "substation_name": "Srikakulam SS",    "district": "Srikakulam",    "latitude": 18.2900, "longitude": 83.8900, "capacity_kva": 500, "installation_year": 2007},
    {"transformer_id": "TRF-SKL-003", "name": "Narasannapeta Feeder",     "substation_name": "Narasannapeta SS", "district": "Srikakulam",    "latitude": 18.4150, "longitude": 83.9200, "capacity_kva": 100, "installation_year": 2014},
    {"transformer_id": "TRF-SKL-004", "name": "Palasa Town",              "substation_name": "Palasa SS",        "district": "Srikakulam",    "latitude": 18.7726, "longitude": 84.4125, "capacity_kva": 200, "installation_year": 2012},
    {"transformer_id": "TRF-SKL-005", "name": "Amadalavalasa Feeder",     "substation_name": "Amadalavalasa SS", "district": "Srikakulam",    "latitude": 18.4100, "longitude": 83.8900, "capacity_kva": 100, "installation_year": 2016},

    # East Godavari
    {"transformer_id": "TRF-EGD-001", "name": "Kakinada Port Area",       "substation_name": "Kakinada SS",      "district": "East Godavari", "latitude": 16.9891, "longitude": 82.2475, "capacity_kva": 630, "installation_year": 2006},
    {"transformer_id": "TRF-EGD-002", "name": "Kakinada Town Centre",     "substation_name": "Kakinada SS",      "district": "East Godavari", "latitude": 16.9800, "longitude": 82.2400, "capacity_kva": 315, "installation_year": 2010},
    {"transformer_id": "TRF-EGD-003", "name": "Rajahmundry Station Rd",   "substation_name": "Rajahmundry SS",   "district": "East Godavari", "latitude": 17.0050, "longitude": 81.7799, "capacity_kva": 500, "installation_year": 2009},
    {"transformer_id": "TRF-EGD-004", "name": "Rajahmundry Godavari Br",  "substation_name": "Rajahmundry SS",   "district": "East Godavari", "latitude": 17.0100, "longitude": 81.7850, "capacity_kva": 200, "installation_year": 2013},
    {"transformer_id": "TRF-EGD-005", "name": "Amalapuram Town",          "substation_name": "Amalapuram SS",    "district": "East Godavari", "latitude": 16.5833, "longitude": 82.0000, "capacity_kva": 200, "installation_year": 2011},

    # West Godavari
    {"transformer_id": "TRF-WGD-001", "name": "Eluru Town Main",          "substation_name": "Eluru SS",         "district": "West Godavari", "latitude": 16.7107, "longitude": 81.0952, "capacity_kva": 315, "installation_year": 2010},
    {"transformer_id": "TRF-WGD-002", "name": "Eluru Industrial Zone",    "substation_name": "Eluru SS",         "district": "West Godavari", "latitude": 16.7050, "longitude": 81.0900, "capacity_kva": 630, "installation_year": 2008},
    {"transformer_id": "TRF-WGD-003", "name": "Bhimavaram Town",          "substation_name": "Bhimavaram SS",    "district": "West Godavari", "latitude": 16.5449, "longitude": 81.5212, "capacity_kva": 315, "installation_year": 2012},
    {"transformer_id": "TRF-WGD-004", "name": "Bhimavaram Agricultural",  "substation_name": "Bhimavaram SS",    "district": "West Godavari", "latitude": 16.5400, "longitude": 81.5150, "capacity_kva": 200, "installation_year": 2009},
    {"transformer_id": "TRF-WGD-005", "name": "Tanuku Colony",            "substation_name": "Tanuku SS",        "district": "West Godavari", "latitude": 16.7550, "longitude": 81.6833, "capacity_kva": 100, "installation_year": 2015},

    # Krishna district
    {"transformer_id": "TRF-KRS-001", "name": "Machilipatnam Port",       "substation_name": "Machilipatnam SS", "district": "Krishna",       "latitude": 16.1875, "longitude": 81.1389, "capacity_kva": 500, "installation_year": 2007},
    {"transformer_id": "TRF-KRS-002", "name": "Machilipatnam Town",       "substation_name": "Machilipatnam SS", "district": "Krishna",       "latitude": 16.1900, "longitude": 81.1400, "capacity_kva": 200, "installation_year": 2011},
    {"transformer_id": "TRF-KRS-003", "name": "Gudivada Town Centre",     "substation_name": "Gudivada SS",      "district": "Krishna",       "latitude": 16.4350, "longitude": 80.9950, "capacity_kva": 315, "installation_year": 2013},
    {"transformer_id": "TRF-KRS-004", "name": "Gudivada Agricultural",    "substation_name": "Gudivada SS",      "district": "Krishna",       "latitude": 16.4300, "longitude": 80.9900, "capacity_kva": 200, "installation_year": 2010},
    {"transformer_id": "TRF-KRS-005", "name": "Nuzvid Colony Feeder",     "substation_name": "Nuzvid SS",        "district": "Krishna",       "latitude": 16.7850, "longitude": 80.8450, "capacity_kva": 100, "installation_year": 2016},
    
    # Visakhapatnam extended (021-050) — matches CSV transformer IDs
    {"transformer_id": "TRF-VZA-021", "name": "Waltair Uplands",        "substation_name": "Waltair SS",       "district": "Visakhapatnam", "latitude": 17.7350, "longitude": 83.3450, "capacity_kva": 200, "installation_year": 2013},
    {"transformer_id": "TRF-VZA-022", "name": "Marripalem Colony",      "substation_name": "Marripalem SS",    "district": "Visakhapatnam", "latitude": 17.7500, "longitude": 83.3600, "capacity_kva": 315, "installation_year": 2011},
    {"transformer_id": "TRF-VZA-023", "name": "Sujatha Nagar Feeder",   "substation_name": "Sujatha Nagar SS", "district": "Visakhapatnam", "latitude": 17.7650, "longitude": 83.3500, "capacity_kva": 200, "installation_year": 2009},
    {"transformer_id": "TRF-VZA-024", "name": "Jagadamba Junction",     "substation_name": "Jagadamba SS",     "district": "Visakhapatnam", "latitude": 17.7200, "longitude": 83.3200, "capacity_kva": 630, "installation_year": 2007},
    {"transformer_id": "TRF-VZA-025", "name": "Lawsons Bay Colony",     "substation_name": "Lawsons Bay SS",   "district": "Visakhapatnam", "latitude": 17.7400, "longitude": 83.3700, "capacity_kva": 100, "installation_year": 2017},
    {"transformer_id": "TRF-VZA-026", "name": "Gopalapatnam Feeder",    "substation_name": "Gopalapatnam SS",  "district": "Visakhapatnam", "latitude": 17.7800, "longitude": 83.2300, "capacity_kva": 315, "installation_year": 2012},
    {"transformer_id": "TRF-VZA-027", "name": "Chinwaltair Main",       "substation_name": "Chinwaltair SS",   "district": "Visakhapatnam", "latitude": 17.7300, "longitude": 83.3150, "capacity_kva": 200, "installation_year": 2010},
    {"transformer_id": "TRF-VZA-028", "name": "Akkayyapalem Colony",    "substation_name": "Akkayyapalem SS",  "district": "Visakhapatnam", "latitude": 17.7250, "longitude": 83.3050, "capacity_kva": 315, "installation_year": 2014},
    {"transformer_id": "TRF-VZA-029", "name": "PM Palem Sector 1",      "substation_name": "PM Palem SS",      "district": "Visakhapatnam", "latitude": 17.7700, "longitude": 83.2500, "capacity_kva": 200, "installation_year": 2016},
    {"transformer_id": "TRF-VZA-030", "name": "PM Palem Sector 2",      "substation_name": "PM Palem SS",      "district": "Visakhapatnam", "latitude": 17.7720, "longitude": 83.2520, "capacity_kva": 100, "installation_year": 2016},
    {"transformer_id": "TRF-VZA-031", "name": "Kurmannapalem Feeder",   "substation_name": "Kurmannapalem SS", "district": "Visakhapatnam", "latitude": 17.7550, "longitude": 83.2200, "capacity_kva": 500, "installation_year": 2008},
    {"transformer_id": "TRF-VZA-032", "name": "Madhurawada Colony",     "substation_name": "Madhurawada SS",   "district": "Visakhapatnam", "latitude": 17.8000, "longitude": 83.3800, "capacity_kva": 315, "installation_year": 2015},
    {"transformer_id": "TRF-VZA-033", "name": "BHPV Township",          "substation_name": "BHPV SS",          "district": "Visakhapatnam", "latitude": 17.6600, "longitude": 83.1900, "capacity_kva": 630, "installation_year": 2006},
    {"transformer_id": "TRF-VZA-034", "name": "Kapuluppada Feeder",     "substation_name": "Kapuluppada SS",   "district": "Visakhapatnam", "latitude": 17.8200, "longitude": 83.4000, "capacity_kva": 200, "installation_year": 2017},
    {"transformer_id": "TRF-VZA-035", "name": "Tagarapuvalasa Colony",  "substation_name": "Tagarapuvalasa SS","district": "Visakhapatnam", "latitude": 17.8300, "longitude": 83.3600, "capacity_kva": 100, "installation_year": 2018},
    {"transformer_id": "TRF-VZA-036", "name": "Bheemili Road Feeder",   "substation_name": "Bheemili SS",      "district": "Visakhapatnam", "latitude": 17.8600, "longitude": 83.4200, "capacity_kva": 200, "installation_year": 2011},
    {"transformer_id": "TRF-VZA-037", "name": "Hanumanthawaka Main",    "substation_name": "Hanumanthawaka SS","district": "Visakhapatnam", "latitude": 17.6850, "longitude": 83.2350, "capacity_kva": 315, "installation_year": 2010},
    {"transformer_id": "TRF-VZA-038", "name": "Kancharapalem Colony",   "substation_name": "Kancharapalem SS", "district": "Visakhapatnam", "latitude": 17.7050, "longitude": 83.2550, "capacity_kva": 200, "installation_year": 2013},
    {"transformer_id": "TRF-VZA-039", "name": "Vepagunta Feeder",       "substation_name": "Vepagunta SS",     "district": "Visakhapatnam", "latitude": 17.7950, "longitude": 83.3300, "capacity_kva": 500, "installation_year": 2009},
    {"transformer_id": "TRF-VZA-040", "name": "Duvvada Industrial",     "substation_name": "Duvvada SS",       "district": "Visakhapatnam", "latitude": 17.7400, "longitude": 83.1600, "capacity_kva": 630, "installation_year": 2007},
    {"transformer_id": "TRF-VZA-041", "name": "Sabbavaram Colony",      "substation_name": "Sabbavaram SS",    "district": "Visakhapatnam", "latitude": 17.7100, "longitude": 83.0900, "capacity_kva": 100, "installation_year": 2015},
    {"transformer_id": "TRF-VZA-042", "name": "Nakkapalli Town",        "substation_name": "Nakkapalli SS",    "district": "Visakhapatnam", "latitude": 17.7300, "longitude": 82.9200, "capacity_kva": 200, "installation_year": 2012},
    {"transformer_id": "TRF-VZA-043", "name": "Elamanchili Feeder",     "substation_name": "Elamanchili SS",   "district": "Visakhapatnam", "latitude": 17.5300, "longitude": 82.8500, "capacity_kva": 200, "installation_year": 2011},
    {"transformer_id": "TRF-VZA-044", "name": "Narsipatnam Town",       "substation_name": "Narsipatnam SS",   "district": "Visakhapatnam", "latitude": 17.6700, "longitude": 82.6100, "capacity_kva": 315, "installation_year": 2010},
    {"transformer_id": "TRF-VZA-045", "name": "Paderu Colony",          "substation_name": "Paderu SS",        "district": "Visakhapatnam", "latitude": 18.0700, "longitude": 82.6600, "capacity_kva": 100, "installation_year": 2014},
    {"transformer_id": "TRF-VZA-046", "name": "Araku Valley Feeder",     "substation_name": "Araku SS",         "district": "Visakhapatnam", "latitude": 18.3333, "longitude": 82.9000, "capacity_kva": 200, "installation_year": 2013},
    {"transformer_id": "TRF-VZA-047", "name": "Chintapalli Town",       "substation_name": "Chintapalli SS",   "district": "Visakhapatnam", "latitude": 18.1500, "longitude": 82.7500, "capacity_kva": 100, "installation_year": 2016},
    {"transformer_id": "TRF-VZA-048", "name": "Pithapuram Feeder",      "substation_name": "Pithapuram SS",    "district": "Visakhapatnam", "latitude": 17.2200, "longitude": 82.2500, "capacity_kva": 200, "installation_year": 2012},
    {"transformer_id": "TRF-VZA-049", "name": "Kothavalasa Town",       "substation_name": "Kothavalasa SS",   "district": "Visakhapatnam", "latitude": 17.9000, "longitude": 83.0000, "capacity_kva": 315, "installation_year": 2011},
    {"transformer_id": "TRF-VZA-050", "name": "Salur Feeder",           "substation_name": "Salur SS",         "district": "Visakhapatnam", "latitude": 18.5200, "longitude": 83.2000, "capacity_kva": 100, "installation_year": 2015},
]


def seed_transformers():
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(Transformer).count()
        if existing > 0:
            print(f"Database already has {existing} transformers. Skipping seed.")
            print("To re-seed, delete all rows from the transformers table in pgAdmin first.")
            return

        print("Seeding 50 transformers into database...")

        for data in TRANSFORMERS:
            transformer = Transformer(**data)
            db.add(transformer)

        db.commit()
        print(f"✓ Successfully inserted {len(TRANSFORMERS)} transformers")
        print("\nDistrict breakdown:")

        # Show summary
        from sqlalchemy import func
        results = db.query(
            Transformer.district,
            func.count(Transformer.id).label("count")
        ).group_by(Transformer.district).all()

        for district, count in results:
            print(f"  {district}: {count} transformers")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_transformers()