from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database.models import AqiHistory

class WarehouseRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_summary(self) -> dict:
        stmt = select(
            func.count(AqiHistory.id).label("total_records"),
            func.avg(AqiHistory.aqi).label("average_aqi"),
            func.max(AqiHistory.aqi).label("max_aqi"),
            func.min(AqiHistory.aqi).label("min_aqi"),
        )
        row = self.session.execute(stmt).one()
        return {
            "total_records": int(row.total_records or 0),
            "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
            "max_aqi": float(row.max_aqi) if row.max_aqi is not None else None,
            "min_aqi": float(row.min_aqi) if row.min_aqi is not None else None,
        }

    def get_city_summary(self, city: str) -> dict:
        stmt = select(
            func.count(AqiHistory.id).label("total_records"),
            func.avg(AqiHistory.aqi).label("average_aqi"),
            func.max(AqiHistory.aqi).label("max_aqi"),
            func.min(AqiHistory.aqi).label("min_aqi"),
        ).where(AqiHistory.city.ilike(f"%{city}%"))
        row = self.session.execute(stmt).one()
        return {
            "city": city,
            "total_records": int(row.total_records or 0),
            "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
            "max_aqi": float(row.max_aqi) if row.max_aqi is not None else None,
            "min_aqi": float(row.min_aqi) if row.min_aqi is not None else None,
        }

    def get_pollutant_stats(self) -> list[dict]:
        pollutant_columns = ["pm25", "pm10", "no2", "o3", "co", "so2"]
        metrics = []
        for pollutant in pollutant_columns:
            if not hasattr(AqiHistory, pollutant):
                continue
            stmt = select(
                func.avg(getattr(AqiHistory, pollutant)).label("average"),
                func.max(getattr(AqiHistory, pollutant)).label("maximum"),
                func.min(getattr(AqiHistory, pollutant)).label("minimum"),
            )
            row = self.session.execute(stmt).one()
            metrics.append(
                {
                    "pollutant": pollutant,
                    "average": float(row.average) if row.average is not None else None,
                    "maximum": float(row.maximum) if row.maximum is not None else None,
                    "minimum": float(row.minimum) if row.minimum is not None else None,
                }
            )
        return metrics

    def get_best_worst_city(self) -> dict[str, str | None]:
        stmt = select(
            AqiHistory.city,
            func.avg(AqiHistory.aqi).label("average_aqi"),
            func.count(AqiHistory.id).label("records"),
        ).group_by(AqiHistory.city)
        rows = self.session.execute(stmt).all()
        if not rows:
            return {"best_city": None, "worst_city": None}

        sorted_rows = sorted(rows, key=lambda row: float(row.average_aqi or 0.0))
        return {
            "best_city": sorted_rows[0].city,
            "worst_city": sorted_rows[-1].city,
        }
