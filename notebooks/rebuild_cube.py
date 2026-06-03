from sqlalchemy import create_engine, text

DB_URL = "mysql+pymysql://root:1882005@localhost:3307/aqi_dw?charset=utf8mb4"
engine = create_engine(DB_URL, pool_pre_ping=True)
MIN_SUP = 100

sql_cs = f"""
    INSERT INTO cube_city_season
        (city, country, season, pollutant_code,
         reading_count, avg_aqi, max_aqi, avg_conc, unhealthy_cnt)
    SELECT l.city, l.country, t.season, p.pollutant_code,
           COUNT(*), ROUND(AVG(f.aqi_value),2),
           MAX(f.aqi_value), ROUND(AVG(f.concentration),4),
           SUM(CASE WHEN f.aqi_value > 150 THEN 1 ELSE 0 END)
    FROM fact_aqi_reading f
    JOIN dim_location  l ON f.location_key  = l.location_key
    JOIN dim_time      t ON f.time_key      = t.time_key
    JOIN dim_pollutant p ON f.pollutant_key = p.pollutant_key
    WHERE f.is_anomaly = 0
    GROUP BY l.city, l.country, t.season, p.pollutant_code
    HAVING COUNT(*) >= {MIN_SUP}
    ON DUPLICATE KEY UPDATE
        reading_count = VALUES(reading_count),
        avg_aqi       = VALUES(avg_aqi),
        max_aqi       = VALUES(max_aqi),
        avg_conc      = VALUES(avg_conc),
        unhealthy_cnt = VALUES(unhealthy_cnt),
        computed_at   = NOW()
"""

sql_cm = f"""
    INSERT INTO cube_city_month
        (city, country, year, month, pollutant_code,
         reading_count, avg_aqi, max_aqi)
    SELECT l.city, l.country, t.year, t.month, p.pollutant_code,
           COUNT(*), ROUND(AVG(f.aqi_value),2), MAX(f.aqi_value)
    FROM fact_aqi_reading f
    JOIN dim_location  l ON f.location_key  = l.location_key
    JOIN dim_time      t ON f.time_key      = t.time_key
    JOIN dim_pollutant p ON f.pollutant_key = p.pollutant_key
    WHERE f.is_anomaly = 0
    GROUP BY l.city, l.country, t.year, t.month, p.pollutant_code
    HAVING COUNT(*) >= {MIN_SUP}
    ON DUPLICATE KEY UPDATE
        reading_count = VALUES(reading_count),
        avg_aqi       = VALUES(avg_aqi),
        max_aqi       = VALUES(max_aqi),
        computed_at   = NOW()
"""

print("=== Rebuild Iceberg Cube ===")
with engine.connect() as conn:
    print("Truncating cũ...")
    conn.execute(text("TRUNCATE TABLE cube_city_season"))
    conn.execute(text("TRUNCATE TABLE cube_city_month"))
    conn.commit()

    print("Building cube_city_season...")
    conn.execute(text(sql_cs))
    conn.commit()
    n = conn.execute(text("SELECT COUNT(*) FROM cube_city_season")).scalar()
    print(f"  ✓ cube_city_season: {n:,} cells")

    print("Building cube_city_month...")
    conn.execute(text(sql_cm))
    conn.commit()
    n = conn.execute(text("SELECT COUNT(*) FROM cube_city_month")).scalar()
    print(f"  ✓ cube_city_month: {n:,} cells")

    # Kiểm tra năm
    years = conn.execute(text(
        "SELECT MIN(year), MAX(year), COUNT(DISTINCT year) FROM cube_city_month"
    )).fetchone()
    print(f"\n  Năm: {years[0]} → {years[1]} ({years[2]} năm)")

print("=== Done! F5 lại Dashboard ===")