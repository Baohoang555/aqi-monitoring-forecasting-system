# DATA_FINAL Project

## Tổng quan
Dự án này là bộ workflow phân tích và mô hình hoá dữ liệu ô nhiễm không khí (AQI) toàn cầu.
Nó bao gồm:
- Nhận dữ liệu thô từ `data/raw` và `data/datalake`
- Phân tích EDA
- Tiền xử lý, feature engineering và tạo bộ dữ liệu huấn luyện
- Huấn luyện mô hình phân loại AQI
- ETL vào kho dữ liệu MariaDB
- Dashboard OLAP bằng Streamlit

## Cấu trúc chính

### `data/`
- `datalake/aqi/`: dữ liệu AQI đã được chuẩn hoá/luồng.
- `raw/`: dữ liệu thô theo quốc gia và file `global_air_quality_2014_2025.csv`.

### `notebooks/`
- `aqi_etl_dag.py`: DAG Airflow để chạy ETL hàng ngày và kiểm tra row count.
- `etl_pipeline.py`: Pipeline ETL từ CSV/Parquet vào MariaDB DW.
- `olap_dashboard.py`: Streamlit dashboard OLAP đọc từ MariaDB.
- `rebuild_cube.py`: Script tái tạo các bảng cube OLAP (`cube_city_season`, `cube_city_month`).
- `eda_analysis.py`: Script khám phá dữ liệu EDA, thống kê miêu tả, top cities, correlation, time series.

### `src/`
- `preprocess_features.py`: tiền xử lý, tạo ma trận dữ liệu giờ, xử lý missing/outlier, feature engineering và tạo target classification.
- `train_classification.py`: huấn luyện mô hình phân loại baseline (LogisticRegression, DecisionTree, RandomForest, ExtraTrees) và lưu kết quả, confusion matrix.

### `backend/`
- `backend/app/main.py`: hiện tại trống, là placeholder cho backend nếu mở rộng sau này.
- `backend/requirements.txt`: hiện tại trống.

### `outputs/`
- `outputs/eda-outputs/`: chứa báo cáo EDA, feature catalog, imputation/outlier summary, preprocessing metadata.
- `outputs/ph05/`: chứa kết quả huấn luyện, báo cáo classification và metrics.

## Các file cài đặt
- `requirements.txt`: dependencies chung cho phân tích, EDA, ML và visualization.
- `backend/requirements.txt`: hiện chưa có nội dung.

## Chức năng theo file

- `notebooks/aqi_etl_dag.py`: định nghĩa DAG Airflow để chạy `notebooks/etl_pipeline.py` và kiểm tra dữ liệu load lên MariaDB.
- `notebooks/etl_pipeline.py`: đọc dữ liệu CSV/Parquet, chuẩn hoá cột, tính AQI nếu thiếu, tạo dim/time/location và nạp vào MariaDB.
- `notebooks/olap_dashboard.py`: hiển thị KPI, top city, xu hướng năm, so sánh mùa và bảng OLAP từ các bảng cube trong MySQL.
- `notebooks/rebuild_cube.py`: xây dựng lại các cube OLAP từ `fact_aqi_reading`.
- `notebooks/eda_analysis.py`: chạy phân tích EDA toàn bộ dataset, tạo biểu đồ và lưu ảnh vào thư mục output.
- `src/preprocess_features.py`: giai đoạn PH-03, load AQI/weather, tạo hourly matrix, xử lý missing, tạo lag/rolling/spatial features và target dự báo AQI 1 giờ.
- `src/train_classification.py`: giai đoạn PH-05, load dữ liệu PH-03, sample train/val, train baseline models, đánh giá và lưu metrics.

## Chạy nhanh
1. Cài dependencies:
   - `pip install -r requirements.txt`
2. Chạy EDA:
   - `python notebooks/eda_analysis.py`
3. Chạy ETL vào MariaDB:
   - `python notebooks/etl_pipeline.py`
4. Chạy dashboard:
   - `streamlit run notebooks/olap_dashboard.py`
5. Chạy tiền xử lýfeatures và huấn luyện:
   - `python src/preprocess_features.py`
   - `python src/train_classification.py`

## Ghi chú
- `backend/` hiện chỉ là cấu trúc placeholder, chưa có thực thi.
- Database MariaDB cần sẵn sàng trên `localhost:3306` với user/password tương ứng.
- `etl_pipeline.py` sử dụng `PARQUET_DIR = F:\DATA_FINAL\data\raw`; có thể cần chỉnh lại theo môi trường.
