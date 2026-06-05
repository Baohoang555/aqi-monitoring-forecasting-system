# 🌤️ Urban Air Quality Intelligence - Frontend Web

Đây là thư mục chứa mã nguồn Frontend Web cho nền tảng giám sát chất lượng không khí (Dự án Data Mining - Nhóm 4). Giao diện được xây dựng bằng React (Vite) kết hợp với các thư viện trực quan hoá dữ liệu.

## 🚀 Tính Năng Chính (Giai đoạn PH-08)
- **Dashboard:** Theo dõi chỉ số AQI hiện tại, biểu đồ xu hướng (Recharts) và giải thích mô hình bằng SHAP.
- **Bản đồ nhiệt (Map):** Hiển thị mức độ ô nhiễm theo thời gian thực (Leaflet & D3 Heatmap).
- **OLAP Viewer:** Xem pivot table và biểu đồ phân tích sâu (Drill-down) từ Data Warehouse.
- **Admin Portal:** Quản lý trạm cảm biến, cài đặt cảnh báo và theo dõi hiệu suất mô hình (F1-score).

## 💻 Yêu Cầu Hệ Thống
- Node.js (phiên bản 18+ trở lên)

## 🛠️ Hướng Dẫn Cài Đặt

**1. Mở terminal tại thư mục frontend và cài đặt thư viện:**
\`\`\`bash
npm install
\`\`\`

*(Lưu ý: Dự án sử dụng thêm các thư viện `recharts`, `leaflet`, `react-leaflet` và `react-leaflet-heatmap-layer-v3`)*

**2. Khởi động server môi trường dev:**
\`\`\`bash
npm run dev
\`\`\`

**3. Truy cập ứng dụng:**
Mở trình duyệt và truy cập vào đường dẫn: `http://localhost:5173` (hoặc port được hiển thị trên terminal).

## 🔗 Lưu ý Kết Nối API
Frontend được cấu hình gọi API tới Backend ở địa chỉ mặc định là `http://localhost:8000`. Hãy đảm bảo Backend (FastAPI) đang được chạy song song để các biểu đồ hiển thị dữ liệu thực.
