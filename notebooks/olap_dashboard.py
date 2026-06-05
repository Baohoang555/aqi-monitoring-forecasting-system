"""
PH-04: OLAP Dashboard — Streamlit + MariaDB
Thay thế Superset bằng Streamlit cho đơn giản, chạy được ngay trên Windows.

Cài đặt:
    pip install streamlit pymysql sqlalchemy pandas plotly

Chạy:
    streamlit run olap_dashboard.py
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

# ─── Kết nối ─────────────────────────────────────────────────────────────
DB_URL = "mysql+pymysql://root:123@localhost:3306/aqi_dw?charset=utf8mb4"


@st.cache_resource
def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True)


@st.cache_data(ttl=300)
def query(sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, get_engine())


# ─── Layout ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="AQI OLAP Dashboard", layout="wide", page_icon="🌍")
st.title("🌍 AQI Data Warehouse — OLAP Dashboard")
st.caption("PH-04 · World Air Pollution 2014–2025 · MariaDB")

# Sidebar filters

st.sidebar.header("Bộ lọc")

# 1. Kiểm tra phòng thủ cho Chất ô nhiễm
pollutants = query("SELECT DISTINCT pollutant_code FROM cube_city_season ORDER BY pollutant_code")
if pollutants.empty:
    st.error("❌ Kho dữ liệu hiện tại đang trống hoặc bị cắt tỉa hết bởi Iceberg Cube!")
    st.info("💡 **Gợi ý xử lý:** Có thể do dữ liệu thử nghiệm quá ít nên không vượt qua được ngưỡng `min_sup = 100`. Bạn hãy mở file `etl_pipeline.py`, sửa dòng `MIN_SUP = 100` thành `MIN_SUP = 1` hoặc `5`, sau đó chạy lại lệnh `python notebooks/etl_pipeline.py` rồi reload lại trang này.")
    st.stop() # Dừng chương trình tại đây để không bị crash giao diện

poll_sel = st.sidebar.selectbox("Chất ô nhiễm", pollutants["pollutant_code"].tolist(), index=0)

seasons_opt = ["Tất cả", "dry", "rainy"]
season_sel  = st.sidebar.selectbox("Mùa", seasons_opt)

# 2. Kiểm tra phòng thủ cho cấu trúc Năm để tránh lỗi RangeError
years = query("SELECT DISTINCT year FROM cube_city_month ORDER BY year")
year_list = years["year"].tolist() if not years.empty else []

if len(year_list) == 0:
    # Trường hợp không có dữ liệu năm nào
    year_range = (2014, 2025) 
elif len(year_list) == 1:
    # Trường hợp chỉ có đúng 1 năm dữ liệu (Tránh lỗi min == max của select_slider)
    st.sidebar.info(f"Đang phân tích dữ liệu năm: {year_list[0]}")
    year_range = (year_list[0], year_list[0])
else:
    # Trường hợp có từ 2 năm trở lên -> Hiển thị thanh trượt bình thường
    year_range = st.sidebar.select_slider(
        "Khoảng năm phân tích",
        options=year_list,
        value=(min(year_list), max(year_list))
    )

# ══════════════════════════════════════════════════════════════════════════
# ROW 1: KPI Cards
# ══════════════════════════════════════════════════════════════════════════
kpi = query(f"""
    SELECT
        COUNT(DISTINCT CONCAT(city,'|',country)) AS n_cities,
        ROUND(AVG(avg_aqi),1)                    AS global_avg,
        MAX(max_aqi)                             AS global_max,
        SUM(unhealthy_cnt)                       AS total_unhealthy
    FROM cube_city_season
    WHERE pollutant_code = '{poll_sel}'
