from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

# Import cấu trúc Star Schema mới của Bảo
from database.models import FactAqiReading, DimLocation, DimTime, CubeCitySeason

class FactRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_cities(self) -> list[str]:
        # Trả về danh sách thành phố hiện có dữ liệu trong khối cube,
        # để frontend chỉ vẽ những trạm thực sự có dữ liệu current.
        stmt = select(CubeCitySeason.city).distinct().order_by(CubeCitySeason.city)
        return [city for city, in self.session.execute(stmt).all()]

    def _apply_filters(self, stmt, city: Optional[str], district: Optional[str], year: Optional[int], month: Optional[int], season: Optional[str]):
        # Tự động thực hiện JOIN với các bảng chiều nếu bộ lọc yêu cầu điều kiện từ bảng đó
        # Sử dụng kiểm tra 'contains_eager' hoặc join thông thường dựa trên quan hệ SQLAlchemy
        if city or district:
            stmt = stmt.join(FactAqiReading.location_rel)
            if city:
                stmt = stmt.where(DimLocation.city.ilike(f"%{city}%"))
            # Lưu ý: Nếu trong DimLocation của Bảo chưa tách cột district, có thể filter tạm theo city hoặc cập nhật sau
            if district:
                stmt = stmt.where(DimLocation.city.ilike(f"%{district}%")) 

        if year or month or season:
            stmt = stmt.join(FactAqiReading.time_rel)
            if year:
                stmt = stmt.where(DimTime.year == year)
            if month:
                stmt = stmt.where(DimTime.month == month)
            if season:
                stmt = stmt.where(DimTime.season.ilike(f"%{season}%"))
        return stmt

    def get_history(self, city: Optional[str] = None, district: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None, season: Optional[str] = None) -> list[dict]:
        # Truy vấn kết hợp các thuộc tính từ bảng Fact và dữ liệu ngữ cảnh từ bảng Dim
        stmt = select(
            FactAqiReading.loaded_at.label("recorded_at"), # Map tạm thời với loaded_at hoặc cột mốc thời gian của bảng Fact
            FactAqiReading.aqi_value.label("aqi"),
            FactAqiReading.aqi_category.label("category"),
            DimLocation.city,
            DimTime.year,
            DimTime.month,
            DimTime.season,
        ).join(FactAqiReading.location_rel).join(FactAqiReading.time_rel).order_by(FactAqiReading.loaded_at)
        
        # Áp dụng bộ lọc (hàm xử lý lọc đã được tối ưu hóa join ở trên)
        if city:
            stmt = stmt.where(DimLocation.city.ilike(f"%{city}%"))
        if year:
            stmt = stmt.where(DimTime.year == year)
        if month:
            stmt = stmt.where(DimTime.month == month)
        if season:
            stmt = stmt.where(DimTime.season.ilike(f"%{season}%"))
            
        rows = self.session.execute(stmt).all()
        return [
            {
                "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
                "aqi": row.aqi,
                "category": row.category,
                "city": row.city,
                "district": "", # Trả về chuỗi rỗng nếu schema hiện tại không phân rã cột district
                "year": row.year,
                "month": row.month,
                "season": row.season,
            }
            for row in rows
        ]

    def get_trend(self, city: Optional[str] = None, district: Optional[str] = None, year: Optional[int] = None, season: Optional[str] = None) -> list[dict]:
        # Phải group by theo các trường thuộc bảng chiều DimTime
        stmt = select(
            DimTime.year,
            DimTime.month,
            func.avg(FactAqiReading.aqi_value).label("average_aqi"),
            func.count(FactAqiReading.fact_key).label("records"),
        ).join(FactAqiReading.time_rel).group_by(DimTime.year, DimTime.month).order_by(DimTime.year, DimTime.month)
        
        # Áp dụng bộ lọc liên kết bảng
        if city:
            stmt = stmt.join(FactAqiReading.location_rel).where(DimLocation.city.ilike(f"%{city}%"))
        if year:
            stmt = stmt.where(DimTime.year == year)
        if season:
            stmt = stmt.where(DimTime.season.ilike(f"%{season}%"))
            
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
            DimTime.season,
            func.avg(FactAqiReading.aqi_value).label("average_aqi"),
            func.max(FactAqiReading.aqi_value).label("max_aqi"),
            func.min(FactAqiReading.aqi_value).label("min_aqi"),
            func.count(FactAqiReading.fact_key).label("records"),
        ).join(FactAqiReading.time_rel).group_by(DimTime.season).order_by(DimTime.season)
        
        if city:
            stmt = stmt.join(FactAqiReading.location_rel).where(DimLocation.city.ilike(f"%{city}%"))
        if year:
            stmt = stmt.where(DimTime.year == year)
            
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
            DimTime.year,
            DimTime.month,
            func.avg(FactAqiReading.aqi_value).label("average_aqi"),
            func.max(FactAqiReading.aqi_value).label("max_aqi"),
            func.min(FactAqiReading.aqi_value).label("min_aqi"),
            func.count(FactAqiReading.fact_key).label("records"),
        ).join(FactAqiReading.time_rel).group_by(DimTime.year, DimTime.month).order_by(DimTime.year, DimTime.month)
        
        if city:
            stmt = stmt.join(FactAqiReading.location_rel).where(DimLocation.city.ilike(f"%{city}%"))
        if year:
            stmt = stmt.where(DimTime.year == year)
            
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
            DimTime.year,
            func.avg(FactAqiReading.aqi_value).label("average_aqi"),
            func.max(FactAqiReading.aqi_value).label("max_aqi"),
            func.min(FactAqiReading.aqi_value).label("min_aqi"),
            func.count(FactAqiReading.fact_key).label("records"),
        ).join(FactAqiReading.time_rel).group_by(DimTime.year).order_by(DimTime.year)
        
        if city:
            stmt = stmt.join(FactAqiReading.location_rel).where(DimLocation.city.ilike(f"%{city}%"))
        if season:
            stmt = stmt.where(DimTime.season.ilike(f"%{season}%"))
            
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