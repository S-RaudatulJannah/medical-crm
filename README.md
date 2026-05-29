# Medical CRM - Platform CRM Medis
## SDGs Goal 3: Good Health and Well-being | Kubernetes Microservices

---

## 📁 Struktur Project

```
medical-crm/
├── backend/          ← Python FastAPI (CPU-intensive endpoint untuk HPA)
└── frontend/         ← Next.js 14 App Router + Tailwind CSS
```

---

## 🚀 Cara Menjalankan Lokal (Development)

### 1. Backend (FastAPI)

```bash
cd backend

# Buat virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
.\venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Jalankan server
uvicorn app.main:app --reload --port 8000
```

Backend berjalan di: `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

### 2. Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Jalankan dev server
npm run dev
```

Frontend berjalan di: `http://localhost:3000`

---

## 🐳 Docker Build

### Backend
```bash
cd backend
docker build -t medical-crm-backend:latest .
docker run -p 8000:8000 medical-crm-backend:latest
```

### Frontend
```bash
cd frontend
# BACKEND_URL akan diset saat runtime di Kubernetes
docker build -t medical-crm-frontend:latest .
docker run -p 3000:3000 \
  -e BACKEND_URL=http://localhost:8000 \
  medical-crm-frontend:latest
```

---

## ☸️ Kubernetes Deployment

### Arsitektur Kubernetes

```
[Internet] → [Ingress]
              ├── / → frontend-service:3000 (Next.js)
              └── (internal) backend-service:8000 (FastAPI)

BACKEND_URL=http://backend-service:8000  ← ConfigMap
```

### ConfigMap (Contoh)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: medical-crm-config
data:
  BACKEND_URL: "http://backend-service:8000"
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-deployment
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50   # Scale up saat CPU > 50%
```

---

## ⚡ Load Testing (Memicu HPA)

```bash
# Install hey (load testing tool)
go install github.com/rakyll/hey@latest

# Kirim 200 request dengan 50 concurrent (memicu HPA)
hey -n 200 -c 50 \
  -m POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","age":30,"chief_complaint":"Nyeri dada","pain_level":8}' \
  http://<BACKEND_URL>/api/patients

# Monitor HPA scaling di Kubernetes
kubectl get hpa -w
kubectl get pods -w
```

---

## 🎨 Design System

- **Warna Utama**: `#62796A` (Sage Green Medical)
- **Font**: Inter (Google Fonts)
- **Framework CSS**: Tailwind CSS v3
- **Triase Kritis**: 🔴 Red (`#ef4444`)
- **Triase Sedang**: 🟡 Amber (`#f59e0b`)
- **Triase Ringan**: 🟢 Emerald (`#10b981`)

---

## 📡 API Endpoints

| Method | Endpoint | Keterangan |
|--------|----------|------------|
| GET | `/health` | Health check |
| GET | `/api/hospitals/stats` | Statistik real-time RS |
| GET | `/api/patients` | Daftar semua pasien |
| POST | `/api/patients` | **Registrasi pasien (CPU-intensive + Triase)** |
| GET | `/api/patients/{id}` | Detail pasien |

---

*Medical CRM v1.0.0 • Kubernetes Ready • SDGs Goal 3*
