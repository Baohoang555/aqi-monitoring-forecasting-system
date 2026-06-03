# 🌍 Backend API - Hệ Thống Dự Báo Chất Lượng Không Khí

Backend này cung cấp API để frontend gọi nhằm lấy dữ liệu chất lượng không khí, dự báo AQI, và các phân tích thống kê.

---

## 🚀 Bắt Đầu Nhanh

### 1. Chuẩn Bị Môi Trường

**Yêu cầu:**
- Python 3.12+
- MariaDB đang chạy
- `.env` file được cấu hình

**Xem file `.env` có:**
```
DATABASE_URL=mysql+pymysql://root:1882005@localhost:3307/aqi_dw?charset=utf8mb4
WAQI_API_TOKEN=YOUR_API_KEY_HERE 
OPENWEATHER_API_KEY=YOUR_API_KEY_HERE
```

### 2. Cài Đặt Thư Viện

```bash
# Active virtual environment
.\venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt
```

### 3. Chạy Backend

```bash
# Chuyển về thư mục backend
cd backend

# Kích hoạt virtual environment
.\venv\Scripts\activate

# Chạy với reload (development)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Hoặc chạy bình thường (production)
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Kiểm tra:**
- Truy cập `http://localhost:8000/health` → Nếu thấy `{"status": "ok"}` là thành công ✅
- Xem docs: `http://localhost:8000/docs` (giao diện Swagger)

---

## 📁 Cấu Trúc Thư Mục & Vai Trò

