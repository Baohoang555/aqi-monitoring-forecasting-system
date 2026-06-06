import { useEffect, useState } from "react"
import axios from "axios"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartsTooltip, ResponsiveContainer, Cell
} from "recharts"

const API = "http://localhost:8000"
const FALLBACK_CITIES = ["Hanoi", "Ho Chi Minh City", "Da Nang"]

const KPICard = ({ label, value, color, sub }) => (
  <div style={{ background: "#1A1D27", borderRadius: 12, padding: "16px 20px", flex: 1, minWidth: 160, border: "1px solid #2A2D3A" }}>
    <div style={{ fontSize: 12, color: "#8B8FA8", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.8 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700, color: color || "white" }}>{value != null ? value : "N/A"}</div>
    {sub && <div style={{ fontSize: 12, color: "#8B8FA8", marginTop: 4 }}>{sub}</div>}
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
  if (v <= 100) return "Moderate"
  if (v <= 150) return "Unhealthy for Sensitive"
  if (v <= 200) return "Unhealthy"
  return "Hazardous"
}

const getCategoryColor = (category) => {
  if (!category) return "#8B8FA8"
  const c = category.toLowerCase()
  if (c.includes("good"))       return "#00E400"
  if (c.includes("moderate"))   return "#92D050"
  if (c.includes("sensitive"))  return "#FFFF00"
  if (c.includes("unhealthy"))  return "#FF7E00"
  if (c.includes("very"))       return "#8B00FF"
  if (c.includes("hazardous"))  return "#FF0000"
  return "#8B8FA8"
}

const MODEL_COLORS = {
  LightGBM: "#4F8EF7",
  XGBoost: "#FF8E53",
  DecisionTree: "#A8E6CF",
  RandomForest: "#FFC75F",
  ExtraTrees: "#C3A6FF",
  LogisticRegression_SGD: "#FF6B6B",
}

