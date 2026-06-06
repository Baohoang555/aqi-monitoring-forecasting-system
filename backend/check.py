from database.session import SessionLocal
from sqlalchemy import text
db = SessionLocal()
rows = db.execute(text("SELECT pollutant_code, avg_aqi FROM cube_city_season WHERE city='Ariquemes'")).fetchall()
for r in rows:
    print(r)