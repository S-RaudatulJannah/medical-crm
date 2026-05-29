"""
Router: Rumah Sakit (Hospital Module)

Endpoints:
- GET /api/hospitals/stats → Statistik real-time rumah sakit
  (Total pasien hari ini, kapasitas, distribusi triase, daftar pasien)
"""

from fastapi import APIRouter
from datetime import datetime

# Import shared data store dari modul patients
from app.routes.patients import _patients_store

router = APIRouter()

# Konfigurasi Rumah Sakit (demo statis)
_HOSPITAL_CONFIG = {
    "hospital_id": 1,
    "hospital_name": "RSUD Harapan Sehat",
    "address": "Jl. Kesehatan Raya No. 1, Jakarta Pusat, 10110",
    "phone": "(021) 1234-5678",
    "email": "info@rsud-harapansehat.go.id",
    "bed_capacity": 150,
}


@router.get(
    "/hospitals/stats",
    summary="Statistik Real-time Rumah Sakit",
    response_description="Data lengkap statistik operasional rumah sakit",
)
def get_hospital_stats():
    """
    ## Statistik Real-time RSUD Harapan Sehat

    Mengembalikan data operasional rumah sakit secara real-time:

    - **total_patients_today**: Jumlah pasien yang terdaftar hari ini
    - **total_patients**: Total seluruh pasien dalam sistem
    - **bed_capacity**: Kapasitas maksimal tempat tidur
    - **beds_occupied**: Jumlah tempat tidur yang sedang digunakan
    - **beds_available**: Jumlah tempat tidur yang masih tersedia
    - **triage_distribution**: Distribusi status triase (Kritis/Sedang/Ringan)
    - **patients**: Daftar lengkap semua pasien beserta status triase
    """
    today_str = datetime.now().date().isoformat()  # Format: "YYYY-MM-DD"

    # Filter pasien yang terdaftar hari ini
    today_patients = [
        p for p in _patients_store
        if isinstance(p.get("registered_at"), str)
        and p["registered_at"][:10] == today_str
    ]

    # Hitung ketersediaan tempat tidur
    beds_occupied = min(len(_patients_store), _HOSPITAL_CONFIG["bed_capacity"])
    beds_available = _HOSPITAL_CONFIG["bed_capacity"] - beds_occupied
    occupancy_rate = round((beds_occupied / _HOSPITAL_CONFIG["bed_capacity"]) * 100, 1)

    # Hitung distribusi status triase
    triage_distribution = {
        "critical": sum(1 for p in _patients_store if p.get("triage_status") == "Kritis"),
        "moderate": sum(1 for p in _patients_store if p.get("triage_status") == "Sedang"),
        "mild":     sum(1 for p in _patients_store if p.get("triage_status") == "Ringan"),
    }

    return {
        **_HOSPITAL_CONFIG,
        "total_patients_today": len(today_patients),
        "total_patients": len(_patients_store),
        "beds_occupied": beds_occupied,
        "beds_available": beds_available,
        "occupancy_rate_percent": occupancy_rate,
        "triage_distribution": triage_distribution,
        "patients": _patients_store,
        "last_updated": datetime.now().isoformat(),
    }
