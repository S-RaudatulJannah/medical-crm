"""
Router: Rumah Sakit (Hospital Module)

Endpoints:
- GET /api/hospitals/stats → Statistik real-time rumah sakit
  (Total pasien hari ini, kapasitas, distribusi triase, daftar pasien)

Storage: Supabase (PostgreSQL) — query langsung ke tabel patients.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.database import get_supabase
from app.security import require_roles

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
    dependencies=[Depends(require_roles("admin", "staff", "viewer"))],
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
    try:
        sb = get_supabase()

        # Ambil semua pasien dari Supabase
        result = sb.table("patients").select("*").order("registered_at", desc=True).execute()
        all_patients = result.data or []

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Gagal mengambil data dari database: {str(e)}",
        )

    today_str = datetime.now(timezone.utc).date().isoformat()  # Format: "YYYY-MM-DD"

    # Filter pasien yang terdaftar hari ini
    today_patients = [
        p for p in all_patients
        if isinstance(p.get("registered_at"), str)
        and p["registered_at"][:10] == today_str
    ]

    # Hitung ketersediaan tempat tidur
    beds_occupied = min(len(all_patients), _HOSPITAL_CONFIG["bed_capacity"])
    beds_available = _HOSPITAL_CONFIG["bed_capacity"] - beds_occupied
    occupancy_rate = round((beds_occupied / _HOSPITAL_CONFIG["bed_capacity"]) * 100, 1)

    # Hitung distribusi status triase
    triage_distribution = {
        "critical": sum(1 for p in all_patients if p.get("triage_status") == "Kritis"),
        "moderate": sum(1 for p in all_patients if p.get("triage_status") == "Sedang"),
        "mild":     sum(1 for p in all_patients if p.get("triage_status") == "Ringan"),
    }

    return {
        **_HOSPITAL_CONFIG,
        "total_patients_today": len(today_patients),
        "total_patients": len(all_patients),
        "beds_occupied": beds_occupied,
        "beds_available": beds_available,
        "occupancy_rate_percent": occupancy_rate,
        "triage_distribution": triage_distribution,
        "patients": all_patients,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
