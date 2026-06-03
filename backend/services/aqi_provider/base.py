from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAQIProvider(ABC):
    @abstractmethod
    def get_city_data(self, city: str) -> Dict[str, Any]:
        """
        Fetch real-time AQI and weather data for a given city.
        Returns a dictionary containing sensor readings and geo info.
        """
        pass
