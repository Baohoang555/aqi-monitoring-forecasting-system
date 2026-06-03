from typing import List
from fastapi import APIRouter, Query, HTTPException

from schemas import ApiResponse, OlapQuery, OlapRecord
from services import CubeService

router = APIRouter()

@router.get("/olap/slice", response_model=ApiResponse[list[OlapRecord]])
def olap_slice(
    city: str | None = Query(None),
    season: str | None = Query(None),
    year: int | None = Query(None),
):
    data = CubeService.slice_cube(city=city, season=season, year=year)
    return ApiResponse(success=True, data=data)

@router.get("/olap/dice", response_model=ApiResponse[list[OlapRecord]])
def olap_dice(
    city: str | None = Query(None),
    district: str | None = Query(None),
    season: str | None = Query(None),
    year: int | None = Query(None),
):
    data = CubeService.dice_cube(city=city, district=district, year=year, season=season)
    return ApiResponse(success=True, data=data)

@router.get("/olap/drilldown", response_model=ApiResponse[list[OlapRecord]])
def olap_drilldown(
    dimensions: List[str] = Query(..., description="Dimensions to drill down by"),
    city: str | None = Query(None),
    year: int | None = Query(None),
    season: str | None = Query(None),
):
    if not dimensions:
        raise HTTPException(status_code=400, detail="At least one dimension is required for drilldown")
    data = CubeService.drilldown(dimensions=dimensions, city=city, year=year, season=season)
    return ApiResponse(success=True, data=data)

@router.get("/olap/rollup", response_model=ApiResponse[list[OlapRecord]])
def olap_rollup(
    dimensions: List[str] = Query(..., description="Dimensions to roll up by"),
    city: str | None = Query(None),
    year: int | None = Query(None),
    season: str | None = Query(None),
):
    if not dimensions:
        raise HTTPException(status_code=400, detail="At least one dimension is required for rollup")
    data = CubeService.rollup(dimensions=dimensions, city=city, year=year, season=season)
    return ApiResponse(success=True, data=data)
