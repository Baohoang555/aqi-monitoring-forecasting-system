from repositories.warehouse_repository import WarehouseRepository
from database.session import get_session
# Import Class dịch vụ Warehouse
from services.warehouse_service import WarehouseService 
from services import model_service

class DashboardService:
    @staticmethod
    def get_overview() -> dict:
        # Mở session dùng chung cho toàn bộ tiến trình lấy dữ liệu dashboard
        with get_session() as session:
            # SỬA TẠI ĐÂY: Khởi tạo đối tượng WarehouseService và truyền session vào thay vì gọi static
            w_service = WarehouseService(session)
            warehouse_summary = w_service.get_summary()
            
            # Khởi tạo repository để gọi các hàm truy vấn tối ưu của Bảo
            repo = WarehouseRepository(session)
            
            # Lấy các chỉ số thống kê đã được tối ưu hóa qua Index và Cube vật hóa
            popular_category = repo.get_most_frequent_category_fast()
            best_worst = repo.get_best_worst_city_fast()

        # Lấy metric của An (giữ ngoài block session nếu nó tự quản lý kết nối)
        model_metrics = model_service.get_performance_metrics()

        return {
            "total_records": warehouse_summary.get("total_records", 0),
            "average_aqi": warehouse_summary.get("average_aqi"),
            "worst_city": best_worst.get("worst_city"),
            "best_city": best_worst.get("best_city"),
            "most_frequent_aqi_category": popular_category,
            "model_metrics": model_metrics,
        }