from fastapi import APIRouter, Query

from schemas import ApiResponse, HistoricalAggregation, HistoricalRecord
from repositories.fact_repository import FactRepository
from database.session import get_session

router = APIRouter()

@router.get("/cities")
def list_cities():
    with get_session() as session:
        repository = FactRepository(session)
        cities = repository.list_cities()
        return ApiResponse(success=True, data=cities)

@router.get("/aqi/history", response_model=ApiResponse[list[HistoricalRecord]])
def aqi_history(
    city: str | None = Query(None),
    district: str | None = Query(None),
    year: int | None = Query(None),
    month: int | None = Query(None),
    season: str | None = Query(None),
):
    with get_session() as session:
        repository = FactRepository(session)
        data = repository.get_history(city=city, district=district, year=year, month=month, season=season)
        return ApiResponse(success=True, data=data)

@router.get("/aqi/trend", response_model=ApiResponse[list[HistoricalAggregation]])
def aqi_trend(
    city: str | None = Query(None),
    district: str | None = Query(None),
    year: int | None = Query(None),
    season: str | None = Query(None),
):
    with get_session() as session:
        repository = FactRepository(session)
        data = repository.get_trend(city=city, district=district, year=year, season=season)
        return ApiResponse(success=True, data=data)

@router.get("/aqi/season", response_model=ApiResponse[list[HistoricalAggregation]])
def seasonal_summary(
    city: str | None = Query(None),
    district: str | None = Query(None),
    year: int | None = Query(None),
):
    with get_session() as session:
        repository = FactRepository(session)
        data = repository.get_seasonal_summary(city=city, district=district, year=year)
        return ApiResponse(success=True, data=data)

@router.get("/aqi/monthly", response_model=ApiResponse[list[HistoricalAggregation]])
def monthly_summary(
    city: str | None = Query(None),
    district: str | None = Query(None),
    year: int | None = Query(None),
):
    with get_session() as session:
        repository = FactRepository(session)
        data = repository.get_monthly_summary(city=city, district=district, year=year)
        return ApiResponse(success=True, data=data)

@router.get("/aqi/yearly", response_model=ApiResponse[list[HistoricalAggregation]])
def yearly_summary(
    city: str | None = Query(None),
    district: str | None = Query(None),
    season: str | None = Query(None),
):
    with get_session() as session:
        repository = FactRepository(session)
        data = repository.get_yearly_summary(city=city, district=district, season=season)
        return ApiResponse(success=True, data=data)
