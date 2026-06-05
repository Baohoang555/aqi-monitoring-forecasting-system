from fastapi import APIRouter, HTTPException
from schemas import ApiResponse, DashboardOverview
from services.dashboard_service import DashboardService

router = APIRouter()

@router.get("/dashboard/overview", response_model=ApiResponse[DashboardOverview])
def dashboard_overview():
    try:
        overview = DashboardService.get_overview()
        return ApiResponse(success=True, data=overview)
    except Exception as e:
        # In chi tiết lỗi cụ thể nếu Pydantic Schema của Thọ (DashboardOverview) bị lệch tên trường
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi cấu trúc dữ liệu Dashboard: {str(e)}"
        )