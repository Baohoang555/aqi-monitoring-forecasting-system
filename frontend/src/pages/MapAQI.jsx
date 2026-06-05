import { useEffect, useState } from "react"
import axios from "axios"
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet"
import "leaflet/dist/leaflet.css"

const API = "http://localhost:8000"

const CITY_COORDS = {
  "Hanoi":           [21.0285, 105.8542],
  "Ho Chi Minh City":[10.8231, 106.6297],
  "Da Nang":         [16.0544, 108.2022],
  "Bangkok":         [13.7563, 100.5018],
  "Beijing":         [39.9042, 116.4074],
  "Delhi":           [28.6139,  77.2090],
  "Tokyo":           [35.6762, 139.6503],
  "Seoul":           [37.5665, 126.9780],
  "Jakarta":         [-6.2088, 106.8456],
  "Mumbai":          [19.0760,  72.8777],
}

const AQI_LEGEND = [
  { label: "Good",           color: "#00E400", range: "0–50"   },
  { label: "Satisfactory",   color: "#92D050", range: "51–100" },
  { label: "Moderate",       color: "#FFFF00", range: "101–150"},
  { label: "Unhealthy",      color: "#FF7E00", range: "151–200"},
  { label: "Very Unhealthy", color: "#FF0000", range: "201–300"},
  { label: "Hazardous",      color: "#7E0023", range: "300+"   },
]

const getColor = (pm25) => {
  if (pm25 == null) return "#555";
  if (pm25 <= 50)  return "#00E400"; // Good - Xanh lá
  if (pm25 <= 100) return "#92D050"; // Satisfactory - Xanh nhạt
  if (pm25 <= 150) return "#FFFF00"; // Moderate - Vàng
  if (pm25 <= 200) return "#FF7E00"; // Unhealthy - Cam
  if (pm25 <= 300) return "#FF0000"; // Very Unhealthy - Đỏ
  return "#7E0023";                  // Hazardous - Tím sẫm
}

const getLabel = (pm25) => {
  if (pm25 == null) return "N/A";
  if (pm25 <= 50)  return "Good";
  if (pm25 <= 100) return "Satisfactory";
  if (pm25 <= 150) return "Moderate";
  if (pm25 <= 200) return "Unhealthy";
  if (pm25 <= 300) return "Very Unhealthy";
  return "Hazardous";
}

export default function MapAQI() {
  const [cities,   setCities]   = useState([])   
  const [cityData, setCityData] = useState({})   
  const [markers,  setMarkers]  = useState([])   
  const [loading,  setLoading]  = useState(true)

  // 1. Tải danh sách thành phố vệ tinh từ DB một lần duy nhất ([])
  useEffect(() => {
    axios.get(`${API}/cities`, { timeout: 5000 })
      .then(r => {
        const list = r.data?.data ?? r.data ?? []
        setCities(Array.isArray(list) && list.length > 0 ? list : Object.keys(CITY_COORDS))
      })
      .catch(() => {
        setCities(Object.keys(CITY_COORDS))
      })
  }, [])

  // 2. Tải thông tin tọa độ địa lý và chỉ số ô nhiễm thời gian thực
  useEffect(() => {
    if (cities.length === 0) return
    setLoading(true)

    Promise.allSettled(
      cities.map(cityName =>
        axios.get(`${API}/current/${encodeURIComponent(cityName)}`, { timeout: 5000 })
          .then(r => {
            let payload = r.data
            if (payload && payload.data) payload = payload.data
            return { cityName, data: payload }
          })
          .catch(() => ({ cityName, data: null }))
      )
    ).then(results => {
      const map = {}
      const built = []

      results.forEach(res => {
        if (res.status === "fulfilled") {
          const { cityName, data } = res.value
          map[cityName] = data

          const fallback = CITY_COORDS[cityName] ?? null
          const lat = data?.lat ?? data?.latitude  ?? fallback?.[0] ?? null
          const lon = data?.lon ?? data?.longitude ?? fallback?.[1] ?? null
          
          if (lat !== null && lon !== null) {
            built.push({ name: cityName, lat, lon, data })
          }
        }
      })

      setCityData(map)
      setMarkers(built)
      setLoading(false)
    })
  }, [cities])

  return (
    <div style={{ display: "flex", gap: 16, height: "calc(100vh - 48px)" }}>
      <div style={{ flex: 1, borderRadius: 12, overflow: "hidden", border: "1px solid #2A2D3A" }}>
        <MapContainer center={[20, 105]} zoom={4} style={{ height: "100%", width: "100%" }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="© OpenStreetMap" />
          {markers.map(({ name, lat, lon, data }) => {
            const color = getColor(data?.pm25)
            return (
              <CircleMarker key={name} center={[lat, lon]} radius={14} pathOptions={{ color: "white", fillColor: color, fillOpacity: 0.9, weight: 2 }}>
                <Popup>
                  <div style={{ minWidth: 170, color: "#000" }}>
                    <b>{name}</b><br />
                    PM2.5: <b>{data?.pm25 ?? "N/A"} μg/m³</b><br />
                    PM10: {data?.pm10 ?? "N/A"} μg/m³<br />
                    NO₂: {data?.no2 ?? "N/A"} μg/m³<br />
                    Nhiệt độ: {data?.temperature ?? data?.temp ?? "N/A"} °C<br />
                    Độ ẩm: {data?.humidity ?? "N/A"}%<br />
                    <span style={{ display: "inline-block", marginTop: 6, padding: "2px 8px", borderRadius: 4, background: color, color: ["#FFFF00","#92D050","#00E400"].includes(color) ? "#000" : "#fff", fontSize: 12, fontWeight: 700 }}>
                      {getLabel(data?.pm25)}
                    </span>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>

      <div style={{ width: 230, background: "#1A1D27", borderRadius: 12, border: "1px solid #2A2D3A", padding: 20, display: "flex", flexDirection: "column", gap: 20, overflowY: "auto" }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
            {loading ? "Đang tải..." : `${markers.length} / ${cities.length} trạm`}
          </div>
          {cities.map(cityName => {
            const d = cityData[cityName]
            const color = getColor(d?.pm25)
            return (
              <div key={cityName} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 0", borderBottom: "1px solid #2A2D3A" }}>
                <span style={{ fontSize: 12, color: "#D3D1C7" }}>{cityName}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color }}>{loading ? "..." : (d?.pm25 ?? "N/A")}</span>
              </div>
            )
          })}
        </div>

        <div>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>AQI Legend</div>
          {AQI_LEGEND.map(l => (
            <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
              <div style={{ width: 14, height: 14, borderRadius: "50%", background: l.color, flexShrink: 0 }} />
              <div style={{ fontSize: 12 }}>
                <div style={{ color: "white" }}>{l.label}</div>
                <div style={{ color: "#8B8FA8" }}>{l.range}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}