from typing import Any
import pandas as pd

from services import model_service
from schemas.prediction import PredictionRequest

class PredictionService:
    @staticmethod
    def build_feature_vector(payload: PredictionRequest) -> pd.DataFrame:
        if payload.features:
            feature_values = payload.features
        else:
            feature_values = {
                "pm25": payload.pm25,
                "pm10": payload.pm10,
                "no2": payload.no2,
                "o3": payload.o3,
                "temperature": payload.temperature,
                "humidity": payload.humidity,
            }
        feature_values = {k: v for k, v in feature_values.items() if v is not None}
        return model_service.build_input_dataframe(feature_values)

    @staticmethod
    def predict(payload: PredictionRequest) -> dict[str, Any]:
        input_df = PredictionService.build_feature_vector(payload)
        result = model_service.predict(input_df)
        return result
