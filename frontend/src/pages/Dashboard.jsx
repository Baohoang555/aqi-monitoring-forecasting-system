import { useEffect, useState } from "react"
import axios from "axios"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, Legend, ResponsiveContainer
} from "recharts"

const API = "http://localhost:8000"

const FALLBACK_CITIES = [
  "Hanoi", "Ho Chi Minh City", "Da Nang",
  "Bangkok", "Beijing", "Delhi",
  "Tokyo", "Seoul", "Jakarta", "Mumbai",
]

const KPICard = ({ label, value, color }) => (
  <div style={{
    background: "#1A1D27", borderRadius: 12, padding: "16px 20px",
    flex: 1, minWidth: 160, border: "1px solid #2A2D3A"
  }}>
    <div style={{ fontSize: 12, color: "#8B8FA8", marginBottom: 8 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700, color: color || "white" }}>
      {value ?? "N/A"}
    </div>
  </div>
)

const Card = ({ title, children, style }) => (
  <div style={{
    background: "#1A1D27", borderRadius: 12, padding: 20,
    border: "1px solid #2A2D3A", ...style
  }}>
    <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>{title}</div>
    {children}
  </div>
)

const getAQIColor = (v) => {
  if (v == null) return "#8B8FA8"
  if (v <= 50)  return "#00E400"
  if (v <= 100) return "#92D050"
  if (v <= 150) return "#FFFF00"
  if (v <= 200) return "#FF7E00"
  if (v <= 300) return "#FF0000"
  return "#7E0023"
}

const getAQILabel = (v) => {
  if (v == null) return "N/A"
  if (v <= 50)  return "Good"
  if (v <= 100) return "Satisfactory"
  if (v <= 150) return "Moderate"
  if (v <= 200) return "Unhealthy"
  if (v <= 300) return "Very Unhealthy"
  return "Hazardous"
}

const trendData = [
  { time: "T2",  pm25: 45,  pm10: 60,  no2: 20 },
  { time: "T3",  pm25: 55,  pm10: 75,  no2: 25 },
  { time: "T4",  pm25: 80,  pm10: 110, no2: 40 },
  { time: "T5",  pm25: 119, pm10: 140, no2: 35 }, // Cập nhật khớp thực tế ảnh 1
  { time: "T6",  pm25: 65,  pm10: 90,  no2: 30 },
  { time: "T7",  pm25: 50,  pm10: 70,  no2: 22 },
  { time: "CN",  pm25: 40,  pm10: 55,  no2: 18 },
  { time: "+24h",pm25: 48,  pm10: 65,  no2: 21 },
]

