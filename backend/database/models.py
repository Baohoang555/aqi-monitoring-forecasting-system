from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ==========================================
# 1. CÁC BẢNG CHIỀU (DIMENSION TABLES)
# ==========================================

class DimTime(Base):
    __tablename__ = "dim_time"

    time_key = Column(Integer, primary_key=True, index=True)
    full_date = Column(DateTime, nullable=False)
    year = Column(Integer, index=True)
    month = Column(Integer)
    month_name = Column(String(20))
    quarter = Column(Integer)
    season = Column(String(20), index=True) # 'dry' hoặc 'rainy'
    week = Column(Integer)
    is_weekend = Column(Integer)

    # Quan hệ ngược lại với bảng Fact
    fact_readings = relationship("FactAqiReading", back_populates="time_rel")


class DimLocation(Base):
    __tablename__ = "dim_location"

    location_key = Column(Integer, primary_key=True, index=True)
    city = Column(String(255), index=True)
    country = Column(String(255), index=True)
    country_code = Column(String(10))
    continent = Column(String(50))

    fact_readings = relationship("FactAqiReading", back_populates="location_rel")


class DimPollutant(Base):
    __tablename__ = "dim_pollutant"

    pollutant_key = Column(Integer, primary_key=True, index=True)
    pollutant_code = Column(String(50), index=True) # PM2.5, PM10, NO2...
    pollutant_name = Column(String(100))
    unit = Column(String(50)) # ug/m3, mg/m3

    fact_readings = relationship("FactAqiReading", back_populates="pollutant_rel")


# ==========================================
# 2. BẢNG SỰ KIỆN TRUNG TÂM (FACT TABLE)
# ==========================================

class FactAqiReading(Base):
    __tablename__ = "fact_aqi_reading"

    # Thay thế cột 'id' cũ bằng cấu trúc Star Schema hệ thống
    fact_key = Column(Integer, primary_key=True, autoincrement=True)
    
    # Các khóa ngoại liên kết sang bảng Dim
    time_key = Column(Integer, ForeignKey("dim_time.time_key"), index=True)
    location_key = Column(Integer, ForeignKey("dim_location.location_key"), index=True)
    pollutant_key = Column(Integer, ForeignKey("dim_pollutant.pollutant_key"), index=True)

    # Các chỉ số đo lường (Measures & Metrics)
    concentration = Column(Float)       # Nồng độ thô chất ô nhiễm
    aqi_value = Column(Float)           # Chỉ số AQI tương ứng
    aqi_category = Column(String(100))   # Phân loại (Good, Moderate...)
    is_anomaly = Column(Integer)        # Đánh dấu dữ liệu bất thường (0.8% anomaly)
    batch_id = Column(String(100))       # Quản lý lô của Airflow
    loaded_at = Column(DateTime)        # Thời gian nạp vào DB

    # Thiết lập các mối quan hệ (Relationships) để Thọ dễ dàng JOIN khi làm OLAP
    time_rel = relationship("DimTime", back_populates="fact_readings")
    location_rel = relationship("DimLocation", back_populates="fact_readings")
    pollutant_rel = relationship("DimPollutant", back_populates="fact_readings")


# ==========================================
# 3. KHỐI VẬT HÓA BĂNG ĐĂNG (ICEBERG CUBE)
# ==========================================

class CubeCitySeason(Base):
    __tablename__ = "cube_city_season"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String(100), index=True)
    country = Column(String(100))
    season = Column(String(10), index=True)
    pollutant_code = Column(String(20))
    reading_count = Column(Integer)
    avg_aqi = Column(Float)
    max_aqi = Column(Integer)
    avg_conc = Column(Float)
    unhealthy_cnt = Column(Integer)


# ==========================================
# 4. ĐÁNH GIÁ MÔ HÌNH (MODEL EVALUATION)
# ==========================================

class ModelEvaluation(Base):
    """Giữ nguyên bảng này phục vụ cho việc tracking metrics của An"""
    __tablename__ = "model_evaluation"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), index=True)
    metric = Column(String(50), index=True) # F1, Precision, Recall...
    value = Column(Float)