from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

# Import đầy đủ kiến trúc Star Schema & Khối Cube vật hóa của Bảo
from database.models import FactAqiReading, DimLocation, DimPollutant, CubeCitySeason

class WarehouseRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_summary(self) -> dict:
        """Tính toán tổng hợp chỉ số AQI trên toàn bộ kho dữ liệu (Fact Table)"""
        stmt = select(
            func.count().label("total_records"),  # Đếm tổng số dòng (Tương đương COUNT(*))
            func.avg(FactAqiReading.aqi_value).label("average_aqi"),
            func.max(FactAqiReading.aqi_value).label("max_aqi"),
            func.min(FactAqiReading.aqi_value).label("min_aqi"),
        )
        row = self.session.execute(stmt).one()
        return {
            "total_records": int(row.total_records or 0),
            "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
            "max_aqi": float(row.max_aqi) if row.max_aqi is not None else None,
            "min_aqi": float(row.min_aqi) if row.min_aqi is not None else None,
        }

    def get_city_summary(self, city: str) -> dict:
        """Lấy số liệu thống kê AQI của một thành phố cụ thể bằng cách JOIN với DimLocation"""
        stmt = (
            select(
                func.count(DimLocation.location_key).label("total_records"),  # Đếm theo khóa của bảng chiều Location cho chuẩn
                func.avg(FactAqiReading.aqi_value).label("average_aqi"),
                func.max(FactAqiReading.aqi_value).label("max_aqi"),
                func.min(FactAqiReading.aqi_value).label("min_aqi"),
            )
            .join(FactAqiReading.location_rel)
            .where(DimLocation.city.ilike(f"%{city}%"))
        )
        row = self.session.execute(stmt).one()
        return {
            "city": city,
            "total_records": int(row.total_records or 0),
            "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None,
            "max_aqi": float(row.max_aqi) if row.max_aqi is not None else None,
            "min_aqi": float(row.min_aqi) if row.min_aqi is not None else None,
        }

    def get_pollutant_stats(self) -> list[dict]:
        """
        Thay vì quét các cột dạng Wide, hệ thống Star Schema lưu dạng Long.
        Hàm này sẽ gom cụm theo từng loại chất ô nhiễm trong bảng DimPollutant.
        """
        stmt = (
            select(
                DimPollutant.pollutant_code.label("pollutant"),
                func.avg(FactAqiReading.concentration).label("average"),
                func.max(FactAqiReading.concentration).label("maximum"),
                func.min(FactAqiReading.concentration).label("minimum"),
            )
            .join(FactAqiReading.pollutant_rel)
            .group_by(DimPollutant.pollutant_code)
        )
        rows = self.session.execute(stmt).all()
        return [
            {
                "pollutant": row.pollutant.lower(),  # Giữ nguyên chữ thường để khớp với frontend cũ
                "average": float(row.average) if row.average is not None else None,
                "maximum": float(row.maximum) if row.maximum is not None else None,
                "minimum": float(row.minimum) if row.minimum is not None else None,
            }
            for row in rows
        ]

    def get_best_worst_city_fast(self) -> dict[str, str | None]:
        """Tối ưu tốc độ load Dashboard bằng cách quét trên Iceberg Cube vật hóa của Bảo"""
        stmt = (
            select(
                CubeCitySeason.city,
                func.avg(CubeCitySeason.avg_aqi).label("average_aqi"),
            )
            .group_by(CubeCitySeason.city)
        )
        rows = self.session.execute(stmt).all()
        if not rows:
            return {"best_city": None, "worst_city": None}
            
        # Sắp xếp danh sách dựa trên AQI trung bình tăng dần để tìm Best/Worst
        sorted_rows = sorted(rows, key=lambda row: float(row.average_aqi or 0.0))
        return {
            "best_city": sorted_rows[0].city,
            "worst_city": sorted_rows[-1].city,
        }

    def get_most_frequent_category_fast(self) -> str:
        """Tối ưu bằng cách đếm nhóm (GROUP BY) trực tiếp dưới DB sử dụng func.count() chuẩn (ĐÃ BỔ SUNG)"""
        stmt = (
            select(
                FactAqiReading.aqi_category,
                func.count().label("cnt")
            )
            .group_by(FactAqiReading.aqi_category)
            .order_by(func.count().desc())
            .limit(1)
        )
        row = self.session.execute(stmt).first()
        return row.aqi_category if row else "N/A"