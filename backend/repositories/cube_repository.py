from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from database.models import CubeCitySeason, FactAqiReading, DimTime, DimLocation, DimPollutant
from database.models import CubeCitySeason

class CubeRepository:
    def __init__(self, session: Session):
        self.session = session

    def _apply_filters(self, stmt, city: Optional[str], season: Optional[str]):
        if city:
            stmt = stmt.where(CubeCitySeason.city.ilike(f"%{city}%"))
        if season:
            stmt = stmt.where(CubeCitySeason.season.ilike(f"%{season}%"))
        return stmt

    def slice(self, city: Optional[str] = None, season: Optional[str] = None, year: Optional[int] = None) -> list[dict]:
        stmt = select(
            CubeCitySeason.city,
            CubeCitySeason.country,
            CubeCitySeason.season,
            CubeCitySeason.pollutant_code,
            CubeCitySeason.avg_aqi,
            CubeCitySeason.max_aqi,
            CubeCitySeason.avg_conc,
            CubeCitySeason.unhealthy_cnt,
            CubeCitySeason.reading_count.label("records")
        )
        stmt = self._apply_filters(stmt, city, season)
        rows = self.session.execute(stmt).all()
        return [
            {
                "city": row.city,
                "district": None,
                "hour": None,
                "season": row.season,
                "average_aqi": float(row.avg_aqi) if row.avg_aqi is not None else None,
                "records": row.records,
                "year": None,
                "month": None,
                "country": row.country,
                "pollutant_code": row.pollutant_code,
                "max_aqi": row.max_aqi,
                "avg_conc": float(row.avg_conc) if row.avg_conc is not None else None,
                "unhealthy_cnt": row.unhealthy_cnt,
            }
            for row in rows
        ]

    def dice(self, city: Optional[str] = None, district: Optional[str] = None, season: Optional[str] = None, hour: Optional[int] = None, year: Optional[int] = None) -> list[dict]:
        stmt = select(
            CubeCitySeason.city,
            CubeCitySeason.country,
            CubeCitySeason.season,
            CubeCitySeason.pollutant_code,
            CubeCitySeason.avg_aqi,
            CubeCitySeason.max_aqi,
            CubeCitySeason.avg_conc,
            CubeCitySeason.unhealthy_cnt,
            CubeCitySeason.reading_count.label("records")
        )
        stmt = self._apply_filters(stmt, city, season)
        rows = self.session.execute(stmt).all()
        return [
            {
                "city": row.city,
                "district": None,
                "hour": None,
                "season": row.season,
                "average_aqi": float(row.avg_aqi) if row.avg_aqi is not None else None,
                "records": row.records,
                "year": None,
                "month": None,
                "country": row.country,
                "pollutant_code": row.pollutant_code,
                "max_aqi": row.max_aqi,
                "avg_conc": float(row.avg_conc) if row.avg_conc is not None else None,
                "unhealthy_cnt": row.unhealthy_cnt,
            }
            for row in rows
        ]

    def drilldown(self, dimensions: list[str], city: Optional[str] = None, season: Optional[str] = None) -> list[dict]:
        return self.rollup(dimensions, city, season)

    def rollup(self, dimensions: list[str], city: Optional[str] = None, season: Optional[str] = None) -> list[dict]:
        if not dimensions:
            return []

        valid_dims = [d for d in dimensions if hasattr(CubeCitySeason, d)]
        if not valid_dims:
            return []

        columns = [getattr(CubeCitySeason, dim) for dim in valid_dims]
        stmt = select(
            *columns,
            func.avg(CubeCitySeason.avg_aqi).label("average_aqi"),
            func.sum(CubeCitySeason.reading_count).label("records")
        )
        stmt = stmt.group_by(*columns).order_by(*columns)
        stmt = self._apply_filters(stmt, city, season)

        rows = self.session.execute(stmt).all()
        results = []
        for row in rows:
            entry = {dim: getattr(row, dim) for dim in valid_dims}
            entry.update({
                "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
                "records": int(row.records) if row.records is not None else 0,
                "year": None,
                "month": None,
                "district": None,
                "hour": None,
            })
            results.append(entry)
        return results
    
    def slice_by_year(self, city: Optional[str] = None, season: Optional[str] = None) -> list[dict]:
        stmt = (
            select(
                DimLocation.city,
                DimLocation.country,
                DimTime.year,
                DimTime.month,
                DimTime.season,
                DimPollutant.pollutant_code,
                func.avg(FactAqiReading.aqi_value).label("average_aqi"),
                func.max(FactAqiReading.aqi_value).label("max_aqi"),
                func.avg(FactAqiReading.concentration).label("avg_conc"),
                func.count().label("records"),
            )
            .join(DimTime, FactAqiReading.time_key == DimTime.time_key)
            .join(DimLocation, FactAqiReading.location_key == DimLocation.location_key)
            .join(DimPollutant, FactAqiReading.pollutant_key == DimPollutant.pollutant_key)
            .group_by(DimLocation.city, DimLocation.country, DimTime.year, DimTime.season, DimPollutant.pollutant_code, DimTime.month)
            .order_by(DimLocation.city, DimTime.year, DimTime.month)
        )
        if city:
            stmt = stmt.where(DimLocation.city.ilike(f"%{city}%"))
        if season:
            stmt = stmt.where(DimTime.season.ilike(f"%{season}%"))

        rows = self.session.execute(stmt).all()
        return [
            {
                "city": row.city,
                "country": row.country,
                "year": row.year,
                "season": row.season,
                "pollutant_code": row.pollutant_code,
                "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
                "max_aqi": float(row.max_aqi) if row.max_aqi is not None else None,
                "avg_conc": float(row.avg_conc) if row.avg_conc is not None else None,
                "records": int(row.records) if row.records is not None else 0,
                "district": None,
                "month": None,
                "hour": None,
                "unhealthy_cnt": None,
            }
            for row in rows
        ]