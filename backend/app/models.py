"""
Pydantic Models untuk Medical CRM API.

Mendefinisikan struktur data untuk:
- Input pendaftaran pasien (validasi otomatis oleh FastAPI)
- Record pasien yang tersimpan
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TriageStatus(str, Enum):
    """Status triase berdasarkan standar START Triage."""
    CRITICAL = "Kritis"   # 🔴 Immediate - Penanganan segera
    MODERATE = "Sedang"   # 🟡 Delayed   - Penanganan dalam waktu dekat
    MILD     = "Ringan"   # 🟢 Minor     - Dapat menunggu


class PatientInput(BaseModel):
    """
    Schema input untuk pendaftaran pasien darurat.
    FastAPI akan otomatis memvalidasi semua field ini.
    """
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nama lengkap pasien",
        examples=["Budi Santoso"],
    )
    age: int = Field(
        ...,
        ge=0,
        le=150,
        description="Usia pasien dalam tahun",
        examples=[35],
    )
    chief_complaint: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Deskripsi keluhan utama pasien",
        examples=["Nyeri dada dan sesak napas"],
    )
    pain_level: int = Field(
        ...,
        ge=1,
        le=10,
        description="Tingkat nyeri pada skala 1 (tidak nyeri) hingga 10 (nyeri ekstrem)",
        examples=[7],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Andi Wijaya",
                "age": 42,
                "chief_complaint": "Nyeri dada hebat dan sulit bernapas sejak 30 menit lalu",
                "pain_level": 9,
            }
        }
    }
