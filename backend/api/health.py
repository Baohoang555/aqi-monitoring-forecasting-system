from fastapi import APIRouter
from schemas import HealthResponse
from services import model_service

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check():
    # Simple check if model is loaded properly
    is_model_loaded = getattr(model_service, "_model", None) is not None
    return HealthResponse(
        status="ok",
        version="1.0.0",
        model_loaded=is_model_loaded
    )
