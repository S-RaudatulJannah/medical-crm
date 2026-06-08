"""
Router: Pasien (Patient Module)

Endpoints:
- POST /api/patients  → Registrasi pasien darurat + Triase Otomatis + CPU-Intensive (HPA Trigger)
- GET  /api/patients  → Daftar semua pasien
- GET  /api/patients/{id} → Detail pasien berdasarkan ID
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime

from app.models import PatientInput
from app.security import require_roles, verify_csrf_token, rate_limiter, waf_protect
from app.services.triage import cpu_intensive_triage_computation, determine_triage_status

router = APIRouter()

# ══════════════════════════════════════════════════════════════════
# IN-MEMORY DATA STORE
# Untuk keperluan demo Kubernetes - tidak perlu setup database
# Di produksi: Gunakan PostgreSQL / MySQL dengan SQLAlchemy ORM
# ══════════════════════════════════════════════════════════════════
_patients_store: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Budi Santoso",
        "age": 45,
        "chief_complaint": "Nyeri dada hebat dan sesak napas sejak 1 jam lalu",
        "pain_level": 9,
        "triage_status": "Kritis",
        "registered_at": datetime.now().isoformat(),
        "hospital_id": 1,
    },
    {
        "id": 2,
        "name": "Siti Rahayu",
        "age": 32,
        "chief_complaint": "Demam tinggi 39°C disertai mual dan muntah",
        "pain_level": 6,
        "triage_status": "Sedang",
        "registered_at": datetime.now().isoformat(),
        "hospital_id": 1,
    },
    {
        "id": 3,
        "name": "Ahmad Fauzi",
        "age": 28,
        "chief_complaint": "Luka gores ringan di lengan kanan saat bekerja",
        "pain_level": 3,
        "triage_status": "Ringan",
        "registered_at": datetime.now().isoformat(),
        "hospital_id": 1,
    },
    {
        "id": 4,
        "name": "Dewi Kartika",
        "age": 55,
        "chief_complaint": "Pusing berat dan migrain yang tidak tertahankan",
        "pain_level": 7,
        "triage_status": "Sedang",
        "registered_at": datetime.now().isoformat(),
        "hospital_id": 1,
    },
    {
        "id": 5,
        "name": "Rudi Hermawan",
        "age": 19,
        "chief_complaint": "Batuk ringan dan pilek sejak 2 hari",
        "pain_level": 2,
        "triage_status": "Ringan",
        "registered_at": datetime.now().isoformat(),
        "hospital_id": 1,
    },
]

_patient_counter = 6  # Auto-increment ID counter


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
    global _patient_counter

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

    # Buat record pasien baru
    new_patient: Dict[str, Any] = {
        "id": _patient_counter,
        "name": patient.name,
        "age": patient.age,
        "chief_complaint": patient.chief_complaint,
        "pain_level": patient.pain_level,
        "triage_status": triage_status,
        "registered_at": datetime.now().isoformat(),
        "hospital_id": 1,
    }

    _patients_store.append(new_patient)
    _patient_counter += 1

    return {
        "message": "Pasien berhasil didaftarkan dan triase telah selesai",
        "patient": new_patient,
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
    return {
        "patients": _patients_store,
        "total": len(_patients_store),
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
    patient = next((p for p in _patients_store if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Pasien dengan ID {patient_id} tidak ditemukan di sistem.",
        )
    return patient