""").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Thành phố",       f"{int(kpi['n_cities']):,}")
c2.metric("AQI trung bình",  kpi["global_avg"])
c3.metric("AQI cao nhất",    kpi["global_max"])
c4.metric("Giờ không lành",  f"{int(kpi['total_unhealthy']):,}")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# ROW 2: Top Cities + Xu hướng
# ══════════════════════════════════════════════════════════════════════════
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏙️ Top 15 thành phố ô nhiễm nhất")
    season_filter = f"AND season = '{season_sel}'" if season_sel != "Tất cả" else ""
    top_cities = query(f"""
        SELECT city, country, ROUND(AVG(avg_aqi),1) AS avg_aqi
        FROM cube_city_season
        WHERE pollutant_code = '{poll_sel}' {season_filter}
        GROUP BY city, country
        ORDER BY avg_aqi DESC
        LIMIT 15
    """)
    top_cities["label"] = top_cities["city"] + " (" + top_cities["country"] + ")"
    fig = px.bar(top_cities.sort_values("avg_aqi"),
                 x="avg_aqi", y="label", orientation="h",
                 color="avg_aqi", color_continuous_scale="Reds",
                 labels={"avg_aqi": "AQI trung bình", "label": ""},
                 height=450)
    fig.update_layout(coloraxis_showscale=False, margin=dict(l=0))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📈 Xu hướng AQI theo năm")
    trend = query(f"""
        SELECT year, ROUND(AVG(avg_aqi),1) AS avg_aqi
        FROM cube_city_month
        WHERE pollutant_code = '{poll_sel}'
          AND year BETWEEN {year_range[0]} AND {year_range[1]}
        GROUP BY year
        ORDER BY year
    """)
    fig2 = px.line(trend, x="year", y="avg_aqi",
                   markers=True,
                   labels={"avg_aqi": "AQI trung bình", "year": "Năm"},
                   height=450)
    fig2.update_traces(line_color="#e74c3c", line_width=2)
    st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# ROW 3: Drill-down + So sánh mùa
# ══════════════════════════════════════════════════════════════════════════
col3, col4 = st.columns(2)

with col3:
    st.subheader("🔍 Drill-down theo thành phố")
    city_list = query("SELECT DISTINCT city FROM cube_city_season ORDER BY city")
    city_sel  = st.selectbox("Chọn thành phố", city_list["city"].tolist())
    city_data = query(f"""
        SELECT year, month,
               ROUND(AVG(avg_aqi),1) AS avg_aqi
        FROM cube_city_month
        WHERE city = '{city_sel}' AND pollutant_code = '{poll_sel}'
        GROUP BY year, month
        ORDER BY year, month
    """)
    if not city_data.empty:
        city_data["period"] = city_data["year"].astype(str) + "-" + city_data["month"].astype(str).str.zfill(2)
        fig3 = px.area(city_data, x="period", y="avg_aqi",
                       labels={"avg_aqi": "AQI", "period": "Tháng"},
                       height=350)
        fig3.update_traces(fillcolor="rgba(231,76,60,0.2)", line_color="#e74c3c")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Không có dữ liệu cho thành phố này.")

with col4:
    st.subheader("☀️🌧️ So sánh mùa khô vs mưa")
    season_cmp = query(f"""
        SELECT season,
               ROUND(AVG(avg_aqi),1) AS avg_aqi,
               MAX(max_aqi)          AS max_aqi,
               SUM(unhealthy_cnt)    AS unhealthy_cnt
        FROM cube_city_season
        WHERE pollutant_code = '{poll_sel}'
        GROUP BY season
    """)
    season_cmp["season_label"] = season_cmp["season"].map({"dry":"Mùa khô","rainy":"Mùa mưa"})
    fig4 = px.bar(season_cmp, x="season_label", y="avg_aqi",
                  color="season_label",
                  color_discrete_map={"Mùa khô":"#e67e22","Mùa mưa":"#3498db"},
                  labels={"avg_aqi": "AQI trung bình", "season_label": ""},
                  text="avg_aqi", height=350)
    fig4.update_traces(textposition="outside")
    fig4.update_layout(showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# ROW 4: Bảng OLAP chi tiết
# ══════════════════════════════════════════════════════════════════════════
st.subheader("📋 Bảng dữ liệu OLAP (Slice & Dice)")
season_filter2 = f"AND season = '{season_sel}'" if season_sel != "Tất cả" else ""
table_data = query(f"""
    SELECT city, country, season,
           reading_count, avg_aqi, max_aqi, unhealthy_cnt
    FROM cube_city_season
    WHERE pollutant_code = '{poll_sel}' {season_filter2}
    ORDER BY avg_aqi DESC
    LIMIT 100
""")
table_data.columns = ["Thành phố","Quốc gia","Mùa","Số bản ghi","AQI TB","AQI Max","Giờ ô nhiễm"]
st.dataframe(table_data, use_container_width=True, hide_index=True)

st.caption(f"Dữ liệu từ: cube_city_season | Chất: {poll_sel} | batch mới nhất")
