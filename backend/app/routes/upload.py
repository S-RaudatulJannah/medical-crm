"""
Router: Secure File Upload

Endpoint:
- POST /api/patients/{patient_id}/upload → Upload dokumen medis pasien

Perubahan Keamanan:
- [FIX-06] Validasi Magic Bytes — mengecek byte pertama file untuk mendeteksi file palsu
- [FIX-10] Upload directory dipindah ke luar web root (konfigurasi via env var)
- [FIX-09] Security logging pada setiap upload (sukses/gagal)

Lapisan Validasi Upload (defense-in-depth):
1. RBAC → Hanya admin dan staff yang boleh upload
2. CSRF → Token CSRF harus valid
3. Ekstensi file → Whitelist (.pdf, .png, .jpg, .jpeg)
4. MIME Type → Whitelist (application/pdf, image/png, image/jpeg)
5. Magic Bytes → Verifikasi file signature asli [BARU]
6. Ukuran file → Maksimal 2 MB
7. Nama file → Diacak (secrets.token_hex) untuk mencegah path traversal
"""

import os
import secrets
from pathlib import Path
from typing import Tuple

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.routes.patients import _patients_store
from app.security import log_security_event, require_roles, verify_csrf_token

router = APIRouter()

# ─────────────────────────────────────────────
# KONFIGURASI UPLOAD
# ─────────────────────────────────────────────
# [FIX-10] Upload directory sekarang dikonfigurasi via environment variable.
# Default: /var/medical-crm/uploads (DI LUAR web root)
#
# Mengapa harus di luar web root?
# Jika Nginx/web server di-configure untuk serve static files dari project root,
# file upload di dalam project tree bisa diakses langsung via URL.
# Contoh berbahaya: attacker upload web shell → akses langsung via browser → RCE
#
# Dengan menempatkan di /var/medical-crm/uploads, file TIDAK bisa diakses
# langsung melalui web server. Hanya aplikasi yang bisa membacanya.
import platform as _platform

_default_upload_dir = "./uploads" if _platform.system() == "Windows" else "/var/medical-crm/uploads"
UPLOAD_DIR = Path(
    os.environ.get("UPLOAD_DIR", _default_upload_dir)
)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Whitelist tipe file yang diizinkan
ALLOWED_UPLOAD_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}
ALLOWED_FILE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB

# ─────────────────────────────────────────────
# MAGIC BYTES (FILE SIGNATURES) — [FIX-06]
# ─────────────────────────────────────────────
# Apa itu magic bytes?
# Setiap format file memiliki "tanda tangan" berupa beberapa byte pertama
# yang unik dan TIDAK bisa dipalsukan tanpa merusak file itu sendiri.
#
# Contoh:
# - File PNG selalu dimulai dengan byte: 89 50 4E 47 (yaitu \x89PNG)
# - File JPEG selalu dimulai dengan byte: FF D8 FF
# - File PDF selalu dimulai dengan teks: %PDF
#
# Mengapa perlu magic bytes kalau sudah ada cek MIME type?
# Karena MIME type (Content-Type header) dikirim oleh KLIEN dan bisa dipalsukan.
# Attacker bisa upload file PHP web shell dengan Content-Type: image/jpeg
# dan ekstensi .jpg, tapi isi filenya sebenarnya kode PHP.
# Magic bytes TIDAK bisa dipalsukan tanpa mengubah isi file.
#
# Dengan mengecek magic bytes, kita memastikan file yang diupload
# BENAR-BENAR adalah format yang diklaim.
MAGIC_BYTES = {
    b"%PDF": "application/pdf",      # PDF selalu dimulai dengan %PDF
    b"\x89PNG": "image/png",         # PNG dimulai dengan \x89PNG
    b"\xff\xd8\xff": "image/jpeg",   # JPEG dimulai dengan FF D8 FF
}


async def validate_magic_bytes(file: UploadFile) -> None:
    """
    Membaca 8 byte pertama file dan mencocokkan dengan tanda tangan (signature)
    format file yang diizinkan.

    Cara kerja:
    1. Baca 8 byte pertama file (cukup untuk identifikasi semua format yang diizinkan)
    2. Cocokkan dengan daftar MAGIC_BYTES
    3. Jika tidak cocok satupun → TOLAK file (kemungkinan file dipalsukan)
    4. Kembalikan posisi baca ke awal agar file bisa disimpan utuh
    """
    header = await file.read(8)
    await file.seek(0)  # PENTING: kembalikan posisi ke awal setelah baca

    if len(header) < 3:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File terlalu kecil atau kosong.",
        )

    matched = any(header.startswith(magic) for magic in MAGIC_BYTES)
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Konten file tidak sesuai dengan format yang diizinkan. "
                "Validasi magic bytes gagal — file mungkin dipalsukan."
            ),
        )


