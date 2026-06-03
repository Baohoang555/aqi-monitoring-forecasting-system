import json
import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from core.config import (
    MODEL_PATH,
    LABEL_ENCODER_PATH,
    FEATURE_COLUMNS_PATH,
    MODEL_METRICS_PATH,
    SHAP_SUMMARY_PATH,
)
from services.aqi_provider.waqi import WaqiProvider
from services.feature_engineer import build_features_from_realtime

logger = logging.getLogger(__name__)

_model: Any = None
_label_encoder: Any = None
_feature_cols: list[str] = []
_aqi_provider = WaqiProvider()


def load_artifacts():
    global _model, _label_encoder, _feature_cols

    if not FEATURE_COLUMNS_PATH:
        raise RuntimeError("FEATURE_COLUMNS_PATH is missing from configuration")

    fc_path = Path(FEATURE_COLUMNS_PATH)
    if not fc_path.exists():
        raise RuntimeError(f"feature_columns.json not found at {fc_path}")

    with open(fc_path, "r", encoding="utf-8") as file:
        _feature_cols = json.load(file)
    logger.info(f"Loaded {len(_feature_cols)} feature columns from {fc_path}")

    if not MODEL_PATH:
        raise RuntimeError("MODEL_PATH is missing from configuration")

    try:
        _model = joblib.load(MODEL_PATH)
        logger.info(f"Loaded model from {MODEL_PATH}")
    except Exception as exc:
        logger.error(f"Failed to load model from {MODEL_PATH}: {exc}")
        raise

    if LABEL_ENCODER_PATH:
        try:
            _label_encoder = joblib.load(LABEL_ENCODER_PATH)
            logger.info(f"Loaded label encoder from {LABEL_ENCODER_PATH}")
        except Exception as exc:
            logger.warning(f"Label encoder not loaded (might not be needed if regression): {exc}")


def _is_classification() -> bool:
    return _label_encoder is not None or hasattr(_model, "classes_")


def _map_aqi_category(aqi_value: Any) -> str:
    if isinstance(aqi_value, str):
        return aqi_value

    try:
        aqi_numeric = float(aqi_value)
    except (TypeError, ValueError):
        return "Unknown"

    if aqi_numeric <= 50:
        return "Good"
    if aqi_numeric <= 100:
        return "Moderate"
    if aqi_numeric <= 150:
        return "Unhealthy for Sensitive Groups"
    if aqi_numeric <= 200:
        return "Unhealthy"
    if aqi_numeric <= 300:
        return "Very Unhealthy"
    return "Hazardous"


def build_input_dataframe(values: dict[str, Any]) -> pd.DataFrame:
    if not _feature_cols:
        raise RuntimeError("Feature columns are not loaded")

    payload = {col: float(values.get(col, 0.0)) if values.get(col) is not None else 0.0 for col in _feature_cols}
    return pd.DataFrame([payload], columns=_feature_cols)


def predict(input_df: pd.DataFrame) -> dict[str, Any]:
    if _model is None:
        raise RuntimeError("Model is not loaded. Cannot predict.")

    if input_df.empty:
        raise ValueError("Input dataframe for prediction is empty")

    try:
        raw_pred = _model.predict(input_df)[0]
    except Exception as exc:
        logger.error(f"Prediction failed: {exc}")
        raise RuntimeError(f"Model prediction failed: {exc}")

    if _is_classification() and _label_encoder is not None:
        try:
            label = str(_label_encoder.inverse_transform([raw_pred])[0])
            return {
                "predicted_aqi": label,
                "category": label,
                "model_type": "classification",
                "raw_prediction": raw_pred,
            }
        except Exception as exc:
            logger.warning(f"Label decoding failed: {exc}")

    category = _map_aqi_category(raw_pred)
    return {
        "predicted_aqi": float(raw_pred),
        "category": category,
        "model_type": "regression" if not _is_classification() else "classification",
        "raw_prediction": raw_pred,
    }


def get_model_info() -> dict[str, Any]:
    return {
        "model_loaded": _model is not None,
        "feature_count": len(_feature_cols),
        "model_path": MODEL_PATH,
        "has_label_encoder": _label_encoder is not None,
    }


def get_feature_importance() -> list[dict[str, Any]]:
    if _model is None:
        return []

    importances = []
    if hasattr(_model, "feature_importances_"):
        raw_importances = getattr(_model, "feature_importances_")
        importances = [
            {"feature": col, "importance": float(raw_importances[idx])}
            for idx, col in enumerate(_feature_cols)
        ]
    elif hasattr(_model, "coef_"):
        coefficients = getattr(_model, "coef_")
        flat = coefficients.ravel() if hasattr(coefficients, "ravel") else coefficients
        importances = [
            {"feature": col, "importance": float(flat[idx])}
            for idx, col in enumerate(_feature_cols)
        ]

    return sorted(importances, key=lambda row: abs(row["importance"]), reverse=True)


def get_shap_summary() -> dict[str, Any]:
    if not SHAP_SUMMARY_PATH:
        return {"message": "SHAP summary file not configured"}

    shap_path = Path(SHAP_SUMMARY_PATH)
    if not shap_path.exists():
        return {"message": f"SHAP summary file not found at {shap_path}"}

    try:
        with open(shap_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        logger.warning(f"Unable to load SHAP summary: {exc}")
        return {"message": "Failed to load SHAP summary"}


def get_performance_metrics() -> dict[str, Any]:
    if not MODEL_METRICS_PATH:
        return {"message": "Model metrics file not configured"}

    metrics_path = Path(MODEL_METRICS_PATH)
    if not metrics_path.exists():
        return {"message": f"Model metrics file not found at {metrics_path}"}

    try:
        with open(metrics_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        logger.warning(f"Unable to load performance metrics: {exc}")
        return {"message": "Failed to load performance metrics"}


def predict_from_city(city: str) -> tuple[str, int, str]:
    if _model is None:
        raise RuntimeError("Model is not loaded. Cannot predict.")

    if not _feature_cols:
        raise RuntimeError("Feature columns not loaded.")

    raw_data = _aqi_provider.get_city_data(city)
    city_resolved = raw_data.pop("city_resolved", city)
    input_df = build_features_from_realtime(raw_data, _feature_cols)
    prediction = predict(input_df)
    return prediction["category"], len(_feature_cols), city_resolved
