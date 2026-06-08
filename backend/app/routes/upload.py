import secrets
from pathlib import Path
from typing import Tuple

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.routes.patients import _patients_store
from app.security import require_roles, verify_csrf_token

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_UPLOAD_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}
ALLOWED_FILE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB


def validate_file_type(file: UploadFile) -> Tuple[str, str]:
    content_type = file.content_type or ""
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


@router.post(
    "/patients/{patient_id}/upload",
    summary="Upload dokumen medis pasien",
    dependencies=[Depends(require_roles("admin", "staff")), Depends(verify_csrf_token)],
)
async def upload_patient_document(patient_id: int, file: UploadFile = File(...)):
    patient = next((p for p in _patients_store if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pasien dengan ID {patient_id} tidak ditemukan.",
        )

    filename, content_type = validate_file_type(file)
    file_ext = Path(filename).suffix.lower()
    upload_name = f"patient-{patient_id}-{secrets.token_hex(8)}{file_ext}"
    destination = UPLOAD_DIR / upload_name

    size = 0
    try:
        with destination.open("wb") as out_file:
            while chunk := await file.read(32_768):
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Ukuran file terlalu besar. Maksimal {MAX_UPLOAD_SIZE_BYTES // 1024} KB.",
                    )
                out_file.write(chunk)
    except HTTPException:
        if destination.exists():
            destination.unlink(missing_ok=True)
        raise

    return {
        "message": "File berhasil diunggah.",
        "patient_id": patient_id,
        "file_name": upload_name,
        "content_type": content_type,
        "size_bytes": size,
    }
