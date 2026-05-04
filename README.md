# Smart Waterway Routing

Hệ thống định tuyến thông minh cho phương tiện đường thủy, tích hợp thuật toán tìm đường trên mạng lưới sông/kênh và mô hình AI dự đoán thời gian di chuyển (ETA).

## Tính năng

- **Định tuyến đường thủy**: Thuật toán A* và Dijkstra trên đồ thị mạng lưới sông, kênh (OpenStreetMap)
- **Dự đoán ETA**: Mô hình XGBoost dự báo thời gian di chuyển dựa trên loại phương tiện, tốc độ, quãng đường
- **Bản đồ tương tác**: Giao diện Leaflet.js với OpenStreetMap, click để chọn điểm đi/đến
- **API RESTful**: FastAPI backend hiệu suất cao

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, Leaflet.js, Tailwind CSS |
| Backend | Python FastAPI, Uvicorn |
| Routing | NetworkX, OSMnx, Overpy |
| AI/ML | XGBoost, scikit-learn |
| Database | PostgreSQL + PostGIS |
| Deploy | Docker Compose |

## Cài đặt nhanh (Docker)

```bash
# Clone repo
git clone <repo-url>
cd smart-waterway-routing

# Copy env file
cp .env.example .env

# Khởi động toàn bộ hệ thống
docker compose up --build
```

Sau khi khởi động:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Cài đặt thủ công

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Khởi tạo dữ liệu (OSM + ML model)
python scripts/init_data.py

# Chạy server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Sử dụng

1. Mở http://localhost:3000
2. Click lên bản đồ để chọn **điểm xuất phát** (xanh lá)
3. Click lần 2 để chọn **điểm đến** (đỏ)
4. Chọn **loại phương tiện** và **tốc độ**
5. Nhấn **Find Route** để tính toán lộ trình
6. Xem tuyến đường và dự đoán thời gian trên bản đồ

## API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/health` | Kiểm tra trạng thái hệ thống |
| POST | `/api/route` | Tính toán lộ trình |
| GET | `/api/graph/info` | Thông tin đồ thị waterway |
| POST | `/api/graph/reload` | Tải lại dữ liệu OSM |

### POST /api/route

```json
{
  "start_lat": 10.8231,
  "start_lon": 106.6297,
  "end_lat": 10.0452,
  "end_lon": 105.7469,
  "algorithm": "astar",
  "vessel_type": 1,
  "speed_knots": 8.0
}
```

## Cấu trúc dự án

```
smart-waterway-routing/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, database
│   │   ├── data_pipeline/ # OSM data fetching & graph building
│   │   ├── routing/      # A*/Dijkstra engine
│   │   └── ml/           # ETA model
│   ├── scripts/          # Init scripts
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/          # Next.js App Router
│       └── components/   # React components
├── docker-compose.yml
└── README.md
```

## Phát triển

### Thêm khu vực mới

Chỉnh sửa bounding box trong `backend/scripts/init_data.py` để thu thập dữ liệu OSM cho khu vực khác.

### Tùy chỉnh ML model

Chỉnh sửa `backend/app/ml/trainer.py` để thêm features hoặc thay đổi mô hình.

## License

MIT
