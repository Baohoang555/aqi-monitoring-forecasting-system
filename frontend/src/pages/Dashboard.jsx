import { useEffect, useState } from "react"
import axios from "axios"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, Legend, ResponsiveContainer
} from "recharts"

const API = "http://localhost:8000"
const FALLBACK_CITIES = ["Hanoi", "Ho Chi Minh City", "Da Nang"]

const KPICard = ({ label, value, color }) => (
  <div style={{ background: "#1A1D27", borderRadius: 12, padding: "16px 20px", flex: 1, minWidth: 160, border: "1px solid #2A2D3A" }}>
    <div style={{ fontSize: 12, color: "#8B8FA8", marginBottom: 8 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700, color: color || "white" }}>{value != null ? value : "N/A"}</div>
  </div>
)

const Card = ({ title, children, style }) => (
  <div style={{ background: "#1A1D27", borderRadius: 12, padding: 20, border: "1px solid #2A2D3A", ...style }}>
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
  return "#FF0000"
}

const getAQILabel = (v) => {
  if (v == null) return "N/A"
  if (v <= 50)  return "Good"
  if (v <= 100) return "Satisfactory"
  if (v <= 150) return "Moderate"
  return "Unhealthy"
}

const trendData = [
  { time: "T2", pm25: 45, pm10: 60, no2: 20 },
  { time: "T3", pm25: 55, pm10: 75, no2: 25 },
  { time: "T4", pm25: 80, pm10: 110, no2: 40 },
  { time: "T5", pm25: 119, pm10: 140, no2: 35 },
  { time: "T6", pm25: 65, pm10: 90, no2: 30 },
  { time: "T7", pm25: 50, pm10: 70, no2: 22 },
  { time: "CN", pm25: 40, pm10: 55, no2: 18 },
]

export default function Dashboard() {
  const [cities, setCities] = useState([])
  const [cityData, setCityData] = useState({})
  const [selected, setSelected] = useState("")
  const [loading, setLoading] = useState(true)

  // Hàm bóc tách dữ liệu đa tầng phòng thủ độc quyền
  const unwrapPayload = (obj) => {
    let current = obj;
    if (current && current.data) current = current.data;
    if (current && current.success && current.data) current = current.data;
    if (current && current.success && current.data) current = current.data;
    return (current && typeof current === 'object' && !Array.isArray(current)) ? current : {};
  };

  useEffect(() => {
    axios.get(`${API}/cities`).then(r => {
      let list = r.data?.data ?? r.data ?? [];
      if (list && list.success && list.data) list = list.data;
      setCities(Array.isArray(list) && list.length ? list : FALLBACK_CITIES)
      setSelected(list[0] || "Hanoi")
    }).catch(() => setCities(FALLBACK_CITIES))
  }, [])

  useEffect(() => {
    if (cities.length === 0) return
    setLoading(true)
    axios.get(`${API}/current-all-stations`, { timeout: 15000 })
      .then(r => {
        const cleanData = unwrapPayload(r.data);
        setCityData(cleanData);
      })
      .catch(err => console.error("Lỗi kết nối API:", err))
      .finally(() => setLoading(false))
  }, [cities])

  const safeCityData = cityData && typeof cityData === 'object' ? cityData : {};
  const current = safeCityData[selected] ?? null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Dashboard Overview</h2>
        <select value={selected} onChange={e => setSelected(e.target.value)} style={{ background: "#1A1D27", border: "1px solid #2A2D3A", borderRadius: 8, padding: "8px 12px", color: "white", minWidth: 200 }}>
          {Array.isArray(cities) && cities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <KPICard label="PM2.5 (μg/m³)" value={loading ? "..." : current?.pm25} color={getAQIColor(current?.pm25)} />
        <KPICard label="PM10 (μg/m³)" value={loading ? "..." : current?.pm10} color="#4F8EF7" />
        <KPICard label="NO₂ (μg/m³)" value={loading ? "..." : current?.no2} color="#FFFF00" />
        <KPICard label="Dự báo AQI" value={loading ? "..." : getAQILabel(current?.pm25)} color={getAQIColor(current?.pm25)} />
      </div>

      <Card title="Biểu đồ xu hướng & Dự báo 24h">
        <div style={{ width: "100%", height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" vertical={false} />
              <XAxis dataKey="time" stroke="#8B8FA8" />
              <YAxis stroke="#8B8FA8" />
              <RechartsTooltip contentStyle={{ backgroundColor: "#1A1D27", borderColor: "#2A2D3A" }} />
              <Line type="monotone" dataKey="pm25" stroke="#4F8EF7" strokeWidth={3} name="Nồng độ PM2.5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}