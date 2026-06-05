"""
PH-04: ETL Pipeline — Parquet → MariaDB
Đọc data từ datalake Parquet (do nhóm PH-01/02/03 tạo), load vào MariaDB DW.

Không cần Spark. Dùng pandas + pymysql thuần.

Cài đặt:
    pip install pandas pyarrow pymysql sqlalchemy

Chạy:
    python etl/etl_pipeline.py
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine, text

# ─── Cấu hình ───────────────────────────────────────────────────────────────
DB_HOST: str = "localhost"
DB_PORT: int = 3306
DB_USER: str = "root"
DB_PASSWORD: str = "123"
DB_NAME: str = "aqi_dw"
DB_CHARSET: str = "utf8mb4"

ENGINE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}"
)

# Thư mục Parquet từ PH-01 (chỉnh lại đường dẫn cho đúng)
BASE_DIR    = Path(__file__).resolve().parent.parent
PARQUET_DIR = Path(r"C:\Users\ASUS\Documents\DATA_FINAL-1\data")
MIN_SUP  = 100   # Ngưỡng Iceberg Cube
BATCH_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("aqi_etl")


# ══════════════════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════════════════

def get_engine():
    return create_engine(ENGINE_URL, pool_pre_ping=True)


def mysql_connect():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset=DB_CHARSET,
    )


def run_sql(sql: str, engine=None):
    eng = engine or get_engine()
    with eng.connect() as conn:
        conn.execute(text(sql))
        conn.commit()


# ══════════════════════════════════════════════════════════════════════════
# EXTRACT
# ══════════════════════════════════════════════════════════════════════════

def extract() -> pd.DataFrame:
    """Đọc tất cả các file CSV thô từ thư mục Kaggle."""
    # Quét toàn bộ file có đuôi .csv trong thư mục và các thư mục con
    files = list(PARQUET_DIR.rglob("*.csv"))
    if not files:
        raise FileNotFoundError(f"Không tìm thấy file CSV nào trong thư mục: {PARQUET_DIR}")
    log.info(f"Bắt đầu đọc {len(files)} file CSV từ Data Lake thô...")
    
    # Đọc và gộp tất cả các file CSV lại thành một DataFrame duy nhất
    df = pd.concat([pd.read_csv(f, low_memory=False) for f in files], ignore_index=True)
    log.info(f" Trích xuất thành công: {len(df):,} dòng, {df.shape[1]} thuộc tính.")
    return df


# ══════════════════════════════════════════════════════════════════════════
# TRANSFORM
# ══════════════════════════════════════════════════════════════════════════

def _season(month: int) -> str:
    """Phân loại mùa đơn giản theo tháng (nhiệt đới)."""
    return "dry" if month in (11, 12, 1, 2, 3, 4) else "rainy"


def _aqi_category(aqi) -> str:
    if pd.isna(aqi):   return "Unknown"
    if aqi <= 50:       return "Good"
    if aqi <= 100:      return "Moderate"
    if aqi <= 150:      return "Unhealthy SG"
    if aqi <= 200:      return "Unhealthy"
    if aqi <= 300:      return "Very Unhealthy"
    return "Hazardous"


def _calc_aqi_pm25(c) -> float | None:
    """Tính AQI từ PM2.5 theo chuẩn EPA."""
    BP = [(0,12,0,50),(12.1,35.4,51,100),(35.5,55.4,101,150),
          (55.5,150.4,151,200),(150.5,250.4,201,300),(250.5,500.4,301,500)]
    if pd.isna(c) or c < 0: return None
    for lo, hi, alo, ahi in BP:
        if lo <= c <= hi:
            return round((ahi - alo) / (hi - lo) * (c - lo) + alo)
    return None


def transform(df: pd.DataFrame):
    """Trả về 4 DataFrame đã chuẩn hoá."""
    df.columns = [c.lower().strip() for c in df.columns]
    # Chuẩn hóa tên cột (tương thích eda_analysis.py của Thọ)
    rename = {
        "date": "date", "city": "city", "country": "country",
        "aqi": "aqi", "pm2.5 (ug/m3)": "pm25", "pm10 (ug/m3)": "pm10",
        "no2 (ug/m3)": "no2", "so2 (ug/m3)": "so2",
        "co (mg/m3)": "co",   "o3 (ug/m3)": "o3",
        "no (ug/m3)": "no",   "nh3 (ug/m3)": "nh3",
    }
    df = df.rename(columns=rename)
    # 3. KỸ THUẬT PHÒNG THỦ: Nếu file thiếu hẳn cột 'country' hoặc 'city'
    if "country" not in df.columns:
        # Nếu thiếu, ta mặc định gắn một giá trị tạm thời hoặc để trống thay vì sập hệ thống
        df["country"] = "Unknown" 
        
    if "city" not in df.columns:
        # Nếu file trạm đo phân tách theo thư mục mà trong file không có cột city
        df["city"] = "Unknown"
    # 4. Ép kiểu dữ liệu thời gian một cách an toàn
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Lọc bỏ dòng lỗi date hoặc city
    df = df.dropna(subset=["date", "city", "country"])
    
    # Chuẩn hóa viết hoa chữ cái đầu
    df["city"]    = df["city"].astype(str).str.strip().str.title()
    df["country"] = df["country"].astype(str).str.strip().str.title()

    # Tính AQI nếu thiếu và bảo đảm cột aqi luôn tồn tại
    if "aqi" not in df.columns:
        df["aqi"] = pd.NA
    if "pm25" in df.columns:
        missing_aqi = df["aqi"].isna() & df["pm25"].notna()
        df.loc[missing_aqi, "aqi"] = df.loc[missing_aqi, "pm25"].apply(_calc_aqi_pm25)

    df["aqi_category"] = df["aqi"].apply(_aqi_category)

    # Anomaly: z-score > 4 theo city
    if "aqi" in df.columns:
        grp = df.groupby("city")["aqi"]
        df["z"] = (df["aqi"] - grp.transform("mean")) / (grp.transform("std") + 1e-9)
        df["is_anomaly"] = (df["z"].abs() > 4).astype(int)
        df.drop(columns="z", inplace=True)
    else:
        df["is_anomaly"] = 0

    # ── DIM_TIME ──────────────────────────────────────────────────────
    dates = df["date"].dt.normalize().unique()
    dim_time = pd.DataFrame({"full_date": pd.to_datetime(dates)})
    dim_time["year"]       = dim_time["full_date"].dt.year
    dim_time["month"]      = dim_time["full_date"].dt.month
    dim_time["month_name"] = dim_time["full_date"].dt.strftime("%B")
    dim_time["quarter"]    = dim_time["full_date"].dt.quarter
    dim_time["day"]        = dim_time["full_date"].dt.day
    dim_time["week"]       = dim_time["full_date"].dt.isocalendar().week.astype(int)
    dim_time["season"]     = dim_time["month"].apply(_season)
    dim_time["is_weekend"] = dim_time["full_date"].dt.dayofweek.isin([5, 6]).astype(int)
    dim_time["full_date"]  = dim_time["full_date"].dt.strftime("%Y-%m-%d")

    # ── DIM_LOCATION ──────────────────────────────────────────────────
    dim_location = (df[["city", "country"]]
                    .drop_duplicates()
                    .reset_index(drop=True))
    if "country_code" in df.columns:
        dim_location = dim_location.merge(
            df[["country", "country_code"]].drop_duplicates(), on="country", how="left")
    if "continent" in df.columns:
        dim_location = dim_location.merge(
            df[["country", "continent"]].drop_duplicates(), on="country", how="left")

    # ── MELT → pollutants ─────────────────────────────────────────────
    pollutant_cols = [c for c in ["pm25","pm10","no2","so2","co","o3","no","nh3"]
                      if c in df.columns]
    code_map = {"pm25":"PM2.5","pm10":"PM10","no2":"NO2",
                "so2":"SO2","co":"CO","o3":"O3","no":"NO","nh3":"NH3"}

    id_vars = ["date","city","country","aqi","aqi_category","is_anomaly"]
    id_vars = [c for c in id_vars if c in df.columns]

    long = df[id_vars + pollutant_cols].melt(
        id_vars=id_vars,
        value_vars=pollutant_cols,
        var_name="pollutant_raw",
        value_name="concentration"
    )
    long["pollutant_code"] = long["pollutant_raw"].map(code_map)
    long.dropna(subset=["concentration"], inplace=True)

    log.info(f"  Transform xong: {len(dim_time)} ngày, "
             f"{len(dim_location)} địa điểm, {len(long):,} bản ghi đo")
    return dim_time, dim_location, long


# ══════════════════════════════════════════════════════════════════════════
# LOAD
# ══════════════════════════════════════════════════════════════════════════

def load_dim_time(dim_time: pd.DataFrame, engine) -> dict:
    """Upsert dim_time, trả về {date_str: time_key}."""
    log.info(f"  Load dim_time: {len(dim_time)} dòng...")
    sql = """
        INSERT IGNORE INTO dim_time
            (full_date, year, month, month_name, quarter, day, week, season, is_weekend)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    conn = mysql_connect()
    with conn.cursor() as cur:
        cur.executemany(sql, dim_time.values.tolist())
    conn.commit()
    conn.close()

    with engine.connect() as c:
        rows = c.execute(text("SELECT time_key, full_date FROM dim_time")).fetchall()
    return {str(r[1]): r[0] for r in rows}


