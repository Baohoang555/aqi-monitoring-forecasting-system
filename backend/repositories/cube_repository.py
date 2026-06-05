from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

# Import bảng Cube vật hóa đã được Bảo tối ưu bằng BUC
from database.models import CubeCitySeason

class CubeRepository:
    def __init__(self, session: Session):
        self.session = session

    def _apply_filters(self, stmt, city: Optional[str], district: Optional[str], season: Optional[str], hour: Optional[int]):
        """Áp dụng bộ lọc trực tiếp trên các chiều của bảng Iceberg Cube"""
        if city:
            stmt = stmt.where(CubeCitySeason.city.ilike(f"%{city}%"))
        if district:
            stmt = stmt.where(CubeCitySeason.district.ilike(f"%{district}%"))
        if season:
            stmt = stmt.where(CubeCitySeason.season.ilike(f"%{season}%"))
        if hour is not None:
            stmt = stmt.where(CubeCitySeason.hour == hour)
        return stmt

    def slice(self, city: Optional[str] = None, season: Optional[str] = None) -> list[dict]:
        """OLAP Slice: Cắt lát dữ liệu (ví dụ: Xem toàn bộ dữ liệu thuộc về riêng 'Mùa khô')"""
        stmt = select(
            CubeCitySeason.city,
            CubeCitySeason.district,
            CubeCitySeason.hour,
            CubeCitySeason.season,
            CubeCitySeason.avg_aqi,
            CubeCitySeason.reading_count.label("records")
        )
        stmt = self._apply_filters(stmt, city, None, season, None)
        rows = self.session.execute(stmt).all()
        return [
            {
                "city": row.city,
                "district": row.district,
                "hour": row.hour,
                "season": row.season,
                "average_aqi": row.avg_aqi,
                "records": row.records,
            }
            for row in rows
        ]

    def dice(self, city: Optional[str] = None, district: Optional[str] = None, season: Optional[str] = None, hour: Optional[int] = None) -> list[dict]:
        """OLAP Dice: Lọc đồng thời trên nhiều chiều để tạo khối con (Sub-cube)"""
        stmt = select(
            CubeCitySeason.city,
            CubeCitySeason.district,
            CubeCitySeason.hour,
            CubeCitySeason.season,
            CubeCitySeason.avg_aqi,
            CubeCitySeason.reading_count.label("records")
        )
        stmt = self._apply_filters(stmt, city, district, season, hour)
        rows = self.session.execute(stmt).all()
        return [
            {
                "city": row.city,
                "district": row.district,
                "hour": row.hour,
                "season": row.season,
                "average_aqi": row.avg_aqi,
                "records": row.records,
            }
            for row in rows
        ]

    def drilldown(self, dimensions: list[str], city: Optional[str] = None, season: Optional[str] = None) -> list[dict]:
        """OLAP Drill-down: Khoan sâu dữ liệu từ mức tổng quan xuống mức chi tiết hơn 
        (Dựa trên các chiều có sẵn trong Cube vật hóa: city -> district -> hour)"""
        return self.rollup(dimensions, city, season)

    def rollup(self, dimensions: list[str], city: Optional[str] = None, season: Optional[str] = None) -> list[dict]:
        """OLAP Roll-up: Thu nhỏ dữ liệu, gộp các chiều chi tiết thành chiều tổng quan hơn"""
        if not dimensions:
            return []
            
        # Lấy danh sách các cột hợp lệ từ bảng Cube vật hóa
        columns = [getattr(CubeCitySeason, dim) for dim in dimensions if hasattr(CubeCitySeason, dim)]
        if not columns:
            return []
            
        # Tính toán lại hàm gom cụm (Aggregate) dựa trên dữ liệu đã được tổng hợp sơ bộ của Cube
        # Tránh được việc phải quét lại bảng Fact gốc 10.7 triệu dòng
        stmt = select(
            *columns, 
            func.avg(CubeCitySeason.avg_aqi).label("average_aqi"), 
            func.sum(CubeCitySeason.reading_count).label("records")
        )
        stmt = stmt.group_by(*columns).order_by(*columns)
        stmt = self._apply_filters(stmt, city, None, season, None)
        
        rows = self.session.execute(stmt).all()
        results = []
        for row in rows:
            entry = {dim: getattr(row, dim) for dim in dimensions if hasattr(CubeCitySeason, dim)}
            entry.update({
                "average_aqi": float(row.average_aqi) if row.average_aqi is not None else None, 
                "records": int(row.records) if row.records is not None else 0
            })
            results.append(entry)
        return results