try:
    from database.connection import SessionLocal
except ImportError:
    from .connection import SessionLocal

class SessionProxy:
    def __init__(self):
        # Khởi tạo session kết nối MariaDB gốc của Bảo
        self._db = SessionLocal()

    def __enter__(self):
        # Phục vụ cho lệnh: with get_session() as session:
        # Trả về chính xác đối tượng Session gốc để code cũ của Thọ chạy không lỗi
        return self._db

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Tự động đóng kết nối khi thoát khối lệnh with
        self._db.close()

    def __getattr__(self, name):
        # Phục vụ cho FastAPI: db: Session = Depends(get_session)
        # Nếu gọi trực tiếp các hàm như .execute(), .query(), .commit(), 
        # proxy sẽ tự động chuyển tiếp lệnh xuống thẳng session gốc
        return getattr(self._db, name)

    def __del__(self):
        # Cơ chế phòng thủ: Tự động giải phóng connection pool nếu không dùng tới nữa
        try:
            self._db.close()
        except Exception:
            pass

def get_session():
    return SessionProxy()