def load_dim_location(dim_location: pd.DataFrame, engine) -> dict:
    """Upsert dim_location, trả về {(city, country): location_key}."""
    log.info(f"  Load dim_location: {len(dim_location)} dòng...")
    cols = ["city", "country"]
    extra = [c for c in ["country_code", "continent"] if c in dim_location.columns]
    insert_cols = cols + extra
    placeholders = ", ".join(["%s"] * len(insert_cols))
    sql = f"INSERT IGNORE INTO dim_location ({', '.join(insert_cols)}) VALUES ({placeholders})"

    conn = mysql_connect()
    with conn.cursor() as cur:
        cur.executemany(sql, dim_location[insert_cols].values.tolist())
    conn.commit()
    conn.close()

    with engine.connect() as c:
        rows = c.execute(
            text("SELECT location_key, city, country FROM dim_location")
        ).fetchall()
    return {(r[1], r[2]): r[0] for r in rows}


def load_dim_pollutant(engine) -> dict:
    """Đã seed trong SQL, chỉ cần đọc mapping."""
    with engine.connect() as c:
        rows = c.execute(
            text("SELECT pollutant_key, pollutant_code FROM dim_pollutant")
        ).fetchall()
    return {r[1]: r[0] for r in rows}


def load_fact(long: pd.DataFrame,
              time_map: dict, loc_map: dict, poll_map: dict,
              engine, chunk_size: int = 5000) -> int:
    """Load fact table theo từng chunk."""
    long["date_str"] = long["date"].dt.strftime("%Y-%m-%d")
    long["time_key"]      = long["date_str"].map(time_map)
    long["location_key"]  = long.apply(
        lambda r: loc_map.get((r["city"], r["country"])), axis=1)
    long["pollutant_key"] = long["pollutant_code"].map(poll_map)

    fact = long.dropna(subset=["time_key","location_key","pollutant_key"]).copy()
    fact["time_key"]     = fact["time_key"].astype(int)
    fact["location_key"] = fact["location_key"].astype(int)
    fact["pollutant_key"]= fact["pollutant_key"].astype(int)
    fact["aqi_value"]    = pd.to_numeric(fact["aqi"], errors="coerce").astype("Int64")
    fact["batch_id"]     = BATCH_ID

    cols = ["time_key","location_key","pollutant_key",
            "concentration","aqi_value","aqi_category","is_anomaly","batch_id"]
    cols = [c for c in cols if c in fact.columns]

    sql = f"""
        INSERT INTO fact_aqi_reading ({', '.join(cols)})
        VALUES ({', '.join(['%s']*len(cols))})
    """
    conn = mysql_connect()
    total = 0
    with conn.cursor() as cur:
        for i in range(0, len(fact), chunk_size):
            chunk_df = fact.iloc[i:i+chunk_size][cols]
            rows = [
                [None if pd.isna(value) else value for value in row]
                for row in chunk_df.itertuples(index=False, name=None)
            ]
            if rows:
                cur.executemany(sql, rows)
                conn.commit()
                total += len(rows)
                log.info(f"    Chunk {i//chunk_size+1}: {total:,}/{len(fact):,} dòng")
    conn.close()
    log.info(f"  ✓ Fact loaded: {total:,} dòng")
    return total


