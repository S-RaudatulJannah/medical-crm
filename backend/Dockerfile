# ============================================================
# Medical CRM - Backend Dockerfile (Security Hardened)
# Base: python:3.11-slim
# Exposes: Port 8000 (FastAPI via Uvicorn)
#
# Perubahan Keamanan:
# - [FIX-10] Direktori upload di luar web root (/var/medical-crm/uploads)
# - [FIX-09] Direktori log untuk security events (/var/log/medical-crm)
# - Non-root user untuk menjalankan aplikasi (best practice container security)
# - Python 3.11 (lebih baru, lebih aman dari 3.9)
#
# Kubernetes HPA Note:
# Running with --workers 1 agar setiap pod memiliki beban CPU
# yang dapat diprediksi. HPA akan menambah pod saat CPU tinggi.
# ============================================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install OS-level dependencies (minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# [FIX-10] Buat direktori upload DI LUAR web root
# [FIX-09] Buat direktori log untuk security events
# Kedua direktori ini TIDAK berada di dalam /app (web root)
# sehingga file upload dan log tidak bisa diakses via web server
RUN mkdir -p /var/medical-crm/uploads /var/log/medical-crm

# Buat non-root user untuk menjalankan aplikasi
# Ini adalah best practice container security — jika attacker berhasil
# melakukan RCE, mereka hanya mendapat akses sebagai user terbatas,
# bukan root yang bisa menguasai seluruh container/host.
RUN groupadd --system appuser \
    && useradd --system --gid appuser --create-home appuser \
    && chown -R appuser:appuser /var/medical-crm /var/log/medical-crm

# Copy & install Python dependencies dulu (layer caching optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy aplikasi ke dalam container
COPY . .

# Hapus file .env dari image (secrets harus diinject via env var, bukan baked in)
RUN rm -f .env

# Set ownership ke non-root user
RUN chown -R appuser:appuser /app

# Gunakan non-root user
USER appuser

# Expose port FastAPI
EXPOSE 8000

# Environment variables default (bisa di-override via Kubernetes ConfigMap/Secret)
ENV APP_ENV=production \
    UPLOAD_DIR=/var/medical-crm/uploads \
    SECURITY_LOG_DIR=/var/log/medical-crm

# Health check untuk Kubernetes liveness/readiness probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Jalankan dengan 1 worker agar CPU usage per pod dapat diprediksi
# Kubernetes HPA akan menambah pod saat CPU melebihi threshold
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
