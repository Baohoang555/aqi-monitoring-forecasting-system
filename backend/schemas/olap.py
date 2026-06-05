from typing import List, Optional
from pydantic import BaseModel, Field

class OlapQuery(BaseModel):
    city: Optional[str] = Field(None, description="City filter for OLAP queries")
    district: Optional[str] = Field(None, description="District filter for OLAP queries")
    year: Optional[int] = Field(None, description="Year filter")
    season: Optional[str] = Field(None, description="Season filter")
    month: Optional[int] = Field(None, description="Month filter")
    dimensions: Optional[List[str]] = Field(None, description="Dimensions to drilldown or rollup")

class OlapRecord(BaseModel):
    city: Optional[str] = None
    district: Optional[str] = None
    year: Optional[int] = None
    season: Optional[str] = None
    month: Optional[int] = None
    hour: Optional[int] = None
    average_aqi: Optional[float] = None
    records: Optional[int] = None
    # Thêm các field này:
    country: Optional[str] = None
    pollutant_code: Optional[str] = None
    max_aqi: Optional[float] = None
    avg_conc: Optional[float] = None
    unhealthy_cnt: Optional[int] = None