# ══════════════════════════════════════════════════════════════════════════
# ICEBERG CUBE (min_sup = 100)
# ══════════════════════════════════════════════════════════════════════════

def build_iceberg_cube(engine):
    """
    Xây Iceberg Cube bằng SQL thuần trong MariaDB.
    Chỉ vật hoá cuboid có reading_count >= MIN_SUP.
    """
    log.info("  Xây Iceberg Cube...")

    # Cube: City × Season × Pollutant
    sql_cs = f"""
        INSERT INTO cube_city_season
            (city, country, season, pollutant_code,
             reading_count, avg_aqi, max_aqi, avg_conc, unhealthy_cnt)
        SELECT
            l.city, l.country, t.season, p.pollutant_code,
            COUNT(*)                                          AS reading_count,
            ROUND(AVG(f.aqi_value), 2)                       AS avg_aqi,
            MAX(f.aqi_value)                                  AS max_aqi,
            ROUND(AVG(f.concentration), 4)                   AS avg_conc,
            SUM(CASE WHEN f.aqi_value > 150 THEN 1 ELSE 0 END) AS unhealthy_cnt
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

    # Cube: City × Month × Pollutant
    sql_cm = f"""
        INSERT INTO cube_city_month
            (city, country, year, month, pollutant_code,
             reading_count, avg_aqi, max_aqi)
        SELECT
            l.city, l.country, t.year, t.month, p.pollutant_code,
            COUNT(*)                   AS reading_count,
            ROUND(AVG(f.aqi_value),2)  AS avg_aqi,
            MAX(f.aqi_value)           AS max_aqi
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

    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE cube_city_season"))
        conn.execute(text("TRUNCATE TABLE cube_city_month"))
        conn.execute(text(sql_cs))
        conn.execute(text(sql_cm))
        conn.commit()

    with engine.connect() as conn:
        n_cs = conn.execute(text("SELECT COUNT(*) FROM cube_city_season")).scalar()
        n_cm = conn.execute(text("SELECT COUNT(*) FROM cube_city_month")).scalar()

    log.info(f"  ✓ cube_city_season : {n_cs:,} cells (min_sup={MIN_SUP})")
    log.info(f"  ✓ cube_city_month  : {n_cm:,} cells (min_sup={MIN_SUP})")


