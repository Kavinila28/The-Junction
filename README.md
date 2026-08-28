# 🚦 THE JUNCTION

### AI-Powered Road Conflict Intelligence System

> **Detect dangerous road interactions before they become accidents.**

THE JUNCTION is an AI-powered road safety platform that analyses CCTV traffic footage to detect **near-misses, sudden braking, unsafe interactions, and vehicle–pedestrian conflicts** at road junctions.

It uses computer vision and trajectory analysis to identify **emerging high-risk junctions before they become accident blackspots**.

## 🔥 Key Features

* 🎥 CCTV traffic video analysis
* 🚗 Vehicle & pedestrian detection using **YOLOv8**
* 🎯 Multi-object tracking using **ByteTrack**
* ⚠️ Near-miss & conflict detection
* ⏱️ Time-to-Collision (TTC) analysis
* 🚶 Vehicle–pedestrian conflict detection
* 📊 0–100 Junction Risk Score
* 🎬 AI-annotated traffic video
* 📈 Interactive traffic safety dashboard

## 🧠 System Workflow

```text
CCTV Footage
     ↓
YOLOv8 Detection
     ↓
ByteTrack Tracking
     ↓
Trajectory & Velocity Analysis
     ↓
Conflict Detection
     ↓
Risk Scoring
     ↓
FastAPI Backend
     ↓
React Dashboard
```

## 🛠️ Tech Stack

### AI / Computer Vision

Python • PyTorch • YOLOv8 • ByteTrack • OpenCV • NumPy

### Backend

FastAPI • Uvicorn • Pydantic • SQLite

### Frontend

React • Vite • Tailwind CSS • Recharts

### Deployment

Vercel • Render

## 🏗️ Architecture

```text
                CCTV Video
                    │
                    ▼
          YOLOv8 + ByteTrack
                    │
                    ▼
       Trajectory & Conflict Analysis
                    │
                    ▼
            FastAPI Backend
                    │
                    ▼
           React Dashboard
                    │
                    ▼
          Junction Risk Score
```

## 🎯 Use Cases

* 🚦 Identify emerging dangerous junctions
* 🚶 Improve pedestrian safety
* ⚠️ Detect recurring near-miss locations
* 🏙️ Support smart-city road planning
* 🛣️ Assist junction redesign and safety interventions

## 🌐 Live Demo

**Frontend:**
https://the-junction-tawny.vercel.app/

**Backend API:**
https://the-junction-api.onrender.com/

**API Documentation:**
https://the-junction-api.onrender.com/docs

## 🚀 Vision

Traditional road safety asks:

> **“Where did accidents happen?”**

THE JUNCTION asks:

> **“Where is dangerous behaviour happening before an accident happens?”**

### From reactive accident analysis → proactive road-conflict intelligence.

---

### 👩‍💻 Author

**Kavinila Prabhakaran**
Computer Science Engineering — Artificial Intelligence & Machine Learning

GitHub: https://github.com/Kavinila28
