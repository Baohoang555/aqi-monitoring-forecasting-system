from sqlalchemy.orm import Session
from repositories.warehouse_repository import WarehouseRepository

class WarehouseService:
    def __init__(self, db: Session):
        self.repository = WarehouseRepository(db)

    def get_summary(self) -> dict:
        return self.repository.get_summary()

    def get_city_summary(self, city: str) -> dict:
        # Đảm bảo gọi đúng hàm get_city_summary từ repository mới đã sửa của Bảo
        return self.repository.get_city_summary(city)

    def get_pollutant_stats(self) -> list[dict]:
        return self.repository.get_pollutant_stats()

    def get_best_worst_city(self) -> dict:
        return self.repository.get_best_worst_city_fast()