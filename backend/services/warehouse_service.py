from typing import Optional

from repositories.warehouse_repository import WarehouseRepository
from database.session import get_session

class WarehouseService:
    @staticmethod
    def get_summary() -> dict:
        with get_session() as session:
            repository = WarehouseRepository(session)
            return repository.get_summary()

    @staticmethod
    def get_city_summary(city: str) -> dict:
        with get_session() as session:
            repository = WarehouseRepository(session)
            return repository.get_city_summary(city)

    @staticmethod
    def get_pollutant_stats() -> list[dict]:
        with get_session() as session:
            repository = WarehouseRepository(session)
            return repository.get_pollutant_stats()