export default function Dashboard() {
  const [cities, setCities] = useState([])
  const [cityData, setCityData] = useState({})
  const [selected, setSelected] = useState("")
  const [loading, setLoading] = useState(true)
  const [prediction, setPrediction] = useState(null)
  const [predLoading, setPredLoading] = useState(false)
  const [weather, setWeather] = useState(null)
  const [modelEval, setModelEval] = useState([])
  const [bestModel, setBestModel] = useState(null)

  const unwrapPayload = (obj) => {
    let current = obj
    if (current?.data) current = current.data
    if (current?.success && current?.data) current = current.data
    return (current && typeof current === "object" && !Array.isArray(current)) ? current : {}
  }

  // Load cities
  useEffect(() => {
    axios.get(`${API}/cities`).then(r => {
      let list = r.data?.data ?? r.data ?? []
      if (list?.success && list?.data) list = list.data
      setCities(Array.isArray(list) && list.length ? list : FALLBACK_CITIES)
      setSelected((Array.isArray(list) && list[0]) || "Hanoi")
    }).catch(() => { setCities(FALLBACK_CITIES); setSelected("Hanoi") })
  }, [])

  // Load all stations
  useEffect(() => {
    if (!cities.length) return
    setLoading(true)
    axios.get(`${API}/current-all-stations`, { timeout: 60000 })
      .then(r => setCityData(unwrapPayload(r.data)))
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [cities])

  // Load model evaluation
  useEffect(() => {
    axios.get(`${API}/model-evaluation`).then(r => {
      const data = r.data?.data || []
      setModelEval(data)
      // Tìm model tốt nhất theo Accuracy
      const accuracyRows = data.filter(d => d.metric === "Accuracy")
      if (accuracyRows.length) {
        const best = accuracyRows.reduce((a, b) => a.value > b.value ? a : b)
        setBestModel(best)
      }
    }).catch(() => {})
  }, [])

  // Khi city thay đổi: predict + weather
  useEffect(() => {
    if (!selected || !cityData || !cityData[selected]) return
    const cityInfo = cityData[selected]
    if (!cityInfo.pm25 && !cityInfo.pm10 && !cityInfo.no2) return

    // Reset khi đổi city
    setPrediction(null)
    setWeather(null)
    setPredLoading(true)

    const now = new Date()
    const month = now.getMonth() + 1
    const monthSin = Math.sin(2 * Math.PI * month / 12)
    const monthCos = Math.cos(2 * Math.PI * month / 12)
    const no2_nox_ratio = cityInfo.no2 && cityInfo.pm25
      ? cityInfo.no2 / (cityInfo.no2 + cityInfo.pm25)
      : 0.5

    axios.post(`${API}/predict`, {
      city: selected,
      pm25: cityInfo.pm25,
      pm10: cityInfo.pm10,
      no2: cityInfo.no2,
      temperature: cityInfo.temperature || 27,
      humidity: cityInfo.humidity || 65,
      features: {
        pm25: cityInfo.pm25 || 0,
        pm10: cityInfo.pm10 || 0,
        no2: cityInfo.no2 || 0,
        temperature: cityInfo.temperature || 27,
        humidity: cityInfo.humidity || 65,
        month: month,
        month_sin: monthSin,
        month_cos: monthCos,
        no2_nox_ratio: no2_nox_ratio,
        division: 0,
      }
    }).then(r => setPrediction(r.data?.data || null))
      .catch(() => setPrediction(null))
      .finally(() => setPredLoading(false))
  }, [selected, cityData])

  const current = cityData[selected] ?? null

  // Chuẩn bị data chart model: chỉ lấy Accuracy
  const chartData = modelEval
    .filter(d => d.metric === "Accuracy")
    .sort((a, b) => b.value - a.value)
    .map(d => ({ name: d.model_name, value: Math.round(d.value * 100 * 10) / 10 }))

  const weatherIcon = (code) => {
    if (code == null) return "🌡"
    if (code === 0) return "☀️"
    if (code <= 3) return "⛅"
    if (code <= 67) return "🌧"
    if (code <= 77) return "❄️"
    return "⛈"
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Dashboard Overview</h2>
          {bestModel && (
            <div style={{ fontSize: 13, color: "#8B8FA8", marginTop: 4 }}>
              🏆 Model tốt nhất: <span style={{ color: MODEL_COLORS[bestModel.model_name] || "#4F8EF7", fontWeight: 600 }}>
                {bestModel.model_name}
              </span> — Accuracy {(bestModel.value * 100).toFixed(1)}%
            </div>
          )}
        </div>
        <select value={selected} onChange={e => setSelected(e.target.value)}
          style={{ background: "#1A1D27", border: "1px solid #2A2D3A", borderRadius: 8, padding: "8px 12px", color: "white", minWidth: 200 }}>
          {cities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* KPI Row */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <KPICard label="PM2.5 (μg/m³)" value={loading ? "..." : current?.pm25}
          color={getAQIColor(current?.pm25)} />
        <KPICard label="PM10 (μg/m³)" value={loading ? "..." : current?.pm10}
          color="#4F8EF7" />
        <KPICard label="NO₂ (μg/m³)" value={loading ? "..." : current?.no2}
          color="#FFC75F" />
      </div>

      {/* Thời tiết + Dự báo chi tiết */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Card title="🏭 Top 5 thành phố ô nhiễm nhất">
          {Object.entries(cityData)
            .filter(([, v]) => v?.pm25 != null)
            .sort(([, a], [, b]) => b.pm25 - a.pm25)
            .slice(0, 5)
            .map(([name, v], i) => (
              <div key={name} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "10px 0", borderBottom: "1px solid #2A2D3A"
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div style={{
                    width: 24, height: 24, borderRadius: "50%",
                    background: getAQIColor(v.pm25),
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 11, fontWeight: 700, color: "#000"
                  }}>{i + 1}</div>
                  <span style={{ fontSize: 14 }}>{name}</span>
                </div>
                <span style={{ fontSize: 16, fontWeight: 700, color: getAQIColor(v.pm25) }}>
                  {v.pm25} μg/m³
                </span>
              </div>
            ))
          }
          {Object.keys(cityData).length === 0 && (
            <div style={{ color: "#8B8FA8", fontSize: 13 }}>Đang tải...</div>
          )}
        </Card>

        <Card title="🤖 Dự báo AQI từ mô hình ML">
          {predLoading ? (
            <div style={{ color: "#8B8FA8" }}>Đang dự báo...</div>
          ) : prediction ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <div style={{
                  width: 80, height: 80, borderRadius: "50%",
                  background: getCategoryColor(prediction.category),
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, fontWeight: 700, color: "#000", textAlign: "center", padding: 8
                }}>
                  {prediction.category}
                </div>
                <div>
                  <div style={{ fontSize: 13, color: "#8B8FA8" }}>Phân loại dự báo</div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: getCategoryColor(prediction.category) }}>
                    {prediction.category}
                  </div>
                  {typeof prediction.predicted_aqi === "number" && (
                    <div style={{ fontSize: 13, color: "#8B8FA8" }}>
                      AQI: {prediction.predicted_aqi.toFixed(1)}
                    </div>
                  )}
                </div>
              </div>
              <div style={{ fontSize: 12, color: "#8B8FA8", borderTop: "1px solid #2A2D3A", paddingTop: 10 }}>
                Input: PM2.5={current?.pm25} · PM10={current?.pm10} · NO₂={current?.no2}
              </div>
            </div>
          ) : (
            <div style={{ color: "#8B8FA8", fontSize: 13 }}>Chọn thành phố có đủ dữ liệu để dự báo</div>
          )}
        </Card>
      </div>

      {/* Model Performance */}
      <Card title="📊 Hiệu suất các mô hình ML (Accuracy %)">
        {chartData.length > 0 ? (
          <div style={{ width: "100%", height: 240 }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
              <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid stroke="#2A2D3A" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" stroke="#8B8FA8" fontSize={12} />
                <YAxis stroke="#8B8FA8" fontSize={12} domain={[60, 100]} unit="%" />
                <RechartsTooltip
                  contentStyle={{ 
                    backgroundColor: "#1A1D27", 
                    borderColor: "#2A2D3A",
                    color: "white",
                    borderRadius: 8,
                  }}
                  labelStyle={{ color: "white", fontWeight: 600 }}
                  itemStyle={{ color: "#4F8EF7" }}
                  cursor={{ fill: "rgba(255,255,255,0.05)" }}
                  formatter={(v) => [`${v}%`, "Accuracy"]}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={60}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={MODEL_COLORS[entry.name] || "#4F8EF7"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div style={{ color: "#8B8FA8", fontSize: 13 }}>Đang tải...</div>
        )}
        {bestModel && (
          <div style={{
            marginTop: 12, padding: "10px 14px", background: "#0F1117",
            borderRadius: 8, border: "1px solid #2A2D3A", fontSize: 13
          }}>
            🏆 <span style={{ color: MODEL_COLORS[bestModel.model_name] || "#4F8EF7", fontWeight: 600 }}>
              {bestModel.model_name}
            </span> đạt accuracy cao nhất: <strong>{(bestModel.value * 100).toFixed(1)}%</strong>
          </div>
        )}
      </Card>

    </div>
  )
}
