from typing import Dict, Optional
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    city: Optional[str] = Field(None, description="Optional city in the payload")
    pm25: Optional[float] = Field(None, description="PM2.5 concentration")
    pm10: Optional[float] = Field(None, description="PM10 concentration")
    no2: Optional[float] = Field(None, description="NO2 concentration")
    o3: Optional[float] = Field(None, description="O3 concentration")
    temperature: Optional[float] = Field(None, description="Ambient temperature")
    humidity: Optional[float] = Field(None, description="Relative humidity")
    features: Optional[Dict[str, float]] = Field(None, description="Optional full feature vector for model inference")

class PredictionDetails(BaseModel):
    predicted_aqi: Optional[float]
    category: str
    model_type: str
    input_features: Dict[str, float]

class PredictionResponse(BaseModel):
    success: bool
    data: Optional[PredictionDetails] = None
    error: Optional[str] = None
    cached: bool = False
