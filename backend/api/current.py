from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database.session import get_session
from core.config import OPENWEATHER_API_KEY, WAQI_API_TOKEN
from services.aqi_provider.waqi import WaqiProvider
from typing import Optional
from pathlib import Path
from urllib.parse import quote_plus
import json
import requests
import traceback

router = APIRouter()

CACHE_FILE = Path(__file__).resolve().parent.parent / "city_geo_cache.json"
_geo_cache = None


def load_city_geo_cache():
    global _geo_cache
    if _geo_cache is not None:
        return _geo_cache
    try:
        if CACHE_FILE.exists():
            with CACHE_FILE.open("r", encoding="utf-8") as f:
                _geo_cache = json.load(f)
        else:
            _geo_cache = {}
    except Exception:
        _geo_cache = {}
    return _geo_cache


def save_city_geo_cache(cache):
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CACHE_FILE.open("w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def normalize_city_key(city: str, country: Optional[str] = None):
    key = city.strip() if city else ""
    if country:
        key = f"{key},{country.strip()}"
    return key


def query_dim_location_coords(db: Session, city: str, country: Optional[str] = None):
    queries = [
        ("SELECT latitude, longitude FROM dim_location WHERE city = :city LIMIT 1", {"city": city}),
        ("SELECT lat, lon FROM dim_location WHERE city = :city LIMIT 1", {"city": city}),
    ]
    if country:
        queries = [
            ("SELECT latitude, longitude FROM dim_location WHERE city = :city AND country = :country LIMIT 1", {"city": city, "country": country}),
            ("SELECT lat, lon FROM dim_location WHERE city = :city AND country = :country LIMIT 1", {"city": city, "country": country}),
            ("SELECT latitude, longitude FROM dim_location WHERE city = :city LIMIT 1", {"city": city}),
            ("SELECT lat, lon FROM dim_location WHERE city = :city LIMIT 1", {"city": city}),
        ]
    for sql_text, params in queries:
        try:
            loc_res = db.execute(text(sql_text), params).first()
            if loc_res and loc_res[0] is not None and loc_res[1] is not None:
                return float(loc_res[0]), float(loc_res[1])
        except Exception:
            continue
    return None


def geocode_city_openweather(city: str, country: Optional[str] = None):
    if not OPENWEATHER_API_KEY:
        return None
    q = city
    if country:
        q = f"{city},{country}"
    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={quote_plus(q)}&limit=1&appid={OPENWEATHER_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            first = data[0]
            if first.get("lat") is not None and first.get("lon") is not None:
                return float(first["lat"]), float(first["lon"])
    except Exception:
        pass
    return None


def geocode_city_waqi(city: str, country: Optional[str] = None):
    if not WAQI_API_TOKEN:
        return None
    try:
        provider = WaqiProvider()
        query = f"{city},{country}" if country else city
        info = provider.get_city_data(query)
        lat = info.get("lat")
        lon = info.get("lon")
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    except Exception:
        pass
    return None


def resolve_city_coordinates(db: Session, city: str, country: Optional[str] = None, allow_external: bool = True):
    cache = load_city_geo_cache()
    key = normalize_city_key(city, country)
    if key in cache:
        coords = cache[key]
        if coords and coords.get("lat") is not None and coords.get("lon") is not None:
            return coords["lat"], coords["lon"]

    coords = query_dim_location_coords(db, city, country)
    source = "dim_location"
    if coords is None and allow_external:
        coords = geocode_city_openweather(city, country)
        source = "openweather"
    if coords is None and allow_external:
        coords = geocode_city_waqi(city, country)
        source = "waqi"

    if coords is not None:
        new_entry = {"lat": coords[0], "lon": coords[1], "source": source}
        if cache.get(key) != new_entry:
            cache[key] = new_entry
            save_city_geo_cache(cache)

    return coords

# 1. API lấy chi tiết cho 1 thành phố (Phục vụ ô Dropdown ở Dashboard)
@router.get("/current/{city}")
def get_current_aqi(city: str, db: Session = Depends(get_session)):
    try:
        # Lấy dữ liệu pollutant thực tế từ khối cube hiện tại.
        sql = text("""
            SELECT pollutant_code, AVG(avg_aqi) as avg_aqi
            FROM cube_city_season
            WHERE city = :city
            GROUP BY pollutant_code
        """)
        result = db.execute(sql, {"city": city}).fetchall()
        
        pm25 = None
        pm10 = None
        no2 = None
        has_data = False
        
        for row in result:
            has_data = True
            val = float(row[1]) if row[1] is not None else None
            code = str(row[0]).lower() if row[0] else ""
            if "pm2.5" in code or "pm25" in code:
                pm25 = val
            elif "pm10" in code:
                pm10 = val
            elif "no2" in code:
                no2 = val
                
        # Nếu không có dữ liệu pollutant-specific, fallback về trung bình chung của city
        if not has_data:
            fallback_res = db.execute(text("SELECT AVG(avg_aqi) FROM cube_city_season WHERE city = :city"), {"city": city}).scalar()
            if fallback_res is not None:
                pm25 = float(fallback_res)
                pm10 = round(pm25 * 1.3, 1)
                no2 = round(pm25 * 0.4, 1)

        # Đảm bảo luôn có giá trị số cho frontend
        pm25 = round(pm25, 1) if pm25 is not None else None
        pm10 = round(pm10, 1) if pm10 is not None else None
        no2 = round(no2, 1) if no2 is not None else None

        lat_lon = resolve_city_coordinates(db, city)
        lat, lon = lat_lon if lat_lon is not None else (None, None)

        return {
            "success": True,
            "data": {
                "pm25": pm25, "pm10": pm10, "no2": no2,
                "temperature": 27.0, "humidity": 65.0,
                "lat": lat, "lon": lon
            }
        }
    except Exception as e:
        return {"success": False, "detail": str(e)}


# 2. API Gom cụm tổng lực (Tách biệt luồng để không bị lọc mất trạm)
@router.get("/current-all-stations")
def get_all_stations_aqi(db: Session = Depends(get_session)):
    try:
        # Bước A: Lấy dữ liệu pollutant-specific từ cube, để frontend được giá trị PM2.5 / PM10 / NO2 chính xác.
        sql = text("""
            SELECT
                city,
                AVG(CASE WHEN pollutant_code IN ('PM2.5','PM25') THEN avg_aqi END) AS pm25,
                AVG(CASE WHEN pollutant_code = 'PM10' THEN avg_aqi END) AS pm10,
                AVG(CASE WHEN pollutant_code = 'NO2' THEN avg_aqi END) AS no2
            FROM cube_city_season
            GROUP BY city
        """)
        rows = db.execute(sql).fetchall()
        
        station_map = {}
        for row in rows:
            city_name = row[0]
            if not city_name:
                continue

            pm25 = float(row[1]) if row[1] is not None else None
            pm10 = float(row[2]) if row[2] is not None else None
            no2 = float(row[3]) if row[3] is not None else None
            
            station_map[city_name] = {
                "country": None,
                "pm25": round(pm25, 1) if pm25 is not None else None,
                "pm10": round(pm10, 1) if pm10 is not None else None,
                "no2": round(no2, 1) if no2 is not None else None,
                "temperature": 26.0,
                "humidity": 70.0,
                "lat": None,
                "lon": None,
            }

        try:
            country_rows = db.execute(text("SELECT city, country FROM dim_location")).fetchall()
            for city_name, country_name in country_rows:
                if city_name in station_map and country_name:
                    station_map[city_name]["country"] = country_name
        except Exception:
            pass
        
        # Bước B: Nếu dim_location chứa tọa độ, bổ sung luôn.
        try:
            loc_rows = db.execute(text("SELECT city, latitude, longitude FROM dim_location")).fetchall()
        except Exception:
            try:
                loc_rows = db.execute(text("SELECT city, lat, lon FROM dim_location")).fetchall()
            except Exception:
                loc_rows = []
        
        for l_row in loc_rows:
            c_name = l_row[0]
            if c_name in station_map:
                station_map[c_name]["lat"] = float(l_row[1]) if l_row[1] is not None else None
                station_map[c_name]["lon"] = float(l_row[2]) if l_row[2] is not None else None

        # Bước C: Với các thành phố chưa có tọa độ, dùng cache để tránh gọi API ngoài tuyến.
        geo_cache = load_city_geo_cache()
        for city_name, station in station_map.items():
            if station["lat"] is None or station["lon"] is None:
                key = normalize_city_key(city_name, station.get("country"))
                cache_entry = geo_cache.get(key)
                if cache_entry and cache_entry.get("lat") is not None and cache_entry.get("lon") is not None:
                    station["lat"], station["lon"] = cache_entry["lat"], cache_entry["lon"]
            station.pop("country", None)

        return {
            "success": True,
            "data": station_map
        }
    except Exception as e:
        return {"success": False, "detail": str(e)}