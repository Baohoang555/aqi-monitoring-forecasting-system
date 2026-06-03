import requests
from typing import Dict, Any
from core.config import WAQI_API_TOKEN
from services.aqi_provider.base import BaseAQIProvider

class WaqiProvider(BaseAQIProvider):
    BASE_URL = "https://api.waqi.info/feed"

    def get_city_data(self, city: str) -> Dict[str, Any]:
        if not WAQI_API_TOKEN:
            raise RuntimeError("WAQI_API_TOKEN is not configured")

        url = f"{self.BASE_URL}/{city}/?token={WAQI_API_TOKEN}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch data from WAQI API: {str(e)}")

        if data.get("status") != "ok":
            raise ValueError(f"WAQI API Error: {data.get('data', 'Unknown error')}")

        raw_data = data.get("data", {})
        iaqi = raw_data.get("iaqi", {})
        geo = raw_data.get("city", {}).get("geo", [0.0, 0.0])
        city_name = raw_data.get("city", {}).get("name", city)

        # Map to standard sensor readings
        result = {
            "city_resolved": city_name,
            "co": iaqi.get("co", {}).get("v", None),
            "no2": iaqi.get("no2", {}).get("v", None),
            "o3": iaqi.get("o3", {}).get("v", None),
            "pm1": iaqi.get("pm1", {}).get("v", None), # Often missing in WAQI
            "pm10": iaqi.get("pm10", {}).get("v", None),
            "pm25": iaqi.get("pm25", {}).get("v", None),
            "so2": iaqi.get("so2", {}).get("v", None),
            "um003": None, # Specific sensor, usually missing
            "lat": geo[0] if len(geo) > 0 else None,
            "lon": geo[1] if len(geo) > 1 else None,
            "temp": iaqi.get("t", {}).get("v", None),
            "humidity": iaqi.get("h", {}).get("v", None),
            "wind_speed": iaqi.get("w", {}).get("v", None)
        }
        return result