export default function Dashboard() {
  const [cities,        setCities]        = useState([])
  const [cityData,      setCityData]      = useState({})
  const [selected,      setSelected]      = useState("")
  const [loadingCities, setLoadingCities] = useState(true)
  const [loadingData,   setLoadingData]   = useState(false)
  const [debugInfo,     setDebugInfo]     = useState("")
  const [chartPol,      setChartPol]      = useState("pm25")

  // 1. Tải danh sách thành phố từ DB
  useEffect(() => {
    setLoadingCities(true)
    axios.get(`${API}/cities`, { timeout: 5000 })
      .then(r => {
        let list = r.data?.data ?? r.data ?? []
        if (!Array.isArray(list)) list = FALLBACK_CITIES
        if (list.length === 0) list = FALLBACK_CITIES
        
        setCities(list)
        setSelected(list[0] || "Hanoi")
        setDebugInfo(`✅ Kết nối kho dữ liệu thành công!`)
      })
      .catch(() => {
        setCities(FALLBACK_CITIES)
        setSelected(FALLBACK_CITIES[0])
        setDebugInfo("⚠️ Sử dụng danh sách trạm dự phòng")
      })
      .finally(() => setLoadingCities(false))
  }, [])

  // 2. Tải thông số chi tiết của từng thành phố
  useEffect(() => {
    if (cities.length === 0) return
    setLoadingData(true)

    Promise.allSettled(
      cities.map(city =>
        axios.get(`${API}/current/${encodeURIComponent(city)}`, { timeout: 5000 })
          .then(r => {
            // Chốt chặn tối cao: Bóc sạch mọi tầng bao bọc của API response
            let payload = r.data;
            if (payload && payload.data) {
              payload = payload.data;
              // Nếu Backend bọc thêm 1 tầng data nữa do dùng ApiResponse model
              if (payload && payload.data) {
                payload = payload.data;
              }
            }
            return { city, data: payload };
          })
          .catch(() => ({ city, data: null }))
      )
    ).then(results => {
      const map = {}
      results.forEach(res => {
        if (res.status === "fulfilled") {
          const { city, data } = res.value
          map[city] = data
        }
      })
      setCityData(map)
      setLoadingData(false)
    })
  }, [cities])

  const current   = cityData[selected] ?? null
  const today     = new Date().toLocaleDateString("vi-VN")
  const isLoading = loadingCities || loadingData

  const shapFeatures = [
    { name: "pm25",      pct: 90 },
    { name: "pm10",      pct: 72 },
    { name: "no2",       pct: 55 },
    { name: "humidity",  pct: 40 },
    { name: "wind_speed", pct: 28 },
  ]

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Dashboard Overview</h2>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          {loadingCities ? (
            <div style={{ background: "#1A1D27", border: "1px solid #2A2D3A", borderRadius: 8, padding: "8px 16px", fontSize: 13, color: "#8B8FA8" }}>Đang tải...</div>
          ) : (
            <select
              value={selected}
              onChange={e => setSelected(e.target.value)}
              style={{
                background: "#1A1D27", border: "1px solid #2A2D3A", borderRadius: 8, padding: "8px 12px", color: "white",
                fontSize: 13, cursor: "pointer", outline: "none", minWidth: 200,
              }}
            >
              {cities.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          )}
          <div style={{ background: "#1A1D27", border: "1px solid #2A2D3A", borderRadius: 8, padding: "8px 16px", fontSize: 13, color: "#8B8FA8" }}>{today}</div>
        </div>
      </div>

      {debugInfo && (
        <div style={{ padding: "8px 14px", borderRadius: 8, fontSize: 12, background: "rgba(79,142,247,0.08)", border: "1px solid #4F8EF7", color: "#4F8EF7", fontFamily: "monospace" }}>
          {debugInfo}
        </div>
      )}

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <KPICard label="PM2.5 (μg/m³)" value={isLoading ? "..." : current?.pm25} color={getAQIColor(current?.pm25)} />
        <KPICard label="PM10 (μg/m³)" value={isLoading ? "..." : current?.pm10} color="#4F8EF7" />
        <KPICard label="NO₂ (μg/m³)" value={isLoading ? "..." : current?.no2} color="#FFFF00" />
        <KPICard label="Dự báo AQI" value={isLoading ? "..." : getAQILabel(current?.pm25)} color={getAQIColor(current?.pm25)} />
      </div>

      <Card title="Biểu đồ xu hướng & Dự báo 24h">
        <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
          {["pm25", "pm10", "no2"].map(p => (
            <button key={p} onClick={() => setChartPol(p)} style={{ padding: "6px 12px", background: chartPol === p ? "#4F8EF7" : "#2A2D3A", color: "white", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600 }}>
              {p.toUpperCase()}
            </button>
          ))}
        </div>
        <div style={{ width: "100%", height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" vertical={false} />
              <XAxis dataKey="time" stroke="#8B8FA8" fontSize={12} tickLine={false} />
              <YAxis stroke="#8B8FA8" fontSize={12} tickLine={false} axisLine={false} />
              <RechartsTooltip contentStyle={{ backgroundColor: "#1A1D27", borderColor: "#2A2D3A", borderRadius: 8, color: "#fff" }} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
              <Line type="monotone" dataKey={chartPol} stroke="#4F8EF7" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} name={`Nồng độ ${chartPol.toUpperCase()}`} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <Card title="Chỉ số Model" style={{ flex: 1, minWidth: 280 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {[
              { label: "Model", value: "Stacking Ensemble", color: "#4F8EF7" },
              { label: "Weighted F1", value: "0.989", color: "#00E400" },
              { label: "Accuracy", value: "98.91%", color: "#00E400" },
              { label: "ROC-AUC", value: "0.9996", color: "#4F8EF7" },
            ].map(m => (
              <div key={m.label} style={{ display: "flex", justifyContent: "space-between", padding: "10px 12px", background: "#0F1117", borderRadius: 8 }}>
                <span style={{ color: "#8B8FA8", fontSize: 13 }}>{m.label}</span>
                <span style={{ color: m.color, fontWeight: 600, fontSize: 13 }}>{m.value}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Panel Giải thích SHAP" style={{ flex: 2, minWidth: 320 }}>
          <div style={{ marginBottom: 16, padding: 12, background: "rgba(79,142,247,0.08)", borderRadius: 8, borderLeft: "4px solid #4F8EF7", color: "#E0E6ED", fontStyle: "italic", fontSize: 13, lineHeight: 1.6 }}>
            Chỉ số AQI chịu ảnh hưởng lớn nhất bởi <b>PM25</b> (90%), tiếp theo là PM10 và NO2.
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {shapFeatures.map(f => (
              <div key={f.name} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 90, fontSize: 12, color: "#8B8FA8" }}>{f.name.toUpperCase()}</div>
                <div style={{ flex: 1, background: "#0F1117", borderRadius: 4, height: 8 }}>
                  <div style={{ width: `${f.pct}%`, height: "100%", background: "#4F8EF7", borderRadius: 4 }} />
                </div>
                <div style={{ width: 35, fontSize: 12, color: "#8B8FA8", textAlign: "right" }}>{f.pct}%</div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {cities.length > 0 && (
        <Card title={`Tất cả ${cities.length} thành phố`}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 8 }}>
            {cities.map(city => {
              const d = cityData[city]
              const color = getAQIColor(d?.pm25)
              return (
                <div key={city} onClick={() => setSelected(city)} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", borderRadius: 8, background: selected === city ? "rgba(79,142,247,0.15)" : "#0F1117", border: `1px solid ${selected === city ? "#4F8EF7" : "#2A2D3A"}`, cursor: "pointer", transition: "all .15s" }}>
                  <span style={{ fontSize: 12, color: "#D3D1C7" }}>{city}</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color }}>{isLoading ? "..." : (d?.pm25 ?? "N/A")}</span>
                </div>
              )
            })}
          </div>
        </Card>
      )}
    </div>
  )
}