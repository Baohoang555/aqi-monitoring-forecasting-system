from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class PredictRequest(BaseModel):
    city: str = Field(..., description="Name of the city or location to predict AQI for")

class PredictionDetails(BaseModel):
    aqi_label: str
    features_used: int
    data_source: str
    city_resolved: str

class PredictResponse(BaseModel):
    success: bool
    data: Optional[PredictionDetails] = None
    error: Optional[str] = None
    cached: bool = False

class CurrentAQIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
