# Set-Location 'f:\DATA_FINAL'
#  chạy: python .\backend\scripts\build_city_geo_cache.py --delay 1.0
import json
import sys
import time
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote_plus

import requests
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

CACHE_FILE = ROOT_DIR / "city_geo_cache.json"
ENV_FILE = ROOT_DIR / ".env"

OPENWEATHER_API_KEY = None
WAQI_API_TOKEN = None


def load_env(path: Path) -> Dict[str, str]:
    env = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def load_cache() -> Dict[str, Dict]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, Dict]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_city_key(city: str, country: Optional[str] = None) -> str:
    key = city.strip() if city else ""
    if country:
        key = f"{key},{country.strip()}"
    return key


def geocode_openweather(city: str, country: Optional[str] = None) -> Optional[tuple[float, float]]:
    if not OPENWEATHER_API_KEY:
        return None
    q = city if not country else f"{city},{country}"
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={quote_plus(q)}&limit=1&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            first = data[0]
            if first.get("lat") is not None and first.get("lon") is not None:
                return float(first["lat"]), float(first["lon"])
    except Exception:
        return None
    return None


def geocode_waqi(city: str, country: Optional[str] = None) -> Optional[tuple[float, float]]:
    if not WAQI_API_TOKEN:
        return None
    from services.aqi_provider.waqi import WaqiProvider
    try:
        provider = WaqiProvider()
        query = f"{city},{country}" if country else city
        info = provider.get_city_data(query)
        lat = info.get("lat")
        lon = info.get("lon")
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    except Exception:
        return None
    return None


def build_cache(limit: Optional[int] = None, delay: float = 1.0) -> None:
    env = load_env(ENV_FILE)
    global OPENWEATHER_API_KEY, WAQI_API_TOKEN
    OPENWEATHER_API_KEY = env.get("OPENWEATHER_API_KEY")
    WAQI_API_TOKEN = env.get("WAQI_API_TOKEN")

    db_url = env.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is missing from .env")
    if db_url.startswith("mysql://"):
        db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

    engine = create_engine(db_url, future=True)
    cache = load_cache()

    with engine.connect() as conn:
        cities = [row[0] for row in conn.execute(text("SELECT DISTINCT city FROM cube_city_season ORDER BY city"))]
        print(f"Found {len(cities)} distinct cities")
        if limit is not None:
            cities = cities[:limit]

        country_map = {}
        for row in conn.execute(text("SELECT city, country FROM dim_location")):
            city_name, country_name = row
            if city_name and country_name and city_name not in country_map:
                country_map[city_name] = country_name

        updated = 0
        for idx, city_name in enumerate(cities, start=1):
            key = normalize_city_key(city_name, country_map.get(city_name))
            entry = cache.get(key)
            if entry and entry.get("lat") is not None and entry.get("lon") is not None:
                continue

            print(f"[{idx}/{len(cities)}] Geocoding {city_name} ({key})...")
            coords = None
            if OPENWEATHER_API_KEY:
                coords = geocode_openweather(city_name, country_map.get(city_name))
            if coords is None and WAQI_API_TOKEN:
                coords = geocode_waqi(city_name, country_map.get(city_name))

            if coords is not None:
                cache[key] = {"lat": coords[0], "lon": coords[1], "source": "openweather" if OPENWEATHER_API_KEY else "waqi"}
                updated += 1
                save_cache(cache)
                print(f"  -> {coords}")
            else:
                print("  -> not found")

            time.sleep(delay)

        print(f"Updated {updated} coordinates")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Build city coordinate cache for AQI map')
    parser.add_argument('--limit', type=int, default=None, help='Maximum number of cities to geocode')
    parser.add_argument('--delay', type=float, default=1.0, help='Seconds to wait between requests')
    args = parser.parse_args()
    build_cache(limit=args.limit, delay=args.delay)
