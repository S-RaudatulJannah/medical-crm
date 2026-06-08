"""
Medical CRM - Backend API
Platform CRM Medis: Manajemen Pasien & Rumah Sakit
SDGs Goal 3: Good Health and Well-being

Arsitektur:
- FastAPI + Uvicorn (single-worker untuk HPA demo)
- CORS enabled untuk komunikasi dengan Frontend (Next.js)
- In-memory storage untuk keperluan demo Kubernetes
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import patients, hospitals, auth, upload
from app.security import SecurityHeadersMiddleware

# ─────────────────────────────────────────────
# Inisialisasi FastAPI Application
# ─────────────────────────────────────────────
app = FastAPI(
    title="Medical CRM API",
    description=(
        "## Platform CRM Medis - Manajemen Pasien & Rumah Sakit\n\n"
        "**SDGs Goal 3**: Good Health and Well-being\n\n"
        "### Fitur Utama:\n"
        "- **POST /api/patients** - Registrasi pasien dengan Triase Otomatis (CPU-intensive untuk demo HPA)\n"
        "- **GET /api/patients** - Daftar semua pasien\n"
        "- **GET /api/hospitals/stats** - Statistik real-time rumah sakit\n\n"
        "### Kubernetes HPA:\n"
        "Endpoint `POST /api/patients` menjalankan komputasi berat yang disengaja "
        "untuk memicu Horizontal Pod Autoscaler saat load testing."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────
# CORS Middleware (Penting untuk komunikasi Frontend ↔ Backend)
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Di produksi, ganti dengan domain spesifik
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Security Middleware
# ─────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ─────────────────────────────────────────────
# Register Routers
# ─────────────────────────────────────────────
app.include_router(auth.router, prefix="/api", tags=["🔐 Authentication"])
app.include_router(upload.router, prefix="/api", tags=["📁 File Upload"])
app.include_router(patients.router, prefix="/api", tags=["🏥 Patients - Manajemen Pasien"])
app.include_router(hospitals.router, prefix="/api", tags=["🏨 Hospitals - Manajemen Rumah Sakit"])


# ─────────────────────────────────────────────
# Root & Health Endpoints
# ─────────────────────────────────────────────
@app.get("/", tags=["📌 Info"])
def root():
    """Root endpoint - informasi dasar API."""
    return {
        "service": "Medical CRM API",
        "version": "1.0.0",
        "status": "running",
        "sdgs": "Goal 3 - Good Health and Well-being",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["📌 Info"])
def health_check():
    """
    Health check endpoint untuk Kubernetes liveness & readiness probe.
    Kubernetes akan hit endpoint ini secara berkala untuk memastikan pod sehat.
    """
    return {"status": "healthy", "service": "medical-crm-backend"}