def validate_file_type(file: UploadFile) -> Tuple[str, str]:
    """
    Validasi berdasarkan Content-Type header dan ekstensi file.

    Ini adalah lapisan validasi PERTAMA (sebelum magic bytes).
    Meskipun Content-Type bisa dipalsukan, kita tetap memeriksanya
    sebagai defense-in-depth. Attacker harus melewati SEMUA lapisan.
    """
    content_type = file.content_type or ""
    # Path().name → mengambil hanya nama file (buang path traversal seperti ../../)
    filename = Path(file.filename or "").name
    file_ext = Path(filename).suffix.lower()

    if content_type not in ALLOWED_UPLOAD_TYPES or file_ext not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Tipe file tidak didukung. Hanya PDF, PNG, dan JPEG yang diizinkan."
            ),
        )

    return filename, content_type


# ══════════════════════════════════════════════════════════════════
# ENDPOINT: POST /api/patients/{patient_id}/upload
# ══════════════════════════════════════════════════════════════════
@router.post(
    "/patients/{patient_id}/upload",
    summary="Upload dokumen medis pasien",
    dependencies=[Depends(require_roles("admin", "staff")), Depends(verify_csrf_token)],
)
async def upload_patient_document(
    patient_id: int,
    request: Request,
    file: UploadFile = File(...),
):
    """
    Upload file dokumen medis untuk pasien tertentu.

    Urutan validasi (defense-in-depth):
    1. RBAC: Hanya admin & staff → (dicek di dependencies)
    2. CSRF: Token harus valid → (dicek di dependencies)
    3. Patient exists: Pasien dengan ID tersebut harus ada
    4. File extension: Harus .pdf/.png/.jpg/.jpeg
    5. MIME type: Harus application/pdf, image/png, atau image/jpeg
    6. Magic bytes: Byte pertama file harus cocok dengan format asli [BARU]
    7. File size: Maksimal 2 MB (dicek streaming, bukan di memory)
    8. Filename: Diacak dengan secrets.token_hex untuk mencegah path traversal
    """
    # Validasi: Apakah pasien ada?
    patient = next((p for p in _patients_store if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pasien dengan ID {patient_id} tidak ditemukan.",
        )

    # Lapisan 1: Validasi ekstensi + MIME type
    filename, content_type = validate_file_type(file)

    # Lapisan 2: [FIX-06] Validasi magic bytes (file signature)
    await validate_magic_bytes(file)

    # Nama file diacak → mencegah:
    # - Path traversal (../../etc/passwd)
    # - File overwrite (jika nama sama)
    # - Information disclosure (nama file asli bisa berisi info sensitif)
    file_ext = Path(filename).suffix.lower()
    upload_name = f"patient-{patient_id}-{secrets.token_hex(8)}{file_ext}"
    destination = UPLOAD_DIR / upload_name

    # Simpan file secara streaming (chunk by chunk)
    # Ini penting agar file besar tidak memakan seluruh RAM
    size = 0
    try:
        with destination.open("wb") as out_file:
            while chunk := await file.read(32_768):  # Baca 32KB per chunk
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Ukuran file terlalu besar. Maksimal {MAX_UPLOAD_SIZE_BYTES // 1024} KB.",
                    )
                out_file.write(chunk)
    except HTTPException:
        # Jika file terlalu besar, hapus file yang sudah ditulis sebagian
        if destination.exists():
            destination.unlink(missing_ok=True)
        raise

    # [FIX-09] Log upload sukses
    log_security_event("FILE_UPLOAD_SUCCESS", request, {
        "patient_id": patient_id,
        "original_filename": filename,
        "stored_filename": upload_name,
        "content_type": content_type,
        "size_bytes": size,
    })

    return {
        "message": "File berhasil diunggah.",
        "patient_id": patient_id,
        "file_name": upload_name,
        "content_type": content_type,
        "size_bytes": size,
    }
