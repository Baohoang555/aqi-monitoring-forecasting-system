from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database.models import AqiHistory

class FactRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_cities(self) -> list[str]:
        stmt = select(AqiHistory.city).distinct().order_by(AqiHistory.city)
        return [city for city, in self.session.execute(stmt).all()]

    def _apply_filters(self, stmt, city: Optional[str], district: Optional[str], year: Optional[int], month: Optional[int], season: Optional[str]):
        if city:
            stmt = stmt.where(AqiHistory.city.ilike(f"%{city}%"))
        if district:
            stmt = stmt.where(AqiHistory.district.ilike(f"%{district}%"))
        if year:
            stmt = stmt.where(AqiHistory.year == year)
        if month:
            stmt = stmt.where(AqiHistory.month == month)
        if season:
            stmt = stmt.where(AqiHistory.season.ilike(f"%{season}%"))
        return stmt

    def get_history(self, city: Optional[str] = None, district: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None, season: Optional[str] = None) -> list[dict]:
        stmt = select(
            AqiHistory.recorded_at,
            AqiHistory.aqi,
            AqiHistory.category,
            AqiHistory.city,
            AqiHistory.district,
            AqiHistory.year,
            AqiHistory.month,
            AqiHistory.season,
        ).order_by(AqiHistory.recorded_at)
        stmt = self._apply_filters(stmt, city, district, year, month, season)
        rows = self.session.execute(stmt).all()
        return [
            {
                "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
                "aqi": row.aqi,
                "category": row.category,
                "city": row.city,
                "district": row.district,
                "year": row.year,
                "month": row.month,
                "season": row.season,
            }
            for row in rows
        ]

    def get_trend(self, city: Optional[str] = None, district: Optional[str] = None, year: Optional[int] = None, season: Optional[str] = None) -> list[dict]:
        stmt = select(
            AqiHistory.year,
            AqiHistory.month,
            func.avg(AqiHistory.aqi).label("average_aqi"),
            func.count(AqiHistory.id).label("records"),
        ).group_by(AqiHistory.year, AqiHistory.month).order_by(AqiHistory.year, AqiHistory.month)
        stmt = self._apply_filters(stmt, city, district, year, None, season)
        rows = self.session.execute(stmt).all()
        return [
            {
                "year": row.year,
                "month": row.month,
                "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
                "records": row.records,
            }
            for row in rows
        ]

    def get_seasonal_summary(self, city: Optional[str] = None, district: Optional[str] = None, year: Optional[int] = None) -> list[dict]:
        stmt = select(
            AqiHistory.season,
            func.avg(AqiHistory.aqi).label("average_aqi"),
            func.max(AqiHistory.aqi).label("max_aqi"),
            func.min(AqiHistory.aqi).label("min_aqi"),
            func.count(AqiHistory.id).label("records"),
        ).group_by(AqiHistory.season).order_by(AqiHistory.season)
        stmt = self._apply_filters(stmt, city, district, year, None, None)
        rows = self.session.execute(stmt).all()
        return [
            {
                "season": row.season,
                "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
                "max_aqi": float(row.max_aqi) if row.max_aqi is not None else None,
                "min_aqi": float(row.min_aqi) if row.min_aqi is not None else None,
                "records": row.records,
            }
            for row in rows
        ]

    def get_monthly_summary(self, city: Optional[str] = None, district: Optional[str] = None, year: Optional[int] = None) -> list[dict]:
        stmt = select(
            AqiHistory.year,
            AqiHistory.month,
            func.avg(AqiHistory.aqi).label("average_aqi"),
            func.max(AqiHistory.aqi).label("max_aqi"),
            func.min(AqiHistory.aqi).label("min_aqi"),
            func.count(AqiHistory.id).label("records"),
        ).group_by(AqiHistory.year, AqiHistory.month).order_by(AqiHistory.year, AqiHistory.month)
        stmt = self._apply_filters(stmt, city, district, year, None, None)
        rows = self.session.execute(stmt).all()
        return [
            {
                "year": row.year,
                "month": row.month,
                "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
                "max_aqi": float(row.max_aqi) if row.max_aqi is not None else None,
                "min_aqi": float(row.min_aqi) if row.min_aqi is not None else None,
                "records": row.records,
            }
            for row in rows
        ]

    def get_yearly_summary(self, city: Optional[str] = None, district: Optional[str] = None, season: Optional[str] = None) -> list[dict]:
        stmt = select(
            AqiHistory.year,
            func.avg(AqiHistory.aqi).label("average_aqi"),
            func.max(AqiHistory.aqi).label("max_aqi"),
            func.min(AqiHistory.aqi).label("min_aqi"),
            func.count(AqiHistory.id).label("records"),
        ).group_by(AqiHistory.year).order_by(AqiHistory.year)
        stmt = self._apply_filters(stmt, None, None, None, None, season)
        if city:
            stmt = stmt.where(AqiHistory.city.ilike(f"%{city}%"))
        if district:
            stmt = stmt.where(AqiHistory.district.ilike(f"%{district}%"))
        rows = self.session.execute(stmt).all()
        return [
            {
                "year": row.year,
                "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
                "max_aqi": float(row.max_aqi) if row.max_aqi is not None else None,
                "min_aqi": float(row.min_aqi) if row.min_aqi is not None else None,
                "records": row.records,
            }
            for row in rows
        ]
