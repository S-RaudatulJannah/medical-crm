"""
Router: Authentication

Endpoints:
- POST /api/auth/login        → Login admin, dapatkan access token + CSRF token
- POST /api/auth/issue-token   → Admin mengeluarkan token untuk staff/viewer

Perubahan Keamanan:
- [FIX-05] Rate limiter ditambahkan pada login endpoint — mencegah brute-force
- [FIX-05] Account lockout ditambahkan — kunci akun setelah 5x gagal login
- [FIX-09] Security logging pada setiap login sukses/gagal
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.security import (
    ALLOWED_ROLES,
    check_account_lockout,
    clear_failed_logins,
    create_access_token,
    get_token_info,
    log_security_event,
    rate_limiter,
    record_failed_login,
    require_roles,
    verify_admin_credentials,
    verify_api_token,
    waf_protect,
)

router = APIRouter()


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    csrf_token: str


class IssueTokenRequest(BaseModel):
    role: str = Field(..., description="Role baru yang akan dibuat untuk token.", example="staff")


class IssueTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    csrf_token: str


# ══════════════════════════════════════════════════════════════════
# ENDPOINT: POST /api/auth/login
# ══════════════════════════════════════════════════════════════════
# [FIX-05] Perubahan dari versi lama:
# - LAMA: Tidak ada rate_limiter, tidak ada waf_protect, tidak ada account lockout
#   → Lawan bisa brute-force tanpa batas menggunakan Hydra/custom script
# - BARU: 3 lapis pertahanan:
#   1. rate_limiter → Batasi 20 request/menit per IP
#   2. waf_protect → Deteksi payload berbahaya di request body
#   3. check_account_lockout → Kunci akun setelah 5x gagal login dalam 5 menit
# ══════════════════════════════════════════════════════════════════
@router.post(
    "/auth/login",
    response_model=AuthResponse,
    summary="Login admin untuk mendapatkan akses token API",
    # [FIX-05] BARU: rate_limiter dan waf_protect ditambahkan sebagai dependencies
    dependencies=[Depends(rate_limiter), Depends(waf_protect)],
)
def login(auth: AuthRequest, request: Request):
    """
    Login endpoint dengan 3 lapis pertahanan anti-brute-force:

    1. **Rate Limiter**: Maks 20 request/menit per IP (dicek di dependency)
    2. **WAF**: Blokir payload SQLi/XSS di request body (dicek di dependency)
    3. **Account Lockout**: Kunci akun setelah 5x gagal login (dicek di dalam handler)

    Jika login berhasil, mengembalikan:
    - access_token: Token untuk Authorization header
    - csrf_token: Token untuk X-CSRF-Token header pada POST/PUT/DELETE
    - role: Role pengguna (admin/staff/viewer)
    """
    # [FIX-05] Cek apakah akun sedang dikunci (5 gagal → kunci 5 menit)
    check_account_lockout(auth.username, request)

    if not verify_admin_credentials(auth.username, auth.password):
        # [FIX-05] Catat percobaan gagal untuk mekanisme lockout
        record_failed_login(auth.username)

        # [FIX-09] Log event ke file untuk Wazuh SIEM
        log_security_event("LOGIN_FAILED", request, {
            "username": auth.username,
            "reason": "Invalid credentials",
        })

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nama pengguna atau kata sandi salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Login berhasil — bersihkan catatan gagal dan buat token
    clear_failed_logins(auth.username)

    token = create_access_token(auth.username, role="admin")
    token_info = get_token_info(token)

    # [FIX-09] Log login sukses
    log_security_event("LOGIN_SUCCESS", request, {
        "username": auth.username,
        "role": "admin",
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "admin",
        "csrf_token": token_info["csrf_token"] if token_info else "",
    }


# ══════════════════════════════════════════════════════════════════
# ENDPOINT: POST /api/auth/issue-token
# ══════════════════════════════════════════════════════════════════
@router.post(
    "/auth/issue-token",
    response_model=IssueTokenResponse,
    summary="Issue token baru untuk staff atau viewer oleh admin",
    dependencies=[Depends(require_roles("admin"))],
)
def issue_token(payload: IssueTokenRequest, request: Request):
    if payload.role not in ALLOWED_ROLES or payload.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role tidak valid. Gunakan 'staff' atau 'viewer'.",
        )

    token = create_access_token("admin", role=payload.role)
    token_info = get_token_info(token)

    # [FIX-09] Log token issuance
    log_security_event("TOKEN_ISSUED", request, {
        "issued_role": payload.role,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": payload.role,
        "csrf_token": token_info["csrf_token"] if token_info else "",
    }
