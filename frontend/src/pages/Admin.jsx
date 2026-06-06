import { useState, useEffect } from "react"
import axios from "axios"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const API = "https://2870w5x1-8000.asse.devtunnels.ms/"

const F1_PERFORMANCE_DATA = [
  { date: '01/05', f1: 0.82 },
  { date: '08/05', f1: 0.85 },
  { date: '15/05', f1: 0.84 },
  { date: '22/05', f1: 0.89 },
  { date: '29/05', f1: 0.92 },
  { date: '05/06', f1: 0.91 },
]

const STATUS_COLORS = {
  Active:  { bg: "rgba(0,228,0,0.15)",   text: "#00E400" },
  Warning: { bg: "rgba(255,126,0,0.15)", text: "#FF7E00" },
  Offline: { bg: "rgba(255,0,0,0.15)",   text: "#FF0000" },
}

// Modal thêm/sửa trạm
function StationModal({ station, onSave, onClose }) {
  const [form, setForm] = useState(
    station || { id: "", name: "", status: "Active", lastUpdate: "Just now" }
  )
  const isEdit = !!station

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
    }}>
      <div style={{ background: "#1A1D27", borderRadius: 12, padding: 24, width: 400, border: "1px solid #2A2D3A" }}>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>
          {isEdit ? "Sửa trạm" : "Thêm trạm mới"}
        </div>
        {[
          { label: "Mã trạm", key: "id", disabled: isEdit },
          { label: "Tên / Vị trí", key: "name" },
          { label: "Cập nhật cuối", key: "lastUpdate" },
        ].map(({ label, key, disabled }) => (
          <div key={key} style={{ marginBottom: 14 }}>
            <label style={{ fontSize: 12, color: "#8B8FA8", display: "block", marginBottom: 6 }}>{label}</label>
            <input
              value={form[key]}
              disabled={disabled}
              onChange={e => setForm({ ...form, [key]: e.target.value })}
              style={{
                width: "100%", background: "#0F1117", border: "1px solid #2A2D3A",
                color: disabled ? "#8B8FA8" : "white", padding: "8px 12px",
                borderRadius: 6, boxSizing: "border-box"
              }}
            />
          </div>
        ))}
        <div style={{ marginBottom: 20 }}>
          <label style={{ fontSize: 12, color: "#8B8FA8", display: "block", marginBottom: 6 }}>Trạng thái</label>
          <select
            value={form.status}
            onChange={e => setForm({ ...form, status: e.target.value })}
            style={{ width: "100%", background: "#0F1117", border: "1px solid #2A2D3A", color: "white", padding: "8px 12px", borderRadius: 6 }}
          >
            <option>Active</option>
            <option>Warning</option>
            <option>Offline</option>
          </select>
        </div>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{ background: "transparent", border: "1px solid #8B8FA8", color: "#8B8FA8", padding: "8px 16px", borderRadius: 6, cursor: "pointer" }}>
            Huỷ
          </button>
          <button onClick={() => onSave(form)} style={{ background: "#4F8EF7", color: "white", border: "none", padding: "8px 16px", borderRadius: 6, cursor: "pointer", fontWeight: 600 }}>
            {isEdit ? "Cập nhật" : "Thêm"}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Admin() {
  const [stations, setStations] = useState([])
  const [isRetraining, setIsRetraining] = useState(false)
  const [retrainResult, setRetrainResult] = useState(null)
  const [alertThreshold, setAlertThreshold] = useState(150)
  const [savedThreshold, setSavedThreshold] = useState(null)
  const [modal, setModal] = useState(null) // null | { mode: "add"|"edit", station? }
  const [toast, setToast] = useState(null)

  const showToast = (msg, color = "#00E400") => {
    setToast({ msg, color })
    setTimeout(() => setToast(null), 3000)
  }

  // Load stations + config
  useEffect(() => {
    axios.get(`${API}/admin/stations`)
      .then(r => setStations(r.data?.data || []))
      .catch(() => {})

    axios.get(`${API}/admin/config`)
      .then(r => setAlertThreshold(r.data?.data?.alert_threshold || 150))
      .catch(() => {})
  }, [])

  // Poll retrain status khi đang chạy
  useEffect(() => {
    if (!isRetraining) return
    const interval = setInterval(() => {
      axios.get(`${API}/admin/retrain/status`).then(r => {
        const data = r.data?.data
        if (!data.running) {
          setIsRetraining(false)
          setRetrainResult(data.last_result)
          showToast(data.last_result === "success" ? "✅ Retrain hoàn thành!" : "❌ Retrain thất bại", data.last_result === "success" ? "#00E400" : "#FF0000")
          clearInterval(interval)
        }
      })
    }, 1500)
    return () => clearInterval(interval)
  }, [isRetraining])

  const handleRetrain = () => {
    axios.post(`${API}/admin/retrain`)
      .then(() => { setIsRetraining(true); setRetrainResult(null) })
      .catch(e => showToast("❌ " + (e.response?.data?.detail || "Lỗi retrain"), "#FF0000"))
  }

  const handleSaveThreshold = () => {
    axios.post(`${API}/admin/config`, { alert_threshold: Number(alertThreshold) })
      .then(() => { setSavedThreshold(alertThreshold); showToast("✅ Đã lưu ngưỡng AQI: " + alertThreshold) })
      .catch(() => showToast("❌ Lưu thất bại", "#FF0000"))
  }

  const handleSaveStation = (form) => {
    if (modal.mode === "add") {
      axios.post(`${API}/admin/stations`, form)
        .then(r => {
          setStations(prev => [...prev, r.data.data])
          setModal(null)
          showToast("✅ Thêm trạm thành công")
        })
        .catch(e => showToast("❌ " + (e.response?.data?.detail || "Lỗi thêm trạm"), "#FF0000"))
    } else {
      axios.put(`${API}/admin/stations/${form.id}`, form)
        .then(r => {
          setStations(prev => prev.map(s => s.id === form.id ? r.data.data : s))
          setModal(null)
          showToast("✅ Cập nhật trạm thành công")
        })
        .catch(e => showToast("❌ " + (e.response?.data?.detail || "Lỗi cập nhật"), "#FF0000"))
    }
  }

  const handleDelete = (id) => {
    if (!window.confirm(`Xoá trạm ${id}?`)) return
    axios.delete(`${API}/admin/stations/${id}`)
      .then(() => {
        setStations(prev => prev.filter(s => s.id !== id))
        showToast(`✅ Đã xoá trạm ${id}`)
      })
      .catch(() => showToast("❌ Xoá thất bại", "#FF0000"))
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, paddingBottom: 40 }}>
      {/* Toast */}
      {toast && (
        <div style={{
          position: "fixed", top: 20, right: 20, zIndex: 2000,
          background: "#1A1D27", border: `1px solid ${toast.color}`,
          color: toast.color, padding: "12px 20px", borderRadius: 8,
          fontWeight: 600, fontSize: 14, boxShadow: "0 4px 20px rgba(0,0,0,0.4)"
        }}>
          {toast.msg}
        </div>
      )}

      {modal && (
        <StationModal
          station={modal.mode === "edit" ? modal.station : null}
          onSave={handleSaveStation}
          onClose={() => setModal(null)}
        />
      )}

      <h2 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Admin Portal</h2>

      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {/* Panel 1: Model Performance */}
        <div style={{ flex: 1, minWidth: 350, background: "#1A1D27", borderRadius: 12, padding: 20, border: "1px solid #2A2D3A" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div style={{ fontSize: 16, fontWeight: 600 }}>Model Performance (F1 Score)</div>
            <button
              onClick={handleRetrain}
              disabled={isRetraining}
              style={{
                background: isRetraining ? "#8B8FA8" : "#00E400",
                color: "#0F1117", border: "none", borderRadius: 6, padding: "8px 16px",
                fontWeight: 600, cursor: isRetraining ? "not-allowed" : "pointer"
              }}>
              {isRetraining ? "⏳ Đang Retrain..." : "⚡ Trigger Retrain"}
            </button>
          </div>
          {retrainResult && (
            <div style={{ marginBottom: 12, fontSize: 13, color: retrainResult === "success" ? "#00E400" : "#FF0000" }}>
              {retrainResult === "success" ? "✅ Retrain hoàn thành" : "❌ Retrain thất bại"}
            </div>
          )}
          <div style={{ width: "100%", height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={F1_PERFORMANCE_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2A2D3A" vertical={false} />
                <XAxis dataKey="date" stroke="#8B8FA8" fontSize={12} />
                <YAxis stroke="#8B8FA8" fontSize={12} domain={[0.7, 1.0]} />
                <Tooltip contentStyle={{ backgroundColor: "#0F1117", borderColor: "#2A2D3A", color: "#fff" }} />
                <Line type="monotone" dataKey="f1" stroke="#4F8EF7" strokeWidth={3} dot={{ r: 5 }} name="Weighted F1" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Panel 2: Config */}
        <div style={{ width: 320, background: "#1A1D27", borderRadius: 12, padding: 20, border: "1px solid #2A2D3A" }}>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Cài đặt hệ thống</div>
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: "block", fontSize: 13, color: "#8B8FA8", marginBottom: 8 }}>
              Ngưỡng AQI gửi Alert tự động
            </label>
            <div style={{ display: "flex", gap: 10 }}>
              <input
                type="number"
                value={alertThreshold}
                onChange={e => setAlertThreshold(e.target.value)}
                style={{ flex: 1, background: "#0F1117", border: "1px solid #2A2D3A", color: "white", padding: "8px 12px", borderRadius: 6 }}
              />
              <button
                onClick={handleSaveThreshold}
                style={{ background: "#4F8EF7", color: "white", border: "none", padding: "0 16px", borderRadius: 6, cursor: "pointer", fontWeight: 600 }}>
                Lưu
              </button>
            </div>
            {savedThreshold && (
              <p style={{ fontSize: 12, color: "#00E400", marginTop: 8 }}>✅ Đã lưu ngưỡng: {savedThreshold}</p>
            )}
            <p style={{ fontSize: 12, color: "#FF7E00", marginTop: 8 }}>
              * Trigger banner cảnh báo đỏ trên Dashboard nếu vượt ngưỡng này.
            </p>
          </div>
        </div>
      </div>

      {/* Panel 3: CRUD Stations */}
      <div style={{ background: "#1A1D27", borderRadius: 12, padding: 20, border: "1px solid #2A2D3A" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div style={{ fontSize: 16, fontWeight: 600 }}>Quản lý Trạm Cảm Biến (CRUD)</div>
          <button
            onClick={() => setModal({ mode: "add" })}
            style={{ background: "#4F8EF7", color: "white", border: "none", borderRadius: 6, padding: "8px 16px", cursor: "pointer", fontSize: 13 }}>
            + Thêm trạm mới
          </button>
        </div>

        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #2A2D3A", textAlign: "left", color: "#8B8FA8" }}>
              <th style={{ padding: "12px 8px" }}>Mã Trạm</th>
              <th style={{ padding: "12px 8px" }}>Tên / Vị trí</th>
              <th style={{ padding: "12px 8px" }}>Cập nhật cuối</th>
              <th style={{ padding: "12px 8px" }}>Trạng thái</th>
              <th style={{ padding: "12px 8px", textAlign: "right" }}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {stations.map(s => {
              const sc = STATUS_COLORS[s.status] || STATUS_COLORS.Offline
              return (
                <tr key={s.id} style={{ borderBottom: "1px solid #2A2D3A" }}>
                  <td style={{ padding: "12px 8px", fontWeight: 600 }}>{s.id}</td>
                  <td style={{ padding: "12px 8px" }}>{s.name}</td>
                  <td style={{ padding: "12px 8px", color: "#8B8FA8" }}>{s.lastUpdate}</td>
                  <td style={{ padding: "12px 8px" }}>
                    <span style={{ padding: "4px 8px", borderRadius: 4, fontSize: 12, fontWeight: 600, background: sc.bg, color: sc.text }}>
                      {s.status}
                    </span>
                  </td>
                  <td style={{ padding: "12px 8px", textAlign: "right" }}>
                    <button
                      onClick={() => setModal({ mode: "edit", station: s })}
                      style={{ background: "transparent", border: "1px solid #8B8FA8", color: "#8B8FA8", padding: "4px 12px", borderRadius: 4, cursor: "pointer", marginRight: 8 }}>
                      Sửa
                    </button>
                    <button
                      onClick={() => handleDelete(s.id)}
                      style={{ background: "rgba(255,0,0,0.1)", border: "1px solid #FF0000", color: "#FF0000", padding: "4px 12px", borderRadius: 4, cursor: "pointer" }}>
                      Xoá
                    </button>
                  </td>
                </tr>
              )
            })}
            {stations.length === 0 && (
              <tr>
                <td colSpan="5" style={{ textAlign: "center", padding: 20, color: "#8B8FA8" }}>Không có trạm nào</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}