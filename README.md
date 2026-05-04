# Smart Waterway Routing

> Hệ thống định tuyến thông minh cho phương tiện đường thủy nội địa, tích hợp thuật toán tìm đường trên mạng lưới sông/kênh (OpenStreetMap) và mô hình AI/ML dự đoán thời gian di chuyển (ETA).

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+PostGIS-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Mục lục

1. [Tổng quan](#tổng-quan)
2. [Tính năng](#tính-năng)
3. [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
4. [Tech Stack](#tech-stack)
5. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
6. [Cài đặt nhanh (Docker)](#cài-đặt-nhanh-docker)
7. [Cài đặt thủ công](#cài-đặt-thủ-công)
8. [Biến môi trường](#biến-môi-trường)
9. [API Reference](#api-reference)
10. [Cấu trúc dự án](#cấu-trúc-dự-án)
11. [Makefile Commands](#makefile-commands)
12. [Chi tiết kỹ thuật](#chi-tiết-kỹ-thuật)
13. [Phát triển & Mở rộng](#phát-triển--mở-rộng)
14. [License](#license)

---

## Tổng quan

**Smart Waterway Routing** là một ứng dụng full-stack cho phép tính toán lộ trình tối ưu trên mạng lưới đường thủy nội địa (sông, kênh, hồ). Hệ thống sử dụng dữ liệu thực tế từ **OpenStreetMap** qua Overpass API, xây dựng đồ thị có hướng (directed graph) bằng NetworkX, và áp dụng thuật toán **A\*** / **Dijkstra** để tìm đường ngắn nhất giữa hai tọa độ địa lý.

Bên cạnh định tuyến, hệ thống tích hợp mô hình **XGBoost** để dự đoán thời gian di chuyển (ETA) dựa trên khoảng cách, loại phương tiện, tốc độ, thời điểm trong ngày và mùa vụ. Khi model chưa được huấn luyện, hệ thống tự động fallback sang công thức vật lý.

Giao diện frontend được xây dựng bằng **Next.js 14** với bản đồ tương tác **Leaflet.js**, cho phép người dùng chọn điểm xuất phát và điểm đến trực tiếp trên bản đồ.

---

## Tính năng

### Định tuyến đường thủy
- Hỗ trợ hai thuật toán: **A\*** (mặc định, nhanh hơn với heuristic Haversine) và **Dijkstra** (chính xác hơn cho đồ thị dày đặc)
- Tự động snap tọa độ người dùng vào node gần nhất trên đồ thị
- Trả về toàn bộ waypoints, danh sách cạnh (edge), khoảng cách từng đoạn và waterway type

### Dữ liệu OSM
- Tự động fetch dữ liệu sông/kênh từ **Overpass API** (OpenStreetMap)
- Cache dữ liệu OSM thô (JSON) và graph đã build (Pickle) để giảm thời gian khởi động
- Hỗ trợ reload graph theo yêu cầu qua API mà không cần restart server (background task)

### Dự đoán ETA (AI/ML)
- Model **XGBoost** với 6 features: `distance_km`, `vessel_type`, `speed_knots`, `num_segments`, `time_of_day`, `season`
- Fallback tự động về công thức vật lý khi model chưa tồn tại
- Script `init_data.py` tự động train model với dữ liệu tổng hợp và in metrics (MAE, RMSE)

### Giao diện bản đồ
- Bản đồ tương tác **Leaflet.js** với tile OpenStreetMap
- Click để đặt marker điểm xuất phát (xanh lá) và điểm đến (đỏ)
- Hiển thị tuyến đường (polyline) và ETA trực tiếp trên bản đồ
- Form chọn loại phương tiện và tốc độ

### Hạ tầng
- Toàn bộ stack chạy bằng **Docker Compose** (DB + Backend + Frontend)
- **PostGIS** extension sẵn sàng cho truy vấn không gian nâng cao
- Health check endpoint để giám sát trạng thái graph và model

---

## Kiến trúc hệ thống

```
┌───────────────────────────────────────────────────────────────┐
│                        Browser / Client                       │
│                    http://localhost:3000                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │               Next.js 14 Frontend                       │  │
│  │   ┌──────────────┐  ┌──────────────┐  ┌─────────────┐   │  │
│  │   │  Map.tsx     │  │ SearchForm   │  │ ETADisplay  │   │  │
│  │   │ (Leaflet.js) │  │  .tsx        │  │  .tsx       │   │  │
│  │   └──────────────┘  └──────────────┘  └─────────────┘   │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend :8000                        │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  API Router  │  │ Routing      │  │  ML (ETA Model)      │  │
│  │  /api/route  │→ │ Engine       │  │  XGBoost / Fallback  │  │
│  │  /api/graph  │  │ A* / Dijkstra│  │  Formula             │  │
│  └──────────────┘  └──────┬───────┘  └──────────────────────┘  │
│                            │                                   │
│  ┌─────────────────────────▼────────────────────────────────┐  │
│  │                  Data Pipeline                           │  │
│  │   WaterwayFetcher (Overpass API) → WaterwayGraphBuilder  │  │
│  │   OSM Cache (JSON)               Graph Cache (Pickle)    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│           PostgreSQL 15 + PostGIS :5432                         │
│                waterway_routing database                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Công nghệ | Phiên bản |
|-------|-----------|-----------|
| **Frontend** | Next.js, React | 14.2 / 18.3 |
| **Map** | Leaflet.js, react-leaflet | 1.9 / 4.2 |
| **Styling** | Tailwind CSS | 3.4 |
| **Backend** | FastAPI, Uvicorn | 0.111 / 0.29 |
| **Routing Engine** | NetworkX | 3.3 |
| **OSM Data** | OSMnx, Overpy | 1.9 / 0.7 |
| **ML / AI** | XGBoost, scikit-learn | 2.0 / 1.5 |
| **Geo Utils** | Shapely, PyProj, Haversine | 2.0 / 3.6 / 2.8 |
| **Database** | PostgreSQL + PostGIS | 15 / 3.4 |
| **ORM** | SQLAlchemy (async) | 2.0 |
| **Validation** | Pydantic v2 | 2.7 |
| **Containerization** | Docker Compose | 3.9 |

---

## Yêu cầu hệ thống

### Docker (khuyến nghị)
- Docker Desktop >= 24.0
- Docker Compose >= 2.20
- RAM >= 4 GB (quá trình fetch OSM và build graph cần ~1–2 GB)

### Cài đặt thủ công
- Python >= 3.11
- Node.js >= 18
- PostgreSQL >= 15 với PostGIS extension

---

## Cài đặt nhanh (Docker)

```bash
# 1. Clone repository
git clone <repo-url>
cd smart-waterway-routing

# 2. Tạo file cấu hình môi trường
cp .env.example .env

# 3. Build và khởi động toàn bộ stack
docker compose up --build
```

> Lần đầu khởi động, backend sẽ tự động fetch dữ liệu OSM từ Overpass API cho khu vực **Mekong Delta**. Quá trình này có thể mất 1–5 phút tùy tốc độ mạng.

Sau khi khởi động thành công:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| PostgreSQL | localhost:5432 |

### Khởi tạo dữ liệu thủ công (tuỳ chọn)

Nếu muốn khởi tạo dữ liệu OSM và train ML model trước khi chạy server:

```bash
# Chạy init script bên trong container backend
docker compose exec backend python scripts/init_data.py
```

Script sẽ thực hiện 3 bước:
1. Fetch dữ liệu OSM waterway cho Mekong Delta
2. Build directed graph và lưu cache
3. Train ETA model (XGBoost) và in metrics

---

## Cài đặt thủ công

### Backend

```bash
cd backend

# Tạo virtual environment
python -m venv venv

# Kích hoạt venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows (PowerShell)

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình biến môi trường
cp ../.env.example .env
# Chỉnh sửa .env cho phù hợp với môi trường local

# Khởi tạo dữ liệu (OSM data + ML model)
python scripts/init_data.py

# Chạy development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Cài đặt dependencies
npm install

# Cấu hình biến môi trường
cp .env.example .env.local
# Mặc định: NEXT_PUBLIC_API_URL=http://localhost:8000

# Chạy development server
npm run dev
```

### PostgreSQL (nếu chạy thủ công)

```sql
-- Tạo database và enable PostGIS extension
CREATE DATABASE waterway_routing;
\c waterway_routing
CREATE EXTENSION IF NOT EXISTS postgis;
```

---

## Biến môi trường

### Backend (`.env`)

| Biến | Mô tả | Mặc định |
|------|-------|---------|
| `DATABASE_URL` | Connection string PostgreSQL (asyncpg) | `postgresql+asyncpg://postgres:postgres@localhost:5432/waterway_routing` |
| `OSM_AREA` | Tên khu vực để fetch từ OSM | `Mekong Delta` |
| `DATA_DIR` | Thư mục lưu trữ dữ liệu cache và model | `./data` |
| `MODEL_PATH` | Đường dẫn file ETA model (.joblib) | `./data/eta_model.joblib` |
| `CORS_ORIGINS` | Danh sách allowed origins (JSON array) | `["http://localhost:3000"]` |
| `OVERPASS_API_URL` | URL Overpass API | `https://overpass-api.de/api/interpreter` |
| `OVERPASS_TIMEOUT` | Timeout (giây) cho Overpass request | `120` |
| `DEBUG` | Bật debug mode | `false` |

### Frontend (`.env.local`)

| Biến | Mô tả | Mặc định |
|------|-------|---------|
| `NEXT_PUBLIC_API_URL` | URL của Backend API | `http://localhost:8000` |

---

## API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### `GET /health`
Kiểm tra trạng thái hệ thống.

**Response:**
```json
{
  "status": "ok",
  "graph_loaded": true,
  "model_loaded": true
}
```

---

#### `POST /api/route`
Tính toán lộ trình tối ưu giữa hai tọa độ địa lý trên mạng lưới đường thủy.

**Request Body:**
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

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|----------|-------|
| `start_lat` | float | ✓ | Vĩ độ điểm xuất phát (-90 đến 90) |
| `start_lon` | float | ✓ | Kinh độ điểm xuất phát (-180 đến 180) |
| `end_lat` | float | ✓ | Vĩ độ điểm đến |
| `end_lon` | float | ✓ | Kinh độ điểm đến |
| `algorithm` | string | | `"astar"` (mặc định) hoặc `"dijkstra"` |
| `vessel_type` | int | | `0` = nhỏ, `1` = trung bình, `2` = lớn (mặc định: `0`) |
| `speed_knots` | float | | Tốc độ phương tiện (knot), 0–30 (mặc định: `7.0`) |

**Response:**
```json
{
  "route": {
    "waypoints": [
      { "lat": 10.8225, "lon": 106.6290 },
      { "lat": 10.7843, "lon": 106.5921 }
    ],
    "total_distance_km": 87.43,
    "segments": 142
  },
  "eta": {
    "minutes": 634.5,
    "hours": 10.575,
    "arrival_time": "2026-05-04T18:30:00Z"
  }
}
```

**Error Codes:**

| Code | Mô tả |
|------|-------|
| `404` | Không tìm thấy tuyến đường giữa hai điểm |
| `503` | Waterway graph chưa được load (gọi `POST /api/graph/reload`) |

---

#### `GET /api/graph/info`
Trả về thông tin thống kê về waterway graph đang được load.

**Response:**
```json
{
  "nodes": 15420,
  "edges": 18930,
  "area": "Mekong Delta",
  "loaded": true
}
```

---

#### `POST /api/graph/reload`
Kích hoạt tác vụ nền (background task) để re-fetch dữ liệu OSM và rebuild graph. Server không bị gián đoạn trong quá trình reload.

**Response:**
```json
{
  "status": "reload started",
  "message": "Graph reload triggered in background."
}
```

---

#### `GET /api/health`
Alias của `/health` (cùng response schema).

---

## Cấu trúc dự án

```
smart-waterway-routing/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app, startup event, CORS
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── router.py            # Tất cả API endpoints & Pydantic schemas
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py            # Cấu hình (pydantic-settings, .env)
│   │   ├── data_pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── osm_fetcher.py       # Fetch dữ liệu waterway từ Overpass API
│   │   │   └── graph_builder.py     # Build NetworkX DiGraph từ OSM data
│   │   ├── routing/
│   │   │   ├── __init__.py
│   │   │   └── engine.py            # A* / Dijkstra routing engine
│   │   └── ml/
│   │       ├── __init__.py
│   │       ├── eta_model.py         # ETAModel class (load, predict, fallback)
│   │       └── trainer.py           # Train XGBoost model
│   ├── scripts/
│   │   └── init_data.py             # Bootstrap script: OSM + graph + ML
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout (Next.js App Router)
│   │   │   ├── page.tsx             # Trang chính
│   │   │   └── globals.css
│   │   └── components/
│   │       ├── Map.tsx              # Leaflet map wrapper
│   │       ├── MapComponent.tsx     # Logic click, marker, polyline
│   │       ├── SearchForm.tsx       # Form chọn vessel type và speed
│   │       └── ETADisplay.tsx       # Hiển thị kết quả ETA
│   ├── Dockerfile
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
│
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## Makefile Commands

Dự án cung cấp Makefile để đơn giản hóa các thao tác phổ biến:

```bash
make help            # Hiển thị tất cả lệnh có sẵn
```

| Lệnh | Mô tả |
|------|-------|
| `make up` | Khởi động tất cả services (detached) |
| `make up-build` | Build images và khởi động |
| `make down` | Dừng và xóa containers |
| `make build` | Chỉ build Docker images |
| `make logs` | Xem logs tất cả services (follow) |
| `make logs-backend` | Xem logs backend |
| `make logs-frontend` | Xem logs frontend |
| `make init-data` | Chạy `init_data.py` trong container backend |
| `make backend-shell` | Mở bash shell trong container backend |
| `make frontend-shell` | Mở sh shell trong container frontend |
| `make dev-backend` | Chạy backend local (yêu cầu venv) |
| `make dev-frontend` | Chạy frontend local |
| `make install-backend` | Cài Python dependencies |
| `make install-frontend` | Cài Node dependencies |
| `make clean` | Xóa toàn bộ containers, volumes, và images |

---

## Chi tiết kỹ thuật

### Thuật toán Định tuyến

#### A* (mặc định)
Sử dụng **khoảng cách Haversine** làm hàm heuristic để ước tính chi phí từ node hiện tại đến đích. Khoảng cách thực trên mạng lưới waterway được dùng làm edge weight (`length` tính bằng metres). A* thường nhanh hơn Dijkstra đáng kể trên đồ thị lớn.

#### Dijkstra
Thuật toán tìm đường ngắn nhất kinh điển, đảm bảo tìm được đường tối ưu với chi phí là tổng độ dài cạnh. Phù hợp khi cần kết quả chính xác tuyệt đối hoặc đồ thị có edge weight không đồng đều lớn.

#### Snap to Graph
Khi người dùng click một tọa độ tùy ý, hệ thống tự động tìm **node gần nhất** trên đồ thị bằng cách duyệt toàn bộ nodes và tính Haversine distance. Node có khoảng cách nhỏ nhất sẽ được chọn làm điểm bắt đầu/kết thúc.

### Mô hình ETA (XGBoost)

**Features đầu vào:**

| Feature | Mô tả |
|---------|-------|
| `distance_km` | Tổng khoảng cách tuyến đường (km) |
| `vessel_type` | Loại phương tiện: 0=nhỏ, 1=trung bình, 2=lớn |
| `speed_knots` | Tốc độ phương tiện (knots) |
| `num_segments` | Số cạnh (segments) trên tuyến đường |
| `time_of_day` | Giờ trong ngày (0–23, UTC) |
| `season` | Mùa: 1=Đông, 2=Xuân, 3=Hè, 4=Thu |

**Fallback Formula** (khi model chưa được train):
```
ETA (phút) = (distance_km / speed_kmh) × 60 × vessel_factor × time_factor

vessel_factor: { nhỏ: 1.0, trung bình: 1.1, lớn: 1.2 }
time_factor:   1.0 + 0.1 × sin(hour × π / 12)
```

### Dữ liệu OSM

Dữ liệu waterway được fetch từ [Overpass API](https://overpass-api.de/) với các tag:
- `waterway=river` – sông lớn
- `waterway=canal` – kênh đào
- `waterway=stream` – suối, kênh nhỏ
- `waterway=drain` – mương thoát nước

Graph được build dưới dạng `nx.DiGraph` (đồ thị có hướng), với mỗi node lưu trữ `lat`, `lon`, và mỗi edge lưu `length` (metres), `name`, `waterway_type`, `navigable`.

---

## Phát triển & Mở rộng

### Thêm khu vực địa lý mới

Chỉnh sửa bounding box trong `backend/scripts/init_data.py`:

```python
BBOX = {
    "north": 11.5,
    "south": 9.0,
    "east":  106.8,
    "west":  104.5,
}
```

Hoặc đổi `OSM_AREA` trong `.env` sang tên khu vực khác (ví dụ: `"Ho Chi Minh City"`, `"Can Tho"`), sau đó gọi `POST /api/graph/reload`.

### Tùy chỉnh ML Model

Chỉnh sửa `backend/app/ml/trainer.py` để:
- Thêm features mới (ví dụ: độ rộng kênh, lưu lượng nước)
- Thay XGBoost bằng mô hình khác (LightGBM, RandomForest)
- Sử dụng dữ liệu thực tế thay dữ liệu tổng hợp

Sau khi chỉnh sửa, chạy lại:
```bash
python scripts/init_data.py
# hoặc
make init-data
```

### Mở rộng API

Tất cả endpoints nằm trong `backend/app/api/router.py`. Pydantic schemas được định nghĩa cùng file. Thêm endpoint mới theo pattern hiện có.

### Cơ sở dữ liệu

PostGIS đã được enable sẵn. Có thể dùng SQLAlchemy + GeoAlchemy2 để lưu trữ routes, lịch sử tìm kiếm, hoặc dữ liệu cảng. Schema migrations quản lý qua **Alembic** (`alembic upgrade head`).

---

## License

[MIT](LICENSE) – Tự do sử dụng, chỉnh sửa và phân phối với điều kiện giữ nguyên thông tin bản quyền.
