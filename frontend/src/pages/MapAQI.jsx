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

  const getColor = (pm25) => {
    if (pm25 == null) return "#555"
    if (pm25 <= 50)  return "#00E400"
    if (pm25 <= 100) return "#92D050"
    if (pm25 <= 150) return "#FFFF00"
    return "#FF7E00"
  }

  useEffect(() => {
    axios.get(`${API}/cities`).then(r => {
      let list = r.data?.data ?? r.data ?? [];
      if (list && list.success && list.data) list = list.data;
      setCities(Array.isArray(list) ? list : [])
    }).catch(() => setCities([]))
  }, [])

  useEffect(() => {
    if (!Array.isArray(cities) || cities.length === 0) return
    setLoading(true)

    axios.get(`${API}/current-all-stations`, { timeout: 15000 }).then(r => {
      let current = r.data;
      if (current && current.data) current = current.data;
      if (current && current.success && current.data) current = current.data;
      if (current && current.success && current.data) current = current.data;

      const payload = (current && typeof current === 'object' && !Array.isArray(current)) ? current : {};
      setCityData(payload)

      const built = Object.entries(payload)
        .map(([name, station]) => {
          const lat = station?.lat
          const lon = station?.lon
          if (lat == null || lon == null) return null
          return { name, lat, lon, data: station }
        })
        .filter(Boolean)

      setMarkers(built)
    }).catch(err => console.error(err))
    .finally(() => setLoading(false))
  }, [cities])

  const safeCityData = cityData && typeof cityData === 'object' ? cityData : {};
  const safeCities = Array.isArray(cities) ? cities : [];

  const bounds = Array.isArray(markers) && markers.length
    ? markers.map(m => [m.lat, m.lon])
    : [[20, 105]]

  return (
    <div style={{ display: "flex", gap: 16, height: "calc(100vh - 48px)" }}>
      <div style={{ flex: 1, borderRadius: 12, overflow: "hidden", border: "1px solid #2A2D3A" }}>
        <MapContainer bounds={bounds} boundsOptions={{ padding: [40, 40] }} style={{ height: "100%", width: "100%" }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {Array.isArray(markers) && markers.map(m => (
            <CircleMarker key={m.name} center={[m.lat, m.lon]} radius={8} pathOptions={{ color: "white", fillColor: getColor(m.data?.pm25), fillOpacity: 0.8 }}>
              <Popup style={{ color: "#000" }}>
                <b>{m.name}</b><br />
                PM2.5 (Cube): {m.data?.pm25 ?? "N/A"}<br />
                PM10: {m.data?.pm10 ?? "N/A"}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
      <div style={{ width: 230, background: "#1A1D27", borderRadius: 12, padding: 20, overflowY: "auto", color: "#fff" }}>
        <div><b>{loading ? "Đang quét..." : `${markers.length} / ${safeCities.length} Trạm`}</b></div>
        {safeCities.map(c => {
          const stationInfo = safeCityData[c];
          return (
            <div key={c} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #2A2D3A", fontSize: 12 }}>
              <span style={{ color: "#D3D1C7" }}>{c}</span>
              <span style={{ color: getColor(stationInfo?.pm25), fontWeight: 700 }}>{loading ? "..." : (stationInfo?.pm25 ?? "N/A")}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}