# ══════════════════════════════════════════════════════════════════════════
# OLAP QUERIES MẪU
# ══════════════════════════════════════════════════════════════════════════

def run_olap_queries(engine):
    """In kết quả một số OLAP query mẫu."""
    queries = {
        "Top 10 thành phố ô nhiễm nhất (PM2.5, mùa khô)": """
            SELECT city, country, avg_aqi, max_aqi, unhealthy_cnt
            FROM cube_city_season
            WHERE season = 'dry' AND pollutant_code = 'PM2.5'
            ORDER BY avg_aqi DESC
            LIMIT 10
        """,
        "Xu hướng AQI theo năm (toàn cầu)": """
            SELECT year, ROUND(AVG(avg_aqi),1) AS global_avg_aqi
            FROM cube_city_month
            WHERE pollutant_code = 'PM2.5'
            GROUP BY year
            ORDER BY year
        """,
        "So sánh mùa khô vs mưa (PM2.5)": """
            SELECT season,
                   ROUND(AVG(avg_aqi),1)  AS avg_aqi,
                   MAX(max_aqi)           AS max_aqi,
                   SUM(unhealthy_cnt)     AS total_unhealthy
            FROM cube_city_season
            WHERE pollutant_code = 'PM2.5'
            GROUP BY season
        """,
    }

    print("\n" + "=" * 60)
    print("OLAP QUERY RESULTS")
    print("=" * 60)
    for title, sql in queries.items():
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        print(f"\n▶ {title}")
        print(df.to_string(index=False))
    print("=" * 60)


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════

