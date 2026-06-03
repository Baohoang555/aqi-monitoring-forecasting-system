from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

from core.logging_config import setup_logging
from services import model_service
from api import predict, current, health, model_info, warehouse
from api import historical, olap, dashboard

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Urban Air Quality Intelligence Platform - Backend API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(predict.router, tags=["Prediction"])
app.include_router(current.router, tags=["Realtime Data"])
app.include_router(model_info.router, tags=["Model Info"])
app.include_router(warehouse.router, tags=["Warehouse"])
app.include_router(historical.router, tags=["Historical"])
app.include_router(olap.router, tags=["OLAP"])
app.include_router(dashboard.router, tags=["Dashboard"])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    return response

@app.on_event("startup")
def startup():
    logger.info("Starting up backend service...")
    try:
        model_service.load_artifacts()
    except Exception as e:
        logger.error(f"Failed to load artifacts on startup: {e}")
        # Not raising here to allow /health endpoint to show model is NOT loaded
        
@app.get("/")
def root():
    return {"message": "Urban Air Quality Intelligence Backend API is running"}