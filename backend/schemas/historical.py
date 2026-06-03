from typing import Optional
from pydantic import BaseModel, Field

class HistoricalQuery(BaseModel):
    city: Optional[str] = Field(None, description="City filter for historical AQI")
    district: Optional[str] = Field(None, description="District filter for historical AQI")
    year: Optional[int] = Field(None, description="Year filter")
    month: Optional[int] = Field(None, description="Month filter")
    season: Optional[str] = Field(None, description="Season filter")

class HistoricalRecord(BaseModel):
    recorded_at: Optional[str]
    aqi: Optional[float]
    category: Optional[str]
    city: Optional[str]
    district: Optional[str]
    year: Optional[int]
    month: Optional[int]
    season: Optional[str]

class HistoricalAggregation(BaseModel):
    year: Optional[int]
    month: Optional[int]
    season: Optional[str]
    average_aqi: Optional[float]
    max_aqi: Optional[float]
    min_aqi: Optional[float]
    records: int
