import { useEffect, useMemo, useState } from "react"
import axios from "axios"
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
  Legend,
  LabelList,
  Cell,
} from "recharts"

const API = import.meta.env.VITE_API_URL || "https://2870w5x1-8000.asse.devtunnels.ms/"

const Card = ({ title, children, style }) => (
  <div style={{
    background: "#1A1D27",
    borderRadius: 16,
    padding: "24px 28px",
    border: "1px solid #2A2D3A",
    ...style,
  }}>
    <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 20, color: "#E2E4F0", letterSpacing: 0.2 }}>
      {title}
    </div>
    {children}
  </div>
)

const KPI = ({ label, value, color }) => (
  <div style={{
    flex: 1,
    minWidth: 160,
    background: "#1A1D27",
    borderRadius: 16,
    padding: "20px 24px",
    border: "1px solid #2A2D3A",
  }}>
    <div style={{ fontSize: 12, color: "#8B8FA8", textTransform: "uppercase", letterSpacing: 1 }}>{label}</div>
    <div style={{
      fontSize: 32,
      fontWeight: 800,
      marginTop: 10,
      color: color || "#FFFFFF",
      lineHeight: 1.1,
      letterSpacing: -0.5,
    }}>
      {value ?? "N/A"}
    </div>
  </div>
)

