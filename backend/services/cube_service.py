from typing import List, Optional

from repositories.cube_repository import CubeRepository
from database.session import get_session

class CubeService:
    @staticmethod
    def slice_cube(city: Optional[str] = None, season: Optional[str] = None, year: Optional[int] = None) -> list[dict]:
        with get_session() as session:
            repository = CubeRepository(session)
            return repository.slice(city=city, season=season, year=year)

    @staticmethod
    def dice_cube(city: Optional[str] = None, district: Optional[str] = None, year: Optional[int] = None, season: Optional[str] = None) -> list[dict]:
        with get_session() as session:
            repository = CubeRepository(session)
            return repository.dice(city=city, district=district, year=year, season=season)

    @staticmethod
    def drilldown(dimensions: List[str], city: Optional[str] = None, year: Optional[int] = None, season: Optional[str] = None) -> list[dict]:
        with get_session() as session:
            repository = CubeRepository(session)
            return repository.drilldown(dimensions=dimensions, city=city, year=year, season=season)

    @staticmethod
    def rollup(dimensions: List[str], city: Optional[str] = None, year: Optional[int] = None, season: Optional[str] = None) -> list[dict]:
        with get_session() as session:
            repository = CubeRepository(session)
            return repository.rollup(dimensions=dimensions, city=city, year=year, season=season)
    
    @staticmethod
    def slice_by_year(city: Optional[str] = None, season: Optional[str] = None) -> list[dict]:
        with get_session() as session:
            repository = CubeRepository(session)
            return repository.slice_by_year(city=city, season=season)
