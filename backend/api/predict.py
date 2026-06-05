import time
import logging
from fastapi import APIRouter, HTTPException
from schemas import PredictionRequest, PredictionResponse, PredictionDetails
from services import cache_service, monitoring_service
from services.prediction_service import PredictionService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest):
    monitoring_service.record_request("predict")
    start = time.time()

    if not payload.features and not any(
        [payload.pm25, payload.pm10, payload.no2, payload.o3, payload.temperature, payload.humidity]
    ):
        raise HTTPException(status_code=400, detail="At least one predictive feature must be provided")

    cache_key = {
        "city": payload.city or "",
        "pm25": payload.pm25,
        "pm10": payload.pm10,
        "no2": payload.no2,
        "o3": payload.o3,
        "temperature": payload.temperature,
        "humidity": payload.humidity,
        "features": payload.features,
    }
    cached = cache_service.get("predict", cache_key)
    if cached is not None:
        monitoring_service.record_cache_hit("predict")
        monitoring_service.record_latency("predict", time.time() - start)
        return PredictionResponse(success=True, data=PredictionDetails(**cached), cached=True)

    monitoring_service.record_cache_miss("predict")

    try:
        prediction = PredictionService.predict(payload)
    except ValueError as e:
        logger.warning(f"Prediction request error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    raw = prediction.get("predicted_aqi")

    if isinstance(raw, str):
        predicted_aqi_num = None
        category = prediction.get("category") or raw
    else:
        predicted_aqi_num = float(raw) if raw is not None else None
        category = prediction.get("category") or ""

    input_features = payload.features or {
        k: v for k, v in {
            "pm25": payload.pm25,
            "pm10": payload.pm10,
            "no2": payload.no2,
            "o3": payload.o3,
            "temperature": payload.temperature,
            "humidity": payload.humidity,
        }.items() if v is not None
    }

    details = PredictionDetails(
        predicted_aqi=predicted_aqi_num,
        category=category,
        model_type=prediction.get("model_type", "unknown"),
        input_features=input_features,
    )

    cache_service.set("predict", cache_key, details.model_dump(), ttl=cache_service.PREDICT_TTL)
    monitoring_service.record_latency("predict", time.time() - start)

    return PredictionResponse(success=True, data=details, cached=False)
