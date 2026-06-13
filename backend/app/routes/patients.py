"""
Router: Pasien (Patient Module)

Endpoints:
- POST /api/patients  → Registrasi pasien darurat + Triase Otomatis + CPU-Intensive (HPA Trigger)
- GET  /api/patients  → Daftar semua pasien
- GET  /api/patients/{id} → Detail pasien berdasarkan ID

Storage: Supabase (PostgreSQL) — data persisten antar restart pod/container.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.models import PatientInput
from app.database import get_supabase
from app.security import require_roles, verify_csrf_token, rate_limiter, waf_protect
from app.services.triage import cpu_intensive_triage_computation, determine_triage_status

router = APIRouter()


# ══════════════════════════════════════════════════════════════════
# ENDPOINT: POST /api/patients
# Pendaftaran Pasien + Triase Otomatis + CPU-Intensive (Pemicu HPA)
# ══════════════════════════════════════════════════════════════════
@router.post(
    "/patients",
    summary="Daftarkan Pasien Darurat (Triase Otomatis + CPU Load untuk HPA)",
    response_description="Data pasien yang terdaftar beserta hasil triase",
    dependencies=[Depends(require_roles("admin")), Depends(verify_csrf_token), Depends(rate_limiter), Depends(waf_protect)],
)
def register_patient(patient: PatientInput):
    """
    ## Endpoint Utama: Registrasi Pasien Darurat

    Endpoint ini melakukan dua hal secara berurutan:

    ### 1. Komputasi CPU-Intensive (Pemicu HPA) ⚡
    Sebelum mengembalikan respons, sistem menjalankan fungsi
    `cpu_intensive_triage_computation()` yang menghitung bilangan prima
    hingga 300.000 secara **sinkron dan blocking**.

    Saat **load testing** (e.g., 100 request bersamaan menggunakan `hey` atau `wrk`):
    - Semua thread di thread pool akan sibuk menjalankan kalkulasi ini
    - CPU pod backend akan melonjak mendekati 100%
    - Kubernetes HPA akan mendeteksi CPU tinggi dan menambah pod baru
    - Anda dapat melihat scaling terjadi via: `kubectl get hpa -w`

    ### 2. Triase Otomatis 🏥
    Setelah komputasi, sistem menentukan prioritas triase berdasarkan
    algoritma START Triage menggunakan keluhan dan skala nyeri.

    ### Status Triase:
    - 🔴 **Kritis**: Penanganan segera (nyeri ≥ 8 atau gejala mengancam jiwa)
    - 🟡 **Sedang**: Penanganan dalam waktu dekat (nyeri 5-7)
    - 🟢 **Ringan**: Dapat menunggu antrian (nyeri 1-4)
    """
    # ──────────────────────────────────────────────────────────────
    # BLOK KOMPUTASI BERAT - PEMICU KUBERNETES HPA
    # Fungsi ini berjalan secara sinkron dan memblokir thread penuh
    # selama beberapa detik. DISENGAJA untuk demonstrasi HPA.
    # ──────────────────────────────────────────────────────────────
    prime_count = cpu_intensive_triage_computation()
    # ──────────────────────────────────────────────────────────────

    # Jalankan algoritma triase medis
    triage_status = determine_triage_status(
        chief_complaint=patient.chief_complaint,
        pain_level=patient.pain_level,
    )

    # Buat record pasien baru dan simpan ke Supabase
    new_patient = {
        "name": patient.name,
        "age": patient.age,
        "chief_complaint": patient.chief_complaint,
        "pain_level": patient.pain_level,
        "triage_status": triage_status,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "hospital_id": 1,
    }

    try:
        sb = get_supabase()
        result = sb.table("patients").insert(new_patient).execute()
        saved_patient = result.data[0] if result.data else new_patient
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Gagal menyimpan data pasien ke database: {str(e)}",
        )

    return {
        "message": "Pasien berhasil didaftarkan dan triase telah selesai",
        "patient": saved_patient,
        "triage_status": triage_status,
        "computation_info": (
            f"Verifikasi komputasi triase selesai. "
            f"Sistem memproses {prime_count:,} kalkulasi validasi."
        ),
    }


# ══════════════════════════════════════════════════════════════════
# ENDPOINT: GET /api/patients
# ══════════════════════════════════════════════════════════════════
@router.get(
    "/patients",
    summary="Daftar Semua Pasien Terdaftar",
    dependencies=[Depends(require_roles("admin", "staff", "viewer"))],
)
def get_all_patients():
    """Mendapatkan seluruh daftar pasien yang sudah terdaftar di sistem."""
    try:
        sb = get_supabase()
        result = sb.table("patients").select("*").order("registered_at", desc=True).execute()
        patients = result.data or []
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Gagal mengambil data pasien dari database: {str(e)}",
        )

    return {
        "patients": patients,
        "total": len(patients),
    }


# ══════════════════════════════════════════════════════════════════
# ENDPOINT: GET /api/patients/{patient_id}
# ══════════════════════════════════════════════════════════════════
@router.get(
    "/patients/{patient_id}",
    summary="Detail Pasien Berdasarkan ID",
    dependencies=[Depends(require_roles("admin", "staff", "viewer"))],
)
def get_patient_by_id(patient_id: int):
    """Mendapatkan informasi lengkap seorang pasien berdasarkan ID-nya."""
    try:
        sb = get_supabase()
        result = sb.table("patients").select("*").eq("id", patient_id).execute()
        patients = result.data or []
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Gagal mengambil data pasien dari database: {str(e)}",
        )

    if not patients:
        raise HTTPException(
            status_code=404,
            detail=f"Pasien dengan ID {patient_id} tidak ditemukan di sistem.",
        )

    return patients[0]
