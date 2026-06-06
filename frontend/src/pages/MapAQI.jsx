import { useEffect, useState } from "react"
import axios from "axios"
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet"
import "leaflet/dist/leaflet.css"

const API = "http://localhost:8000"

export default function MapAQI() {
  const [cities, setCities] = useState([])
  const [cityData, setCityData] = useState({})
  const [markers, setMarkers] = useState([])
  const [loading, setLoading] = useState(true)
  const [adminStations, setAdminStations] = useState([])

  const getColor = (pm25) => {
    if (pm25 == null) return "#555"
    if (pm25 <= 50)  return "#00E400"
    if (pm25 <= 100) return "#92D050"
    if (pm25 <= 150) return "#FFFF00"
    if (pm25 <= 200) return "#FF7E00"
    return "#FF0000"
  }

  useEffect(() => {
    axios.get(`${API}/cities`).then(r => {
      let list = r.data?.data ?? r.data ?? []
      if (list && list.success && list.data) list = list.data
      setCities(Array.isArray(list) ? list : [])
    }).catch(() => setCities([]))
  }, [])

  useEffect(() => {
    axios.get(`${API}/admin/stations`)
      .then(r => setAdminStations(r.data?.data || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!Array.isArray(cities) || cities.length === 0) return
    setLoading(true)
    axios.get(`${API}/current-all-stations`, { timeout: 60000 }).then(r => {
      let current = r.data
      if (current && current.data) current = current.data
      if (current && current.success && current.data) current = current.data
      const payload = (current && typeof current === "object" && !Array.isArray(current)) ? current : {}
      setCityData(payload)
      const built = Object.entries(payload)
        .map(([name, station]) => {
          const lat = station?.lat
          const lon = station?.lon
          if (lat == null || lon == null) return null
          return { name, lat, lon, data: station }
        })
        .filter(Boolean)
      console.log(`✅ Loaded ${built.length} cities with coordinates`)
      setMarkers(built)
    }).catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [cities])

  const safeCityData = cityData && typeof cityData === "object" ? cityData : {}
  const safeCities = Array.isArray(cities) ? cities : []

  return (
    <div style={{ display: "flex", gap: 16, height: "calc(100vh - 48px)" }}>
      <div style={{ flex: 1, borderRadius: 12, overflow: "hidden", border: "1px solid #2A2D3A" }}>
        <MapContainer center={[16.04, 108.2]} zoom={5} style={{ height: "100%", width: "100%", zIndex: 0 }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

          {Array.isArray(markers) && markers.map(m => (
            <CircleMarker key={m.name} center={[m.lat, m.lon]} radius={8}
              pathOptions={{ color: "white", fillColor: getColor(m.data?.pm25), fillOpacity: 0.8 }}>
              <Popup>
                <b>{m.name}</b><br />
                PM2.5: {m.data?.pm25 ?? "N/A"}<br />
                PM10: {m.data?.pm10 ?? "N/A"}<br />
                NO₂: {m.data?.no2 ?? "N/A"}
              </Popup>
            </CircleMarker>
          ))}

          {adminStations
            .filter(s => s.status !== "Offline" && s.lat && s.lon)
            .map(s => (
              <CircleMarker
                key={`admin-${s.id}`}
                center={[s.lat, s.lon]}
                radius={10}
                pathOptions={{
                  color: s.status === "Warning" ? "#FF7E00" : "#4F8EF7",
                  fillColor: s.status === "Warning" ? "#FF7E00" : "#4F8EF7",
                  fillOpacity: 0.9,
                  weight: 2
                }}
              >
                <Popup>
                  <b>🏭 {s.id} — {s.name}</b><br />
                  Trạng thái: <b style={{ color: s.status === "Warning" ? "#FF7E00" : "#00E400" }}>{s.status}</b><br />
                  Cập nhật: {s.lastUpdate}
                </Popup>
              </CircleMarker>
            ))
          }
        </MapContainer>
      </div>

      <div style={{ width: 230, background: "#1A1D27", borderRadius: 12, padding: 20, overflowY: "auto", color: "#fff" }}>
        <div style={{ fontWeight: 600, marginBottom: 12 }}>
          {loading ? "Đang tải..." : `${markers.length} trạm`}
        </div>

        <div style={{ fontSize: 12, color: "#8B8FA8", marginBottom: 8 }}>Chú thích PM2.5:</div>
        {[
          { color: "#00E400", label: "Tốt (≤50)" },
          { color: "#92D050", label: "Trung bình (≤100)" },
          { color: "#FFFF00", label: "Kém (≤150)" },
          { color: "#FF7E00", label: "Xấu (≤200)" },
          { color: "#FF0000", label: "Nguy hiểm (>200)" },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", background: color, flexShrink: 0 }} />
            <span style={{ fontSize: 12 }}>{label}</span>
          </div>
        ))}

        <div style={{ borderTop: "1px solid #2A2D3A", marginTop: 12, paddingTop: 12 }}>
          <div style={{ fontSize: 12, color: "#8B8FA8", marginBottom: 8 }}>Trạm Admin:</div>
          {[
            { color: "#4F8EF7", label: "Active" },
            { color: "#FF7E00", label: "Warning" },
          ].map(({ color, label }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
              <div style={{ width: 12, height: 12, borderRadius: "50%", background: color, flexShrink: 0 }} />
              <span style={{ fontSize: 12 }}>{label}</span>
            </div>
          ))}
        </div>

        <div style={{ borderTop: "1px solid #2A2D3A", marginTop: 12, paddingTop: 12 }}>
          <div style={{ fontSize: 12, color: "#8B8FA8", marginBottom: 8 }}>Danh sách trạm:</div>
          {safeCities.map(c => {
            const stationInfo = safeCityData[c]
            return (
              <div key={c} style={{
                display: "flex", justifyContent: "space-between",
                padding: "5px 0", borderBottom: "1px solid #2A2D3A", fontSize: 12
              }}>
                <span style={{ color: "#D3D1C7" }}>{c}</span>
                <span style={{ color: getColor(stationInfo?.pm25), fontWeight: 700 }}>
                  {loading ? "..." : (stationInfo?.pm25 ?? "N/A")}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
