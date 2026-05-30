"""
PH-04: Airflow DAG — ETL mỗi ngày, đơn giản
Không cần Spark, chạy Python ETL trực tiếp.

Copy file này vào thư mục dags/ của Airflow.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

DEFAULT_ARGS = {
    "owner":            "bao_ph04",
    "retries":          1,
    "retry_delay":      timedelta(minutes=10),
    "email_on_failure": True,
    "email":            ["bao@team.edu.vn"],
}


# ── Task functions ────────────────────────────────────────────────────────

def run_etl(**ctx):
    """Chạy ETL pipeline."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "/opt/airflow/etl/etl_pipeline.py"],
        capture_output=True, text=True, timeout=3600
    )
    print(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1000:])


def check_row_count(**ctx):
    """Kiểm tra dữ liệu đã load."""
    import pymysql
    DB = dict(host="localhost", port=3306,
              user="root", password="changeme", db="aqi_dw")
    conn = pymysql.connect(**DB)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM fact_aqi_reading")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM cube_city_season")
        cubes = cur.fetchone()[0]
    conn.close()
    print(f"fact_aqi_reading: {total:,} rows")
    print(f"cube_city_season: {cubes:,} cells")
    if total == 0:
        raise ValueError("fact_aqi_reading trống — ETL thất bại!")


# ── DAG ───────────────────────────────────────────────────────────────────

with DAG(
    dag_id          = "aqi_etl_daily",
    default_args    = DEFAULT_ARGS,
    description     = "PH-04: ETL AQI → MariaDB mỗi ngày",
    schedule_interval = "0 2 * * *",   # 2:00 sáng mỗi ngày
    start_date      = datetime(2014, 1, 1),
    catchup         = False,
    tags            = ["ph04", "aqi"],
) as dag:

    start  = EmptyOperator(task_id="start")
    etl    = PythonOperator(task_id="run_etl",        python_callable=run_etl,        provide_context=True)
    check  = PythonOperator(task_id="check_row_count", python_callable=check_row_count, provide_context=True)
    finish = EmptyOperator(task_id="finish")

    start >> etl >> check >> finish
