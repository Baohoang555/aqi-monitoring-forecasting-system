from database.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()

indexes = [
    "CREATE INDEX IF NOT EXISTS idx_fact_location ON fact_aqi_reading (location_key)",
    "CREATE INDEX IF NOT EXISTS idx_fact_pollutant ON fact_aqi_reading (pollutant_key)",
]

for sql in indexes:
    try:
        db.execute(text(sql))
        db.commit()
        print(f"✅ {sql[:50]}...")
    except Exception as e:
        print(f"❌ {e}")

print("Done")