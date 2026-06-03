from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database.models import AqiHistory

class CubeRepository:
    def __init__(self, session: Session):
        self.session = session

    def _apply_filters(self, stmt, city: Optional[str], district: Optional[str], year: Optional[int], season: Optional[str], month: Optional[int]):
        if city:
            stmt = stmt.where(AqiHistory.city.ilike(f"%{city}%"))
        if district:
            stmt = stmt.where(AqiHistory.district.ilike(f"%{district}%"))
        if year:
            stmt = stmt.where(AqiHistory.year == year)
        if season:
            stmt = stmt.where(AqiHistory.season.ilike(f"%{season}%"))
        if month:
            stmt = stmt.where(AqiHistory.month == month)
        return stmt

    def slice(self, city: Optional[str] = None, season: Optional[str] = None, year: Optional[int] = None) -> list[dict]:
        stmt = select(
            AqiHistory.city,
            AqiHistory.year,
            AqiHistory.season,
            AqiHistory.month,
            func.avg(AqiHistory.aqi).label("average_aqi"),
            func.count(AqiHistory.id).label("records"),
        ).group_by(AqiHistory.city, AqiHistory.year, AqiHistory.season, AqiHistory.month)
        stmt = self._apply_filters(stmt, city, None, year, season, None)
        rows = self.session.execute(stmt).all()
        return [
            {
                "city": row.city,
                "year": row.year,
                "season": row.season,
                "month": row.month,
                "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
                "records": row.records,
            }
            for row in rows
        ]

    def dice(self, city: Optional[str] = None, year: Optional[int] = None, season: Optional[str] = None, district: Optional[str] = None) -> list[dict]:
        stmt = select(
            AqiHistory.city,
            AqiHistory.district,
            AqiHistory.year,
            AqiHistory.season,
            func.avg(AqiHistory.aqi).label("average_aqi"),
            func.count(AqiHistory.id).label("records"),
        ).group_by(AqiHistory.city, AqiHistory.district, AqiHistory.year, AqiHistory.season)
        stmt = self._apply_filters(stmt, city, district, year, season, None)
        rows = self.session.execute(stmt).all()
        return [
            {
                "city": row.city,
                "district": row.district,
                "year": row.year,
                "season": row.season,
                "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
                "records": row.records,
            }
            for row in rows
        ]

    def drilldown(self, dimensions: list[str], city: Optional[str] = None, year: Optional[int] = None, season: Optional[str] = None) -> list[dict]:
        valid_dimensions = []
        columns = []
        for dim in dimensions:
            if hasattr(AqiHistory, dim):
                valid_dimensions.append(dim)
                columns.append(getattr(AqiHistory, dim))
        if not valid_dimensions:
            return []
        stmt = select(*columns, func.avg(AqiHistory.aqi).label("average_aqi"), func.count(AqiHistory.id).label("records"))
        stmt = stmt.group_by(*columns).order_by(*columns)
        stmt = self._apply_filters(stmt, city, None, year, season, None)
        rows = self.session.execute(stmt).all()
        results = []
        for row in rows:
            entry = {dim: getattr(row, dim) for dim in valid_dimensions}
            entry.update({"average_aqi": float(row.average_aqi) if row.average_aqi is not None else None, "records": row.records})
            results.append(entry)
        return results

    def rollup(self, dimensions: list[str], city: Optional[str] = None, year: Optional[int] = None, season: Optional[str] = None) -> list[dict]:
        if not dimensions:
            return []
        columns = [getattr(AqiHistory, dim) for dim in dimensions if hasattr(AqiHistory, dim)]
        if not columns:
            return []
        stmt = select(*columns, func.avg(AqiHistory.aqi).label("average_aqi"), func.count(AqiHistory.id).label("records"))
        stmt = stmt.group_by(*columns).order_by(*columns)
        stmt = self._apply_filters(stmt, city, None, year, season, None)
        rows = self.session.execute(stmt).all()
        results = []
        for row in rows:
            entry = {dim: getattr(row, dim) for dim in dimensions if hasattr(AqiHistory, dim)}
            entry.update({"average_aqi": float(row.average_aqi) if row.average_aqi is not None else None, "records": row.records})
            results.append(entry)
        return results