```
backend/
├── api/                         # Các endpoint (routes)
├── services/                    # Logic xử lý
├── repositories/                # Truy vấn database
├── database/                    # Kết nối & models
├── core/                        # Cấu hình & logging
├── schemas/                     # Định dạng request/response
├── models/                      # File mô hình ML
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
├── .env                         # Cấu hình (không commit)
├── .env.example                 # Template cấu hình
└── README.md                    # File hướng dẫn

### Chi Tiết Từng Folder

#### 🎯 **`api/`** - Các Endpoint (Điểm kết nối)
Frontend gọi các URL từ đây.

| File | Endpoint | Mục đích |
|------|----------|---------|
| `health.py` | `GET /health` | Kiểm tra server có sống không |
| `current.py` | `GET /current/{city}` | Lấy dữ liệu AQI hiện tại |
| `predict.py` | `POST /predict` | Dự báo AQI |
| `model_info.py` | `GET /model/info` | Thông tin mô hình ML |
| `warehouse.py` | `GET /warehouse/*` | Thống kê tổng hợp |
| `historical.py` | `GET /aqi/*` | Lịch sử AQI |
| `olap.py` | `GET /olap/*` | Phân tích OLAP (slice, dice, drill-down) |
| `dashboard.py` | `GET /dashboard/*` | Dữ liệu dashboard |

**Ví dụ từ Frontend:**
```javascript
// React/Vue/Angular
fetch('http://localhost:8000/current/Hanoi')
  .then(res => res.json())
  .then(data => console.log(data))
```

---

#### **`services/`** - Logic Xử Lý
Chỗ xử lý "não bộ" của backend. Frontend không trực tiếp gọi những file này.

| File | Vai trò |
|------|---------|
| `model_service.py` | Load mô hình ML, chạy dự báo |
| `prediction_service.py` | Wrapper cho dự báo |
| `warehouse_service.py` | Xử lý thống kê data |
| `cube_service.py` | OLAP operations (slice, dice) |
| `dashboard_service.py` | Tổng hợp dữ liệu dashboard |
| `feature_engineer.py` | Xử lý features cho ML |
| `monitoring_service.py` | Theo dõi hiệu suất |

**Flow:** `API route` → `Service xử lý` → `Repository query DB` → `Trả kết quả`

---

#### **`repositories/`** - Truy Vấn Database
Tất cả SQL queries để lấy dữ liệu đều ở đây.

| File | Chức năng |
|------|----------|
| `fact_repository.py` | Lấy dữ liệu AqiHistory (thành phố, thời gian, chỉ số) |
| `warehouse_repository.py` | Tóm tắt & thống kê |
| `cube_repository.py` | OLAP queries (nhóm, lọc dữ liệu) |

**Ví dụ xử lý:**
```python
# Repository tự động convert thành SQL
session.query(AqiHistory).filter(
  AqiHistory.city == 'Hanoi',
  AqiHistory.year == 2024
)
# ↓ Thành SQL:
# SELECT * FROM aqi_history WHERE city='Hanoi' AND year=2024
```

---

#### **`database/`** - Database Layer
Kết nối MariaDB & định nghĩa các bảng.

| File | Vai trò |
|------|---------|
| `connection.py` | Tạo kết nối MariaDB engine |
| `session.py` | Quản lý session (mở/đóng connection) |
| `models.py` | Định nghĩa bảng: `AqiHistory`, `OlapCubeFact`, `ModelEvaluation` |

**Note:** Không cần sửa file này trừ khi thêm bảng mới.

---

#### **`core/`** - Cấu Hình & Logging
Những cài đặt chung cho cả backend.

| File | Vai trò |
|------|---------|
| `config.py` | Đọc `.env`, lấy biến môi trường (DATABASE_URL, API tokens) |
| `logging_config.py` | Setup logging (ghi log vào file) |
| `logger.py` | Logger instance dùng chung |

---

#### **`schemas/`** - Request/Response Format
Định nghĩa format data được gửi đi/nhận vào.

| File | Định dạng |
|------|----------|
| `prediction.py` | `PredictionRequest`, `PredictionResponse` |
| `warehouse.py` | `WarehouseSummaryResponse` |
| `historical.py` | `HistoricalAggregation` |
| `common.py` | `ApiResponse` (wrapper cho tất cả response) |

**Ví dụ:**
```python
# Frontend gửi JSON này
{
  "pm25": 35,
  "pm10": 80,
  "city": "Hanoi"
}

# Backend trả về
{
  "success": true,
  "data": {
    "aqi_category": "Moderate",
    "aqi_value": 76
  }
}
```

---

#### **`models/`** - File Mô Hình ML
Những file `.pkl` là mô hình đã train sẵn.

| File | Mục đích |
|------|---------|
| `best_aqi_classifier_pipeline.pkl` | Mô hình dự báo AQI |
| `label_encoder.pkl` | Chuyển số thành tên category (Good, Moderate, Poor) |
| `feature_columns.json` | Danh sách 155 features |
| `model_metrics.json` | Accuracy, precision, recall |
| `stacking_ensemble.pkl` | Mô hình ensemble |

**Note:** Khi khởi động, `model_service.py` tự động load những file này vào memory.

---

#### **`main.py`** - Entry Point
File chính khởi động toàn bộ backend.

**Hoạt động:**
1. Tạo FastAPI app
2. Setup CORS (cho phép frontend gọi)
3. Đăng ký routes
4. Load mô hình ML vào memory
5. Chạy server trên port 8000

---

## Các API Endpoint Chính

### Kiểm tra Server
```
GET /health
Response: {"status": "ok", "model_loaded": true}
```

### Lấy Dữ Liệu AQI Hiện Tại
```
GET /current/Hanoi
Response: {
  "city": "Hanoi",
  "aqi": 85,
  "pm25": 45.2,
  "temperature": 28.5,
  ...
}
```

### Dự Báo AQI (Chưa hoàn chỉnh)
```
POST /predict
Body: {"pm25": 35, "pm10": 80, "city": "Hanoi"}
Response: {
  "aqi_category": "Moderate",
  "aqi_value": 76,
  "confidence": 0.85
}
```

### Thống Kê Warehouse
```
GET /warehouse/summary
Response: {
  "total_cities": 250,
  "avg_aqi": 62.4,
  "cities_with_data": 248
}
```

### Phân Tích OLAP
```
GET /olap/slice?year=2024&month=6
Response: [dữ liệu sliced]
```

---

## Troubleshooting

### Lỗi: "ModuleNotFoundError: No module named 'pymysql'"
```bash
# Cài lại driver MariaDB
pip install pymysql cryptography
```

### Lỗi: "Connection refused: Can't connect to MariaDB"
```
Kiểm tra:
1. MariaDB có chạy không? (Service running)
2. Port 3307 có mở không?
3. Credentials đúng không? (user: root, password: 1882005)
```

### Lỗi: "arange: cannot compute length"
```
→ Lỗi mô hình ML (file pickle bị lỗi)
→ Cần retrain hoặc update numpy version
```

### Cách Debug
```bash
# Xem log chi tiết
# Logs được lưu tại: logs/backend.log

# Test import
python -c "import app.main; print('OK')"

# Xem docs API
http://localhost:8000/docs
```

---

## Tài Liệu Thêm

- **Swagger UI**: http://localhost:8000/docs (xem tất cả endpoint + test)
- **ReDoc**: http://localhost:8000/redoc (xem API structure đẹp hơn)
- **FastAPI**: https://fastapi.tiangolo.com/

---

## Ghi Chú cho Frontend Developer

- 🔴 Các endpoint có `*` = chưa test kỹ (cẩn thận khi dùng)
- 🟡 Endpoint `/predict` = chưa hoàn chỉnh (sắp fix)
- 🟢 Endpoint `/health`, `/current`, `/model/info` = đã test, OK

---

## 📝 License
Nội bộ project DATA_FINAL
│   │   ├── monitoring_service.py
│   │   ├── model_service.py
│   │   ├── prediction_service.py
│   │   ├── warehouse_service.py
│   │   ├── cube_service.py
│   │   ├── dashboard_service.py
│   ├── main.py
```

## Setup

1. Create and activate your Python environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and update the values:
   ```bash
   copy .env.example .env
   ```
4. Set `DATABASE_URL` to point to your PostgreSQL warehouse.
5. Set model artifact paths for `MODEL_PATH`, `LABEL_ENCODER_PATH`, `FEATURE_COLUMNS_PATH`, and optional metric files.