def main():
    log.info(f"=== AQI ETL Start | batch={BATCH_ID} ===")
    engine = get_engine()
    start = datetime.now()

    try:
        # 1. Lấy danh sách tất cả các file CSV
        files = list(PARQUET_DIR.rglob("*.csv"))
        if not files:
            raise FileNotFoundError(f"Không tìm thấy file CSV nào trong thư mục: {PARQUET_DIR}")
        log.info(f"Tìm thấy {len(files)} file CSV. Bắt đầu xử lý cuốn chiếu từng file để tiết kiệm RAM...")

        total_rows_loaded = 0
        
        # 2. Vòng lặp xử lý từng file một
        for idx, file_path in enumerate(files, 1):
            log.info(f"[{idx}/{len(files)}] Đang xử lý file: {file_path.name}")
            
            # Đọc duy nhất 1 file
            raw_chunk = pd.read_csv(file_path, low_memory=False)
            if raw_chunk.empty:
                continue
                
            # 3. Transform phần dữ liệu nhỏ
            dim_time, dim_location, long_chunk = transform(raw_chunk)
            if long_chunk.empty:
                continue

            # 4. Load dimensions (Hàm INSERT IGNORE sẽ tự bỏ qua nếu đã trùng khóa)
            time_map = load_dim_time(dim_time, engine)
            loc_map = load_dim_location(dim_location, engine)
            poll_map = load_dim_pollutant(engine)

            # 5. Load fact table cho chunk hiện tại
            chunk_rows = load_fact(long_chunk, time_map, loc_map, poll_map, engine)
            total_rows_loaded += chunk_rows
            
            # Giải phóng bộ nhớ RAM sau khi xong 1 file
            del raw_chunk, dim_time, dim_location, long_chunk
            import gc
            gc.collect()

        # 6. Sau khi tất cả dữ liệu Fact đã lên kho, tiến hành xây dựng Iceberg Cube bằng SQL
        # Việc tính toán Cube lúc này diễn ra trực tiếp trong MariaDB, không tốn RAM của Python nữa
        build_iceberg_cube(engine)

        # 7. Chạy các câu lệnh OLAP mẫu kiểm tra
        run_olap_queries(engine)

        # 8. Ghi log hoàn thành
        elapsed = (datetime.now() - start).seconds
        conn = mysql_connect()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO etl_log (batch_id, rows_loaded, status, notes) VALUES (%s,%s,%s,%s)",
                (BATCH_ID, total_rows_loaded, "success", f"Elapsed {elapsed}s | Processed {len(files)} files")
            )
        conn.commit()
        conn.close()

        log.info(f"=== ETL Done | Tổng số {total_rows_loaded:,} dòng Fact đã nạp | Thời gian: {elapsed}s ===")

    except Exception as e:
        log.error(f"ETL FAILED: {e}")
        conn = mysql_connect()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO etl_log (batch_id, rows_loaded, status, notes) VALUES (%s,%s,%s,%s)",
                (BATCH_ID, 0, "failed", str(e)[:500])
            )
        conn.commit()
        conn.close()
        raise


if __name__ == "__main__":
    main()
