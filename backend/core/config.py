import os
from dotenv import load_dotenv

load_dotenv()

WAQI_API_TOKEN = os.getenv("WAQI_API_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")
MODEL_PATH = os.getenv("MODEL_PATH")
LABEL_ENCODER_PATH = os.getenv("LABEL_ENCODER_PATH")
FEATURE_COLUMNS_PATH = os.getenv("FEATURE_COLUMNS_PATH")
MODEL_METRICS_PATH = os.getenv("MODEL_METRICS_PATH")
SHAP_SUMMARY_PATH = os.getenv("SHAP_SUMMARY_PATH")

MODEL_SOURCE = os.getenv("MODEL_SOURCE", "local")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")