"""
Medical CRM - Backend API
Platform CRM Medis: Manajemen Pasien & Rumah Sakit
SDGs Goal 3: Good Health and Well-being

Arsitektur:
- FastAPI + Uvicorn (single-worker untuk HPA demo)
- CORS enabled untuk komunikasi dengan Frontend (Next.js)
- In-memory storage untuk keperluan demo Kubernetes

Perubahan Keamanan:
- [FIX-02] CORS origin di-whitelist (bukan wildcard "*")
- [FIX-08] Swagger /docs dan /redoc dimatikan di production
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import patients, hospitals, auth, upload
from app.security import SecurityHeadersMiddleware

# ─────────────────────────────────────────────
# Environment Configuration
# ─────────────────────────────────────────────
# Ambil mode environment dari env var. Default: "production" (paling aman).
# Set APP_ENV=development untuk mengaktifkan Swagger docs saat development.
APP_ENV = os.environ.get("APP_ENV", "production")

# [FIX-02] Daftar origin yang diizinkan untuk CORS.
# Di production, isi ALLOWED_ORIGINS env var dengan domain frontend kalian.
# Contoh: ALLOWED_ORIGINS=http://localhost:3000,http://192.168.1.100:30000
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://frontend-service:3000",
).split(",")

# ─────────────────────────────────────────────
# Inisialisasi FastAPI Application
# ─────────────────────────────────────────────
# [FIX-08] Swagger/OpenAPI docs dimatikan di production.
#
# Mengapa?
# Swagger UI di /docs menampilkan SELURUH peta API:
# - Semua endpoint beserta method (GET/POST/PUT/DELETE)
# - Semua parameter yang diterima beserta tipe datanya
# - Contoh request dan response
# Ini memberikan lawan peta serangan lengkap tanpa perlu scanning.
#
# Di development, set APP_ENV=development untuk mengaktifkan kembali.
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
    # [FIX-08] Docs hanya aktif di development
    docs_url="/docs" if APP_ENV == "development" else None,
    redoc_url="/redoc" if APP_ENV == "development" else None,
    openapi_url="/openapi.json" if APP_ENV == "development" else None,
)

# ─────────────────────────────────────────────
# CORS Middleware — [FIX-02]
# ─────────────────────────────────────────────
# Perubahan dari versi lama:
# - LAMA: allow_origins=["*"] → Semua website di dunia bisa akses API
# - BARU: allow_origins=[daftar_domain_spesifik] → Hanya frontend kita yang bisa akses
#
# Mengapa ini penting?
# Dengan CORS wildcard, lawan bisa membuat halaman web di domain mereka
# yang mengirim fetch() request ke API kita. Jika korban membuka halaman
# lawan sambil login ke Medical CRM, request akan membawa cookie/header
# autentikasi korban → data pasien bocor ke lawan.
#
# - allow_methods dibatasi ke method yang benar-benar dipakai
# - allow_headers dibatasi ke header yang benar-benar dipakai
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
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
    }


@app.get("/health", tags=["📌 Info"])
def health_check():
    """
    Health check endpoint untuk Kubernetes liveness & readiness probe.
    Kubernetes akan hit endpoint ini secara berkala untuk memastikan pod sehat.
    """
    return {"status": "healthy", "service": "medical-crm-backend"}
