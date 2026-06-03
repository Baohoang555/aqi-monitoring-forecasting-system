from typing import Optional
from pydantic import BaseModel

class WarehouseSummaryResponse(BaseModel):
    total_records: int
    average_aqi: Optional[float]
    max_aqi: Optional[float]
    min_aqi: Optional[float]

class CityWarehouseSummaryResponse(WarehouseSummaryResponse):
    city: str

class PollutantMetric(BaseModel):
    pollutant: str
    average: Optional[float]
    maximum: Optional[float]
    minimum: Optional[float]
