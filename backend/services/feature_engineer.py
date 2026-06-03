import datetime
import math
from typing import Dict, Any, List
import pandas as pd

def build_features_from_realtime(raw_api_data: Dict[str, Any], feature_cols: List[str]) -> pd.DataFrame:
    """
    Map realtime API data to the exact 157 features expected by the model.
    Missing features are filled with current values (for lags/rolling) or sensible defaults.
    """
    row = {}

    # 1. Base sensors from API
    base_sensors = ["co", "no2", "o3", "pm1", "pm10", "pm25", "so2", "um003", "temp", "humidity", "wind_speed", "lat", "lon"]
    for col in base_sensors:
        # Default missing values to 0 for numerical safety in inference (or rely on pipeline's imputer if any)
        # Using 0 or reasonable mean is safer. If pm25 is missing but it's the dominant pol, we're in trouble.
        val = raw_api_data.get(col)
        row[col] = float(val) if val is not None else 0.0

    # Fallback for pm1 and um003 if not present (which is typical for WAQI)
    if raw_api_data.get("pm1") is None and raw_api_data.get("pm25") is not None:
         row["pm1"] = row["pm25"] * 0.5  # Rough heuristic if needed, or 0
    
    # 2. Outlier and Sensor Error flags (all 0 because realtime data is assumed raw/clean for this inference context)
    for col in feature_cols:
        if col.endswith("_outlier_iqr") or col.endswith("_sensor_error"):
            row[col] = 0.0
            
    # 3. Lag features (since we only have current snapshot, lag = current)
    # Lags: 1h, 3h, 6h, 12h, 24h for pm25, pm10, no2, o3, so2, co, temp, humidity, wind_speed
    for sensor in ["pm25", "pm10", "no2", "o3", "so2", "co", "temp", "humidity", "wind_speed"]:
        for lag in ["1h", "3h", "6h", "12h", "24h"]:
            col_name = f"{sensor}_lag_{lag}"
            if col_name in feature_cols:
                row[col_name] = row[sensor]
                
    # 4. Rolling features (mean, std, max, min for 3h, 6h, 24h)
    for sensor in ["pm25", "pm10", "temp", "humidity", "wind_speed"]:
        for window in ["3h", "6h", "24h"]:
            mean_col = f"{sensor}_roll_mean_{window}"
            std_col = f"{sensor}_roll_std_{window}"
            max_col = f"{sensor}_roll_max_{window}"
            min_col = f"{sensor}_roll_min_{window}"
            
            if mean_col in feature_cols: row[mean_col] = row[sensor]
            if std_col in feature_cols: row[std_col] = 0.0
            if max_col in feature_cols: row[max_col] = row[sensor]
            if min_col in feature_cols: row[min_col] = row[sensor]

    # 5. Threshold flags
    if "rolling_AQI_exceeds_threshold_24h" in feature_cols:
        row["rolling_AQI_exceeds_threshold_24h"] = 0.0

    # 6. Temporal features
    now = datetime.datetime.now()
    if "hour" in feature_cols: row["hour"] = now.hour
    if "dayofweek" in feature_cols: row["dayofweek"] = now.weekday()
    if "month" in feature_cols: row["month"] = now.month
    
    if "hour_sin" in feature_cols: row["hour_sin"] = math.sin(2 * math.pi * now.hour / 24)
    if "hour_cos" in feature_cols: row["hour_cos"] = math.cos(2 * math.pi * now.hour / 24)
    if "dow_sin" in feature_cols: row["dow_sin"] = math.sin(2 * math.pi * now.weekday() / 7)
    if "dow_cos" in feature_cols: row["dow_cos"] = math.cos(2 * math.pi * now.weekday() / 7)
    if "month_sin" in feature_cols: row["month_sin"] = math.sin(2 * math.pi * now.month / 12)
    if "month_cos" in feature_cols: row["month_cos"] = math.cos(2 * math.pi * now.month / 12)
    
    # 7. Categorical / boolean flags
    if "is_rush_hour" in feature_cols:
        row["is_rush_hour"] = 1.0 if (7 <= now.hour <= 9) or (16 <= now.hour <= 19) else 0.0
    if "is_weekend" in feature_cols:
        row["is_weekend"] = 1.0 if now.weekday() >= 5 else 0.0
    if "is_dry_season" in feature_cols:
        # Simplistic assumption for Southeast Asia, can be refined based on location
        row["is_dry_season"] = 1.0 if now.month in [11, 12, 1, 2, 3, 4] else 0.0
        
    # 8. Spatial / Distance features (Default values if we can't compute properly without external DB)
    if "dist_to_nearest_industrial_km" in feature_cols:
        row["dist_to_nearest_industrial_km"] = 15.0 # sensible default
    if "dist_to_nearest_major_road_km" in feature_cols:
        row["dist_to_nearest_major_road_km"] = 5.0 # sensible default

    # Final check: fill any remaining missing columns with 0 to prevent DataFrame missing col errors
    for col in feature_cols:
        if col not in row:
            row[col] = 0.0

    # Ensure exact column order
    df = pd.DataFrame([row])
    df = df[feature_cols]
    return df
