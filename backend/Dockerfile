# ============================================================
# Medical CRM - Backend Dockerfile
# Base: python:3.9-slim
# Exposes: Port 8000 (FastAPI via Uvicorn)
#
# Kubernetes HPA Note:
# Running with --workers 1 agar setiap pod memiliki beban CPU
# yang dapat diprediksi. HPA akan menambah pod saat CPU tinggi.
# ============================================================

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install OS-level dependencies (minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy & install Python dependencies dulu (layer caching optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy aplikasi ke dalam container
COPY . .

# Expose port FastAPI
EXPOSE 8000

# Health check untuk Kubernetes liveness/readiness probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Jalankan dengan 1 worker agar CPU usage per pod dapat diprediksi
# Kubernetes HPA akan menambah pod saat CPU melebihi threshold
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
