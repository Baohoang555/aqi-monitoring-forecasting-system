from fastapi import APIRouter

from schemas import ApiResponse, DashboardOverview
from services import DashboardService

router = APIRouter()

@router.get("/dashboard/overview", response_model=ApiResponse[DashboardOverview])
def dashboard_overview():
    overview = DashboardService.get_overview()
    return ApiResponse(success=True, data=overview)