const toNumber = (value) => {
  if (value == null) return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

const formatAQI = (value) => {
  const n = toNumber(value)
  if (n == null) return "N/A"
  return n.toFixed(1)
}

const POLLUTANT_COLORS = {
  "PM2.5": "#FF6B6B",
  "PM10": "#FF8E53",
  "NO2": "#FFC75F",
  "SO2": "#A8E6CF",
  "CO": "#88D8B0",
  "O3": "#7EC8E3",
}

const getPollutantColor = (code) => POLLUTANT_COLORS[code] || "#4F8EF7"

const fetchSlice = async () => {
  const res = await axios.get(`${API}/olap/slice`)
  return res.data?.data || []
}

const fetchSliceByYear = async (city) => {
  if (!city) return []
  const res = await axios.get(`${API}/olap/slice-by-year?city=${encodeURIComponent(city)}`)
  return res.data?.data || []
}

const normalizeRows = (rows) =>
  (Array.isArray(rows) ? rows : [])
    .map((row) => ({
      city: row.city ?? "Unknown",
      season: row.season ?? "Unknown",
      average_aqi: toNumber(row.average_aqi ?? row.avg_aqi),
      records: toNumber(row.records ?? row.reading_count) ?? 0,
      country: row.country ?? "",
      pollutant_code: row.pollutant_code ?? "Unknown",
      max_aqi: toNumber(row.max_aqi),
      avg_conc: toNumber(row.avg_conc),
      unhealthy_cnt: toNumber(row.unhealthy_cnt),
      year: toNumber(row.year),  // ← thêm dòng này
    }))
    .filter((row) => row.average_aqi != null)

const weightedGroup = (rows, keyGetter, labelName) => {
  const map = new Map()
  for (const row of rows) {
    const key = keyGetter(row)
    const weight = row.records > 0 ? row.records : 1
    const current = map.get(key) || { sum: 0, weight: 0 }
    current.sum += row.average_aqi * weight
    current.weight += weight
    map.set(key, current)
  }
  return Array.from(map.entries())
    .map(([key, item]) => ({
      [labelName]: key,
      average_aqi: item.weight ? item.sum / item.weight : null,
      records: item.weight,
    }))
    .filter((row) => row.average_aqi != null)
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: "rgba(15, 17, 23, 0.96)",
      border: "1px solid #2A2D3A",
      borderRadius: 12,
      padding: "10px 14px",
      fontSize: 13,
      boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
    }}>
      <div style={{ color: "#8B8FA8", marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || "#fff", fontWeight: 600 }}>
          {p.name}: {formatAQI(p.value)}
        </div>
      ))}
    </div>
  )
}
export default function Visualization() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [selectedCity, setSelectedCity] = useState("")

  const loadData = async () => {
    setLoading(true)
    setError("")
    try {
      const data = await fetchSlice()
      const normalized = normalizeRows(data)
      setRows(normalized)
      if (!selectedCity && normalized.length > 0) {
        setSelectedCity(normalized[0].city)
      }
    } catch (err) {
      console.error(err)
      setError("Không tải được dữ liệu OLAP từ /olap/slice.")
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])


  const [drillRows, setDrillRows] = useState([])
  const [drillLoading, setDrillLoading] = useState(false)

  useEffect(() => {
    if (!selectedCity) return
    setDrillLoading(true)
    fetchSliceByYear(selectedCity)
      .then(data => setDrillRows(normalizeRows(data)))
      .finally(() => setDrillLoading(false))
  }, [selectedCity])

  // Group by city (weighted avg across all pollutants)
  const cityAgg = useMemo(() =>
    weightedGroup(rows, (r) => r.city, "city")
      .sort((a, b) => (b.average_aqi || 0) - (a.average_aqi || 0))
  , [rows])

  // Group by season
  const seasonAgg = useMemo(() =>
    weightedGroup(rows, (r) => r.season, "season")
      .sort((a, b) => {
        const order = { dry: 1, rainy: 2, Unknown: 99 }
        return (order[a.season] || 99) - (order[b.season] || 99)
      })
  , [rows])

  const drilldownAgg = useMemo(() => {
    const map = new Map()
    for (const row of drillRows) {  // ← đổi rows thành drillRows
      const key = row.year
      if (!map.has(key)) map.set(key, { year: key, dry: null, rainy: null, dryW: 0, rainyW: 0 })
      const entry = map.get(key)
      const w = row.records > 0 ? row.records : 1
      if (row.season === "dry") {
        entry.dry = ((entry.dry || 0) * entry.dryW + row.average_aqi * w) / (entry.dryW + w)
        entry.dryW += w
      } else if (row.season === "rainy") {
        entry.rainy = ((entry.rainy || 0) * entry.rainyW + row.average_aqi * w) / (entry.rainyW + w)
        entry.rainyW += w
      }
    }
    return Array.from(map.values())
      .filter(r => r.year != null)
      .sort((a, b) => a.year - b.year)
  }, [drillRows]) 

  // Deduplicated table: group by city + season
  const summaryTable = useMemo(() => {
    const map = new Map()
    for (const row of rows) {
      const key = `${row.city}__${row.season}`
      if (!map.has(key)) {
        map.set(key, {
          city: row.city,
          season: row.season,
          average_aqi: row.average_aqi,
          records: row.records,
          country: row.country,  // lấy thẳng từ row, không qua weightedGroup
        })
      }
    }
    return Array.from(map.values()).sort((a, b) => (b.average_aqi || 0) - (a.average_aqi || 0))
  }, [rows])

  const kpis = useMemo(() => {
    const totalCities = cityAgg.length
    const totalRecords = rows.reduce((sum, row) => sum + (row.records || 0), 0)
    const totalWeight = rows.reduce((sum, row) => sum + (row.records || 1), 0)
    const avgAQI = rows.length > 0
      ? rows.reduce((sum, row) => sum + row.average_aqi * (row.records || 1), 0) / totalWeight
      : null
    const maxAQI = rows.length > 0 ? Math.max(...rows.map((r) => r.average_aqi || 0)) : null
    return { totalCities, totalRecords, avgAQI, maxAQI }
  }, [cityAgg.length, rows])

  useEffect(() => {
    if (!selectedCity && cityAgg.length > 0) setSelectedCity(cityAgg[0].city)
  }, [cityAgg, selectedCity])

  if (loading) return (
    <div style={{ color: "#8B8FA8", padding: 40, textAlign: "center", fontSize: 15 }}>
      Đang tải dữ liệu...
    </div>
  )

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24, padding: "4px 0 40px" }}>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 26, fontWeight: 800, letterSpacing: -0.5 }}>
            Trực quan hóa dữ liệu AQI
          </h2>
          <div style={{ color: "#8B8FA8", fontSize: 13, marginTop: 4 }}>
            Dữ liệu từ {kpis.totalCities.toLocaleString()} thành phố · {kpis.totalRecords.toLocaleString("en-US")} bản ghi
          </div>
        </div>
        <button onClick={loadData} style={{
          background: "#4F8EF7",
          color: "white",
          border: "none",
          borderRadius: 10,
          padding: "10px 20px",
          cursor: "pointer",
          fontWeight: 700,
          fontSize: 14,
        }}>
          ↻ Tải lại
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          background: "#2A1D1D",
          border: "1px solid #5C2B2B",
          color: "#FFB4B4",
          padding: "12px 16px",
          borderRadius: 12,
          fontSize: 14,
        }}>
          {error}
        </div>
      )}

      {/* KPIs */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <KPI label="Số thành phố" value={kpis.totalCities.toLocaleString()} color="#4F8EF7" />
        <KPI label="AQI trung bình" value={formatAQI(kpis.avgAQI)} color="#FF8E53" />
        <KPI label="AQI cao nhất" value={formatAQI(kpis.maxAQI)} color="#FF6B6B" />
        <KPI label="Tổng bản ghi" value={kpis.totalRecords.toLocaleString("en-US")} color="#A8E6CF" />
      </div>

      {/* Top cities + Season */}
      <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr", gap: 20 }}>
        <Card title="🏙️ Top 15 thành phố ô nhiễm nhất">
          <div style={{ width: "100%", height: 400 }}>
            <ResponsiveContainer>
              <BarChart
                data={cityAgg.slice(0, 15).reverse()}
                layout="vertical"
                margin={{ top: 4, right: 60, left: 10, bottom: 4 }}
              >
                <CartesianGrid stroke="#2A2D3A" strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" stroke="#8B8FA8" fontSize={12} />
                <YAxis type="category" dataKey="city" stroke="#8B8FA8" width={130} fontSize={12} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(0,0,0,0.12)" }} />
                <Bar dataKey="average_aqi" fill="#4F8EF7" radius={[0, 8, 8, 0]} maxBarSize={22}>
                  <LabelList dataKey="average_aqi" position="right" fill="#C0C4D8" fontSize={12}
                    formatter={(v) => formatAQI(v)} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="🌦️ AQI theo mùa">
          <div style={{ width: "100%", height: 400 }}>
            <ResponsiveContainer>
              <BarChart data={seasonAgg} margin={{ top: 20, right: 20, left: 0, bottom: 20 }}>
                <CartesianGrid stroke="#2A2D3A" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="season" stroke="#8B8FA8" fontSize={13} />
                <YAxis stroke="#8B8FA8" fontSize={12} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(0,0,0,0.12)" }} />
                <Bar dataKey="average_aqi" radius={[10, 10, 0, 0]} maxBarSize={80}>
                  {seasonAgg.map((entry, i) => (
                    <Cell key={i} fill={i === 0 ? "#FF8E53" : "#4F8EF7"} />
                  ))}
                  <LabelList dataKey="average_aqi" position="top" fill="#C0C4D8" fontSize={13}
                    formatter={(v) => formatAQI(v)} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Pollutant chart + selector */}
      <Card title={`🔍 Drill-down AQI theo thành phố — ${selectedCity}`}>
        <div style={{ marginBottom: 16 }}>
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            style={{
              background: "#0F1117", color: "white",
              border: "1px solid #2A2D3A", padding: "9px 14px",
              borderRadius: 10, minWidth: 240, fontSize: 14,
            }}
          >
            {cityAgg.map((row) => (
              <option key={row.city} value={row.city}>{row.city}</option>
            ))}
          </select>
        </div>

        {drillLoading ? (
          <div style={{ color: "#8B8FA8", textAlign: "center", padding: 40 }}>Đang tải...</div>
        ) : (
          <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            <LineChart data={drilldownAgg} margin={{ top: 10, right: 40, left: 0, bottom: 10 }}>
              <CartesianGrid stroke="#2A2D3A" strokeDasharray="3 3" />
              <XAxis dataKey="year" stroke="#8B8FA8" fontSize={13} />
              <YAxis stroke="#8B8FA8" fontSize={12} />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#3A3D4A" }} wrapperStyle={{ outline: "none" }} />
              <Legend wrapperStyle={{ color: "#8B8FA8", fontSize: 13 }} />
              <Line type="monotone" dataKey="dry" name="Mùa khô" stroke="#FF8E53"
                strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              <Line type="monotone" dataKey="rainy" name="Mùa mưa" stroke="#4F8EF7"
                strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        )}
      </Card>

      {/* Summary Table */}
      <Card title="📋 Bảng tổng hợp OLAP">
        <div style={{
          height: 420,
          overflowY: "auto",
          borderRadius: 10,
          border: "1px solid #2A2D3A",
          scrollbarWidth: "thin",
          scrollbarColor: "#3A3D4A #0F1117",
        }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{
                position: "sticky", top: 0,
                background: "#0F1117",
                borderBottom: "2px solid #2A2D3A",
                zIndex: 1,
              }}>
                {["Thành phố", "Quốc gia", "Mùa", "AQI trung bình", "Số bản ghi"].map((h) => (
                  <th key={h} style={{
                    textAlign: "left", padding: "12px 16px",
                    color: "#8B8FA8", fontWeight: 600,
                    fontSize: 12, textTransform: "uppercase", letterSpacing: 0.8,
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {summaryTable.map((row, idx) => (
                <tr key={idx}
                  style={{ borderBottom: "1px solid #1F2230", transition: "background 0.15s" }}
                  onMouseEnter={(e) => e.currentTarget.style.background = "#1A1D2F"}
                  onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                >
                  <td style={{ padding: "11px 16px", fontWeight: 600 }}>{row.city}</td>
                  <td style={{ padding: "11px 16px", color: "#A0A4B8" }}>{row.country || "-"}</td>
                  <td style={{ padding: "11px 16px" }}>
                    <span style={{
                      background: row.season === "dry" ? "#FF8E5320" : "#4F8EF720",
                      color: row.season === "dry" ? "#FF8E53" : "#4F8EF7",
                      padding: "3px 10px", borderRadius: 20,
                      fontSize: 12, fontWeight: 600,
                    }}>
                      {row.season === "dry" ? "🌤 dry" : "🌧 rainy"}
                    </span>
                  </td>
                  <td style={{ padding: "11px 16px", fontWeight: 700, color: "#E2E4F0" }}>
                    {formatAQI(row.average_aqi)}
                  </td>
                  <td style={{ padding: "11px 16px", color: "#8B8FA8" }}>
                    {(row.records || 0).toLocaleString("en-US")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

    </div>
  )
}