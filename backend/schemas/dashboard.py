from typing import Optional
from pydantic import BaseModel

class DashboardOverview(BaseModel):
    total_records: int
    average_aqi: Optional[float]
    worst_city: Optional[str]
    best_city: Optional[str]
    most_frequent_aqi_category: str
    model_metrics: dict
