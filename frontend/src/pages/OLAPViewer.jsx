import { useState } from "react"
import axios from "axios"

const API = "http://localhost:8000"

export default function OLAPViewer() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({ country: "", city: "", season: "" })

  const fetchData = () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filters.city) params.append("city", filters.city)
    if (filters.season) params.append("season", filters.season)

    axios.get(`${API}/olap/slice?${params.toString()}`)
      .then(r => {
        const raw = r.data.data || []
        const map = new Map()
        for (const row of raw) {
          const key = `${row.city}__${row.season}`
          if (!map.has(key)) map.set(key, row)
        }
        let result = Array.from(map.values())
        if (filters.country) {
          result = result.filter(r => r.country?.toLowerCase().includes(filters.country.toLowerCase()))
        }
        setData(result)
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, height: "calc(100vh - 48px)" }}>

      {/* Filter bar */}
      <div style={{
        background: "#1A1D27", borderRadius: 12, padding: "16px 20px",
        border: "1px solid #2A2D3A", display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end"
      }}>
        {[
          { label: "Quốc gia", key: "country", placeholder: "Ví dụ: Egypt" },
          { label: "Thành phố", key: "city", placeholder: "Ví dụ: Hanoi" },
        ].map(({ label, key, placeholder }) => (
          <div key={key} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <label style={{ fontSize: 11, color: "#8B8FA8", textTransform: "uppercase", letterSpacing: 0.8 }}>{label}</label>
            <input
              value={filters[key]}
              onChange={e => setFilters(f => ({ ...f, [key]: e.target.value }))}
              placeholder={placeholder}
              style={{
                background: "#0F1117", color: "white", border: "1px solid #2A2D3A",
                borderRadius: 8, padding: "7px 12px", fontSize: 13, width: 180,
                outline: "none",
              }}
            />
          </div>
        ))}

        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <label style={{ fontSize: 11, color: "#8B8FA8", textTransform: "uppercase", letterSpacing: 0.8 }}>Mùa</label>
          <select
            value={filters.season}
            onChange={e => setFilters(f => ({ ...f, season: e.target.value }))}
            style={{
              background: "#0F1117", color: "white", border: "1px solid #2A2D3A",
              borderRadius: 8, padding: "7px 12px", fontSize: 13, width: 140,
            }}
          >
            <option value="">Tất cả</option>
            <option value="dry">🌤 Mùa khô</option>
            <option value="rainy">🌧 Mùa mưa</option>
          </select>
        </div>

        <div style={{ display: "flex", gap: 8, marginLeft: "auto" }}>
          <button onClick={fetchData} style={{
            background: "#4F8EF7", border: "none", borderRadius: 8,
            padding: "8px 18px", color: "white", cursor: "pointer", fontSize: 13, fontWeight: 600
          }}>
            🔍 Tải dữ liệu
          </button>
          <button
            onClick={() => {
              if (!data?.length) return
              const csv = ["country,city,average_aqi,season",
                ...data.map(r => `${r.country},${r.city},${r.average_aqi},${r.season}`)
              ].join("\n")
              const a = document.createElement("a")
              a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }))
              a.download = "olap_data.csv"
              a.click()
            }}
            style={{
              background: "#2A2D3A", border: "1px solid #3A3D4A", borderRadius: 8,
              padding: "8px 16px", color: "white", cursor: "pointer", fontSize: 13
            }}>
            ⬇ Export CSV
          </button>
        </div>
      </div>

      {/* Pivot Table */}
      <div style={{
        background: "#1A1D27", borderRadius: 12, padding: 20,
        border: "1px solid #2A2D3A", flex: 1, display: "flex", flexDirection: "column", minHeight: 0
      }}>
        <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>
          Pivot Table Data {data && <span style={{ color: "#8B8FA8", fontWeight: 400, fontSize: 13 }}>— {data.length} dòng</span>}
        </div>

        {loading ? (
          <div style={{ color: "#8B8FA8" }}>Đang tải...</div>
        ) : data ? (
          <div style={{
            overflowY: "auto", flex: 1,
            scrollbarWidth: "thin", scrollbarColor: "#3A3D4A #0F1117",
            borderRadius: 8, border: "1px solid #2A2D3A"
          }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ position: "sticky", top: 0, background: "#0F1117", zIndex: 1 }}>
                  {["Quốc gia", "Thành phố", "Avg AQI", "Mùa"].map(h => (
                    <th key={h} style={{
                      textAlign: "left", padding: "10px 14px", color: "#8B8FA8",
                      borderBottom: "2px solid #2A2D3A", fontSize: 12,
                      textTransform: "uppercase", letterSpacing: 0.8
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr key={i}
                    style={{ borderBottom: "1px solid #1F2230" }}
                    onMouseEnter={e => e.currentTarget.style.background = "#1A1D2F"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                  >
                    <td style={{ padding: "10px 14px" }}>{row.country || "-"}</td>
                    <td style={{ padding: "10px 14px", fontWeight: 600 }}>{row.city}</td>
                    <td style={{ padding: "10px 14px", fontWeight: 700, color: row.average_aqi > 150 ? "#FF7E00" : "#4CAF50" }}>
                      {row.average_aqi?.toFixed(1)}
                    </td>
                    <td style={{ padding: "10px 14px" }}>
                      <span style={{
                        background: row.season === "dry" ? "#FF8E5320" : "#4F8EF720",
                        color: row.season === "dry" ? "#FF8E53" : "#4F8EF7",
                        padding: "3px 10px", borderRadius: 20, fontSize: 12, fontWeight: 600
                      }}>
                        {row.season === "dry" ? "🌤 dry" : "🌧 rainy"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ color: "#8B8FA8", fontSize: 13 }}>Nhập filter và nhấn "Tải dữ liệu"</div>
        )}
      </div>
    </div>
  )
}