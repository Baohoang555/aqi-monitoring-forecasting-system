from fastapi import APIRouter
from services import model_service

router = APIRouter()

@router.get("/model/info")
def model_info():
    return {"success": True, "data": model_service.get_model_info()}

@router.get("/model/feature-importance")
def model_feature_importance():
    return {"success": True, "data": model_service.get_feature_importance()}

@router.get("/model/shap")
def model_shap():
    return {"success": True, "data": model_service.get_shap_summary()}

@router.get("/model/performance")
def model_performance():
    return {"success": True, "data": model_service.get_performance_metrics()}
