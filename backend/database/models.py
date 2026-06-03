from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AqiHistory(Base):
    __tablename__ = "aqi_history"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    district = Column(String, index=True)
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)
    season = Column(String, index=True)
    recorded_at = Column(DateTime)
    aqi = Column(Float)
    category = Column(String)
    pm25 = Column(Float)
    pm10 = Column(Float)
    no2 = Column(Float)
    o3 = Column(Float)
    co = Column(Float)
    so2 = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    population_density = Column(Float)
    industry_density = Column(Float)
    country = Column(String)
    state = Column(String)
    district_name = Column(String)

class OlapCubeFact(Base):
    __tablename__ = "olap_cube"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    district = Column(String, index=True)
    year = Column(Integer, index=True)
    month = Column(Integer, index=True)
    season = Column(String, index=True)
    measure = Column(String, index=True)
    value = Column(Float)
    category = Column(String)
    region = Column(String)

class ModelEvaluation(Base):
    __tablename__ = "model_evaluation"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    metric = Column(String, index=True)
    value = Column(Float)
