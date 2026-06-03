import logging
from fastapi import APIRouter, HTTPException
from schemas import CurrentAQIResponse
from services.aqi_provider.waqi import WaqiProvider

logger = logging.getLogger(__name__)
router = APIRouter()
provider = WaqiProvider()

@router.get("/current/{city}", response_model=CurrentAQIResponse)
def get_current_aqi(city: str):
    if not city.strip():
        raise HTTPException(status_code=400, detail="City name cannot be empty")
        
    try:
        data = provider.get_city_data(city)
        return CurrentAQIResponse(success=True, data=data)
    except ValueError as e:
        logger.warning(f"City not found or API issue for {city}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get current AQI for {city}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
