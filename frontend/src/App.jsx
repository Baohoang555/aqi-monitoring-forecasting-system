import { useState } from "react"
import Dashboard from "./pages/Dashboard"
import MapAQI from "./pages/MapAQI"
import OLAPViewer from "./pages/OLAPViewer"
import Admin from "./pages/Admin"
import Visualization from "./pages/Visualization"

const MENU = [
  { key: "dashboard", label: "Dashboard" },
  { key: "map", label: "Bản đồ AQI" },
  { key: "olap", label: "OLAP Viewer" },
  { key: "visualization", label: "Trực quan hóa" },
  { key: "admin", label: "Admin" },
]

export default function App() {
  const [page, setPage] = useState("dashboard")

  const renderPage = () => {
    if (page === "dashboard") return <Dashboard />
    if (page === "map")       return <MapAQI />
    if (page === "olap")      return <OLAPViewer />
    if (page === "admin")     return <Admin />
    if (page === "visualization") return <Visualization />
  }

  return (
    <div style={{
      display: "flex",
      height: "100vh",
      width: "100vw",
      background: "#0F1117",
      color: "white",
      fontFamily: "Inter, sans-serif",
      margin: 0,
      padding: 0,
      boxSizing: "border-box",
      overflow: "hidden",
    }}>
      {/* Sidebar */}
      <div style={{
        width: 220,
        minWidth: 220,
        background: "#1A1D27",
        padding: "24px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}>
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 24, color: "white", paddingLeft: 8 }}>
          AQI Platform
        </div>
        {MENU.map(m => (
          <div key={m.key}
            onClick={() => setPage(m.key)}
            style={{
              padding: "10px 14px",
              borderRadius: 8,
              cursor: "pointer",
              background: page === m.key ? "#4F8EF7" : "transparent",
              color: page === m.key ? "white" : "#8B8FA8",
              fontSize: 14,
              transition: "all 0.2s",
            }}>
            {m.label}
          </div>
        ))}
      </div>

      {/* Main content */}
      <div style={{
        flex: 1,
        padding: page === "map" ? 0 : 24,
        overflowY: page === "map" ? "hidden" : "auto",
      }}>
        {renderPage()}
      </div>
    </div>
  )
}