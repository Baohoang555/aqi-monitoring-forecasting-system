from database.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
rows = db.execute(text("""
    SELECT l.city,
        AVG(CASE WHEN p.pollutant_code IN ('PM2.5','PM25') THEN f.concentration END) as pm25,
        AVG(CASE WHEN p.pollutant_code = 'PM10' THEN f.concentration END) as pm10,
        AVG(CASE WHEN p.pollutant_code = 'NO2' THEN f.concentration END) as no2
    FROM fact_aqi_reading f
    JOIN dim_location l ON f.location_key = l.location_key
    JOIN dim_pollutant p ON f.pollutant_key = p.pollutant_key
    WHERE l.city = 'Abbottabad'
    GROUP BY l.city
""")).fetchall()
print(rows)