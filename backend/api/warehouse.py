from fastapi import APIRouter, HTTPException

from services import WarehouseService
from schemas import ApiResponse, WarehouseSummaryResponse, CityWarehouseSummaryResponse, PollutantMetric

router = APIRouter()

@router.get("/warehouse/summary", response_model=ApiResponse[WarehouseSummaryResponse])
def warehouse_summary():
    summary = WarehouseService.get_summary()
    return ApiResponse(success=True, data=summary)

@router.get("/warehouse/city/{city}", response_model=ApiResponse[CityWarehouseSummaryResponse])
def warehouse_city(city: str):
    if not city.strip():
        raise HTTPException(status_code=400, detail="City name cannot be empty")
    summary = WarehouseService.get_city_summary(city)
    return ApiResponse(success=True, data=summary)

@router.get("/warehouse/pollutants", response_model=ApiResponse[list[PollutantMetric]])
def warehouse_pollutants():
    metrics = WarehouseService.get_pollutant_stats()
    return ApiResponse(success=True, data=metrics)
