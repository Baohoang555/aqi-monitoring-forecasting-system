from typing import Any
import math
import pandas as pd
from datetime import datetime
from services import model_service
from schemas.prediction import PredictionRequest

FEATURE_COLS = [
    'pm25', 'pm10', 'no', 'no2', 'nox', 'nh3', 'co', 'so2', 'o3',
    'benzene', 'toluene', 'xylene', 'wind_speed', 'humidity',
    'deforestation_rate', 'industry_growth', 'co2_emission', 'population_density',
    'year', 'month', 'quarter', 'day_of_year', 'decade', 'is_covid_period',
    'month_sin', 'month_cos', 'doy_sin', 'doy_cos',
    'pm25_pm10_ratio', 'pm10_minus_pm25', 'no2_nox_ratio', 'benzene_toluene_ratio',
    'so2_no2_ratio', 'pm25_humidity_interaction', 'high_humidity_flag',
    'pm25_wind_dispersion', 'low_wind_flag', 'industry_density_interaction',
    'co2_per_density', 'country_freq', 'city_freq', 'state_freq', 'country_city_freq',
    'pm25_lag_1', 'pm25_lag_3', 'pm25_lag_12',
    'pm10_lag_1', 'pm10_lag_3', 'pm10_lag_12',
    'no2_lag_1', 'no2_lag_3', 'no2_lag_12',
    'o3_lag_1', 'o3_lag_3', 'o3_lag_12',
    'co_lag_1', 'co_lag_3', 'co_lag_12',
    'humidity_lag_1', 'humidity_lag_3', 'humidity_lag_12',
    'wind_speed_lag_1', 'wind_speed_lag_3', 'wind_speed_lag_12',
    'country', 'state', 'city', 'division', 'province', 'region',
    'prefecture', 'federal_district', 'season',
]

class PredictionService:
    @staticmethod
    def build_feature_vector(payload: PredictionRequest) -> pd.DataFrame:
        now = datetime.now()
        month = now.month
        doy = now.timetuple().tm_yday

        pm25 = payload.pm25 or 0.0
        pm10 = payload.pm10 or 0.0
        no2 = payload.no2 or 0.0
        o3 = payload.o3 or 0.0
        humidity = payload.humidity or 70.0
        wind_speed = getattr(payload, "wind_speed", 1.5) or 1.5
        co = getattr(payload, "co", 0.0) or 0.0
        so2 = getattr(payload, "so2", 0.0) or 0.0
        nox = no2  # approximation

        pm25_pm10 = pm25 / pm10 if pm10 > 0 else 0.0
        no2_nox = no2 / nox if nox > 0 else 0.5

        row = {
            'pm25': pm25, 'pm10': pm10, 'no': 0.0, 'no2': no2,
            'nox': nox, 'nh3': 0.0, 'co': co, 'so2': so2, 'o3': o3,
            'benzene': 0.0, 'toluene': 0.0, 'xylene': 0.0,
            'wind_speed': wind_speed, 'humidity': humidity,
            'deforestation_rate': 0.0, 'industry_growth': 0.0,
            'co2_emission': 0.0, 'population_density': 0.0,
            'year': now.year, 'month': month,
            'quarter': (month - 1) // 3 + 1,
            'day_of_year': doy, 'decade': (now.year // 10) * 10,
            'is_covid_period': 0,
            'month_sin': math.sin(2 * math.pi * month / 12),
            'month_cos': math.cos(2 * math.pi * month / 12),
            'doy_sin': math.sin(2 * math.pi * doy / 365),
            'doy_cos': math.cos(2 * math.pi * doy / 365),
            'pm25_pm10_ratio': pm25_pm10,
            'pm10_minus_pm25': pm10 - pm25,
            'no2_nox_ratio': no2_nox,
            'benzene_toluene_ratio': 0.0,
            'so2_no2_ratio': so2 / no2 if no2 > 0 else 0.0,
            'pm25_humidity_interaction': pm25 * humidity,
            'high_humidity_flag': 1 if humidity > 80 else 0,
            'pm25_wind_dispersion': pm25 / wind_speed if wind_speed > 0 else pm25,
            'low_wind_flag': 1 if wind_speed < 1.0 else 0,
            'industry_density_interaction': 0.0,
            'co2_per_density': 0.0,
            'country_freq': 0.0, 'city_freq': 0.0,
            'state_freq': 0.0, 'country_city_freq': 0.0,
            'pm25_lag_1': pm25, 'pm25_lag_3': pm25, 'pm25_lag_12': pm25,
            'pm10_lag_1': pm10, 'pm10_lag_3': pm10, 'pm10_lag_12': pm10,
            'no2_lag_1': no2, 'no2_lag_3': no2, 'no2_lag_12': no2,
            'o3_lag_1': o3, 'o3_lag_3': o3, 'o3_lag_12': o3,
            'co_lag_1': co, 'co_lag_3': co, 'co_lag_12': co,
            'humidity_lag_1': humidity, 'humidity_lag_3': humidity, 'humidity_lag_12': humidity,
            'wind_speed_lag_1': wind_speed, 'wind_speed_lag_3': wind_speed, 'wind_speed_lag_12': wind_speed,
            'country': getattr(payload, 'country', 'Unknown') or 'Unknown',
            'state': getattr(payload, 'state', 'Unknown') or 'Unknown',
            'city': payload.city or 'Unknown',
            'division': 'Unknown', 'province': 'Unknown', 'region': 'Unknown',
            'prefecture': 'Unknown', 'federal_district': 'Unknown',
            'season': 'dry' if month in [11, 12, 1, 2, 3, 4] else 'rainy',
        }

        return pd.DataFrame([row], columns=FEATURE_COLS)

    @staticmethod
    def predict(payload: PredictionRequest) -> dict[str, Any]:
        input_df = PredictionService.build_feature_vector(payload)
        result = model_service.predict(input_df)
        return result