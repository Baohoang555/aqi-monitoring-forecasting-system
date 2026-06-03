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
    city: Optional[str]
    district: Optional[str]
    year: Optional[int]
    season: Optional[str]
    month: Optional[int]
    average_aqi: Optional[float]
    records: int
