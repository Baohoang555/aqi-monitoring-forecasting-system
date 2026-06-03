from collections import Counter

from services import warehouse_service, model_service
from repositories.fact_repository import FactRepository
from repositories.warehouse_repository import WarehouseRepository
from database.session import get_session

class DashboardService:
    @staticmethod
    def get_overview() -> dict:
        warehouse_summary = warehouse_service.WarehouseService.get_summary()
        model_metrics = model_service.get_performance_metrics()
        popular_category = DashboardService._get_most_frequent_category()
        best_worst = DashboardService._get_best_worst_city()

        return {
            "total_records": warehouse_summary.get("total_records", 0),
            "average_aqi": warehouse_summary.get("average_aqi"),
            "worst_city": best_worst.get("worst_city"),
            "best_city": best_worst.get("best_city"),
            "most_frequent_aqi_category": popular_category,
            "model_metrics": model_metrics,
        }

    @staticmethod
    def _get_most_frequent_category() -> str:
        with get_session() as session:
            repository = FactRepository(session)
            history = repository.get_history()
            categories = [item["category"] for item in history if item.get("category")]
            if not categories:
                return "N/A"
            counter = Counter(categories)
            return counter.most_common(1)[0][0]

    @staticmethod
    def _get_best_worst_city() -> dict[str, str | None]:
        with get_session() as session:
            repository = WarehouseRepository(session)
            return repository.get_best_worst_city()
