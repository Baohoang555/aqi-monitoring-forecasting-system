from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import threading
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store (reset khi restart server)
_config = {"alert_threshold": 150}
_stations = [
    {"id": "HN01", "name": "Hoàn Kiếm, Hà Nội", "status": "Active", "lastUpdate": "10 mins ago"},
    {"id": "HN02", "name": "Cầu Giấy, Hà Nội", "status": "Active", "lastUpdate": "12 mins ago"},
    {"id": "HCM01", "name": "Q1, TP.HCM", "status": "Warning", "lastUpdate": "1 hour ago"},
    {"id": "DN01", "name": "Hải Châu, Đà Nẵng", "status": "Offline", "lastUpdate": "2 days ago"},
]
_retrain_status = {"running": False, "last_result": None}


class StationCreate(BaseModel):
    id: str
    name: str
    status: str = "Active"
    lastUpdate: str = "Just now"


class StationUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    lastUpdate: Optional[str] = None


class ConfigUpdate(BaseModel):
    alert_threshold: int


# --- Config ---
@router.get("/admin/config")
def get_config():
    return {"success": True, "data": _config}


@router.post("/admin/config")
def update_config(body: ConfigUpdate):
    _config["alert_threshold"] = body.alert_threshold
    logger.info(f"Alert threshold updated to {body.alert_threshold}")
    return {"success": True, "data": _config}


# --- Stations ---
@router.get("/admin/stations")
def get_stations():
    return {"success": True, "data": _stations}


@router.post("/admin/stations")
def add_station(body: StationCreate):
    if any(s["id"] == body.id for s in _stations):
        raise HTTPException(status_code=400, detail=f"Station ID '{body.id}' already exists")
    _stations.append(body.dict())
    return {"success": True, "data": body.dict()}


@router.put("/admin/stations/{station_id}")
def update_station(station_id: str, body: StationUpdate):
    for s in _stations:
        if s["id"] == station_id:
            if body.name is not None:
                s["name"] = body.name
            if body.status is not None:
                s["status"] = body.status
            if body.lastUpdate is not None:
                s["lastUpdate"] = body.lastUpdate
            return {"success": True, "data": s}
    raise HTTPException(status_code=404, detail="Station not found")


@router.delete("/admin/stations/{station_id}")
def delete_station(station_id: str):
    global _stations
    before = len(_stations)
    _stations = [s for s in _stations if s["id"] != station_id]
    if len(_stations) == before:
        raise HTTPException(status_code=404, detail="Station not found")
    return {"success": True, "message": f"Station {station_id} deleted"}


# --- Retrain ---
@router.get("/admin/retrain/status")
def retrain_status():
    return {"success": True, "data": _retrain_status}


@router.post("/admin/retrain")
def trigger_retrain():
    if _retrain_status["running"]:
        raise HTTPException(status_code=409, detail="Retrain already in progress")

    def _run():
        import time
        _retrain_status["running"] = True
        _retrain_status["last_result"] = None
        logger.info("Retrain started...")
        time.sleep(5)  # Giả lập thời gian train
        _retrain_status["running"] = False
        _retrain_status["last_result"] = "success"
        logger.info("Retrain completed")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return {"success": True, "message": "Retrain triggered"}