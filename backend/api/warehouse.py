from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.session import SessionLocal # Hoặc hàm get_db tùy nhóm thiết lập
from services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouse", tags=["Warehouse"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/summary")
def get_warehouse_summary(db: Session = Depends(get_db)):
    try:
        service = WarehouseService(db)
        return {"success": True, "data": service.get_summary()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/city/{city}")
def get_city_summary(city: str, db: Session = Depends(get_db)):
    try:
        service = WarehouseService(db)
        result = service.get_city_summary(city)
        
        # Nếu không tìm thấy dữ liệu nào của thành phố này trong Fact table
        if not result or result["total_records"] == 0:
            return {
                "success": True,
                "data": {
                    "city": city,
                    "total_records": 0,
                    "average_aqi": None,
                    "max_aqi": None,
                    "min_aqi": None
                }
            }
            
        return {"success": True, "data": result}
    except Exception as e:
        # Trả chi tiết lỗi ra Swagger thay vì chỉ chữ "Internal Server Error" chung chung để dễ debug
        raise HTTPException(status_code=500, detail=f"Lỗi tầng Route: {str(e)}")