# THE JUNCTION

> **"Predicting danger before it becomes an accident."**

An AI-powered road conflict intelligence system that analyses CCTV traffic footage to detect dangerous interactions, near-misses, and spatial proximity breaches before they result in collisions.

---

## 🚦 System Architecture

- **Computer Vision**: Ultralytics **YOLOv8n** pretrained on COCO for real-time traffic entity detection (`pedestrian`, `bicycle`, `car`, `motorcycle`, `bus`, `truck`).
- **Tracking**: **ByteTrack** multi-object tracking for persistent object identities and smoothed velocity vectors.
- **Conflict Engine**: Rule-based physics and temporal trajectory extrapolation for near-misses ($\text{TTC} \le 1.8\text{s}$), vehicle-pedestrian crossing exposures, path intersections, and sudden deceleration events.
- **Risk Index**: Deterministic 0–100 Junction Risk Score categorized into `LOW`, `MODERATE`, `HIGH`, and `CRITICAL`.
- **Annotation & Telemetry**: OpenCV & PyAV rendering motion trails, collision lines, hazard badges, and telemetry HUD with final computed risk scores into browser-streamable H.264 MP4.
- **Backend**: FastAPI + SQLite + Uvicorn with HTTP 206 Partial Content video streaming.
- **Frontend**: React 18 + Vite + Tailwind CSS + Recharts + Lucide React.

---

## 🛠️ Quick Start

### 1. Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

Dashboard is accessible at **`http://localhost:5173`**.

---

## 🧪 Testing

```bash
cd backend
python -m pytest tests
```

```bash
cd frontend
npm.cmd run build
```
Option 2: From Terminal (PowerShell / Command Prompt)
Open two terminal windows:

1. Backend Terminal (FastAPI)
powershell


cd C:\Users\pc\Documents\The-Junction\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
API URL: http://127.0.0.1:8000
Interactive Swagger Docs: http://127.0.0.1:8000/docs
Health Check: http://127.0.0.1:8000/api/health
2. Frontend Terminal (Vite + React)
powershell


cd C:\Users\pc\Documents\The-Junction\frontend
npm.cmd run dev
Dashboard URL: http://localhost:5173
If a Port is Already in Use (Kill Previous Instances)
If port 8000 or 5173 is busy, stop previous processes:

powershell


# Stop any process listening on port 8000 (Backend)
powershell -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"
# Stop any process listening on port 5173 (Frontend)
powershell -Command "Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"
Both servers are currently active and running:

Frontend Dashboard: http://localhost:5173
Backend API: http://127.0.0.1:8000
