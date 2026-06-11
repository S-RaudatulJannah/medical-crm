"""
Security Module — Medical CRM Backend
======================================

Modul ini berisi SELURUH mekanisme keamanan aplikasi:

1. Password Hashing    → bcrypt dengan cost factor 12 (tahan brute-force)
2. Token Management    → CSPRNG token dengan TTL 1 jam
3. CSRF Protection     → Token per-session, divalidasi pada setiap state-changing request
4. Rate Limiting       → IP-based throttling dengan sliding window
5. WAF (Web App FW)    → Pattern-based payload inspection pada SEMUA HTTP method
6. RBAC                → Role-based access control (admin/staff/viewer)
7. Security Headers    → CSP, HSTS, X-Frame-Options, dll.
8. Security Logging    → JSON event log untuk integrasi Wazuh SIEM → Telegram
9. Account Lockout     → Kunci akun setelah 5x gagal login dalam 5 menit
10. IP Validation      → X-Forwarded-For hanya dipercaya dari trusted proxy

Perubahan keamanan dari audit:
- [FIX-01] SHA-256 diganti bcrypt — SHA-256 terlalu cepat, rentan rainbow table
- [FIX-03] Secrets diambil dari environment variable, bukan hardcoded
- [FIX-04] CSP header ditambahkan — mencegah eksekusi script berbahaya
- [FIX-07] WAF diperluas ke semua method — sebelumnya hanya POST
- [FIX-09] Security logger ditambahkan — agar Wazuh bisa ingest event
- [FIX-12] X-Forwarded-For divalidasi — mencegah IP spoofing untuk bypass rate limit
"""

import json
import logging
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

# ─────────────────────────────────────────────
# Load environment variables dari file .env
# Ini menggantikan hardcoded secrets (FIX-03)
# ─────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────
# SECURITY CONFIGURATION — SEMUA dari env vars
# ─────────────────────────────────────────────
# [FIX-03] Sebelumnya: API_SECRET_KEY = "blue-team-demo-secret" (HARDCODED!)
# Sekarang: Diambil dari environment variable. Jika belum diset, generate random.
# Ini penting karena jika lawan membaca source code, mereka TIDAK akan tahu secret-nya.
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", secrets.token_urlsafe(32))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")

# [FIX-01] Sebelumnya: Hash SHA-256 di-hardcode.
# Sekarang: Hash bcrypt disimpan di environment variable.
# Untuk generate hash baru, jalankan:
#   python -c "import bcrypt; print(bcrypt.hashpw(b'PASSWORD_ANDA', bcrypt.gensalt(12)).decode())"
# Lalu set env var ADMIN_PASSWORD_BCRYPT dengan hasilnya.
ADMIN_PASSWORD_BCRYPT = os.environ.get(
    "ADMIN_PASSWORD_BCRYPT",
    # Default hash untuk "BlueteamEAS2025!" — GANTI di production via env var!
    bcrypt.hashpw(b"BlueteamEAS2025!", bcrypt.gensalt(12)).decode("utf-8"),
)

TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", "3600"))  # 1 jam
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
ALLOWED_ROLES = ["admin", "staff", "viewer"]

# [FIX-12] Daftar IP proxy yang dipercaya.
# Hanya IP dalam daftar ini yang boleh mengirim X-Forwarded-For.
# Ini mencegah attacker memalsukan IP mereka untuk bypass rate limiter.
TRUSTED_PROXIES = set(
    os.environ.get("TRUSTED_PROXIES", "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16").split(",")
)

# ─────────────────────────────────────────────
# SECURITY EVENT LOGGER (FIX-09)
# ─────────────────────────────────────────────
# Mengapa ini penting:
# Tanpa logging, tim kita BUTA terhadap serangan yang sedang terjadi.
# Logger ini menulis event keamanan dalam format JSON ke file yang bisa
# dibaca oleh Wazuh SIEM, yang kemudian memicu alert ke Telegram Bot.
#
# Alur: App Log → File JSON → Wazuh Agent → Wazuh Manager → Telegram Bot
# ─────────────────────────────────────────────
import platform as _platform

_default_log_dir = "./logs" if _platform.system() == "Windows" else "/var/log/medical-crm"
LOG_DIR = Path(os.environ.get("SECURITY_LOG_DIR", _default_log_dir))
LOG_DIR.mkdir(parents=True, exist_ok=True)

security_logger = logging.getLogger("security_audit")
security_logger.setLevel(logging.INFO)

# Handler: tulis ke file JSON (satu event per baris = JSON Lines format)
_log_file = LOG_DIR / "security_events.json"
_file_handler = logging.FileHandler(str(_log_file), encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(message)s"))
security_logger.addHandler(_file_handler)

# Handler tambahan: tulis juga ke stdout agar terlihat di docker logs / kubectl logs
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(logging.Formatter("[SECURITY] %(message)s"))
security_logger.addHandler(_stream_handler)


def log_security_event(
    event_type: str,
    request: Request,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Menulis security event ke log file dalam format JSON.

    Format ini didesain agar bisa di-parse oleh Wazuh custom decoder.
    Setiap field dicocokkan oleh regex di decoder XML Wazuh.

    Args:
        event_type: Tipe event (LOGIN_FAILED, WAF_BLOCK, RATE_LIMIT_HIT, dll)
        request: Objek Request FastAPI (untuk ambil IP, method, path)
        details: Informasi tambahan (opsional)
    """
    event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "event_type": event_type,
        "source_ip": get_client_ip(request),
        "method": request.method,
        "path": str(request.url.path),
        "user_agent": request.headers.get("user-agent", ""),
        "details": details or {},
    }
    security_logger.info(json.dumps(event, ensure_ascii=False))


# ─────────────────────────────────────────────
# IN-MEMORY STORES
# ─────────────────────────────────────────────
_token_store: Dict[str, Dict[str, Any]] = {}
_client_request_log: Dict[str, List[float]] = {}
_failed_login_attempts: Dict[str, List[float]] = {}

# Konstanta untuk account lockout
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 menit

security_scheme = HTTPBearer(auto_error=False)

# ─────────────────────────────────────────────
# WAF PATTERNS — Deteksi payload berbahaya
# ─────────────────────────────────────────────
# [FIX-07] Ditambahkan lebih banyak pattern untuk menutup celah bypass
SUSPICIOUS_PATTERNS = [
    # XSS patterns
    r"<script\b",
    r"javascript:\b",
    r"onerror\s*=",
    r"onload\s*=",
    r"onmouseover\s*=",
    r"onfocus\s*=",
    r"onclick\s*=",
    r"onchange\s*=",
    r"<svg[^>]*\bonload\b",
    r"<img[^>]*\bonerror\b",
    r"<iframe\b",
    r"<object\b",
    r"<embed\b",
    r"expression\s*\(",
    r"url\s*\(\s*javascript:",
    # SQL Injection patterns
    r"union\s+select",
    r"select\s+.*from",
    r"drop\s+table",
    r"insert\s+into",
    r"delete\s+from",
    r"update\s+.*set",
    r"alter\s+table",
    r"--",
    r"or\s+1\s*=\s*1",
    r"and\s+1\s*=\s*1",
    r"'\s*or\s+'",
    r";\s*(drop|delete|insert|update|alter)",
    # Command injection
    r";\s*(ls|cat|pwd|whoami|id|uname)",
    r"\|\s*(ls|cat|pwd|whoami|id|uname)",
    r"`[^`]*`",
    r"\$\(.*\)",
    # Path traversal
    r"\.\./",
    r"\.\.\\",
]

suspicious_regex = re.compile("|".join(SUSPICIOUS_PATTERNS), re.IGNORECASE)


# ─────────────────────────────────────────────
# PASSWORD HASHING — bcrypt (FIX-01)
# ─────────────────────────────────────────────
# Mengapa bcrypt dan bukan SHA-256?
#
# SHA-256 menghitung hash dalam ~nanoseconds di GPU modern.
# Attacker bisa mencoba MILIARAN password per detik.
#
# bcrypt dirancang dengan "cost factor" (rounds=12 = 2^12 = 4096 iterasi).
# Setiap percobaan butuh ~0.3 detik. Ini membuat brute-force
# membutuhkan TAHUN alih-alih DETIK.
#
# Selain itu, bcrypt otomatis menambahkan SALT unik per password,
# sehingga dua user dengan password sama akan punya hash berbeda.
# Ini menggagalkan rainbow table attack.
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    """
    Hash password menggunakan bcrypt dengan cost factor 12.

    Cost factor 12 berarti: 2^12 = 4.096 iterasi internal.
    Waktu per hash: ~0.3 detik (cukup lambat untuk menggagalkan brute-force,
    cukup cepat untuk user experience login yang baik).
    """
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifikasi password terhadap hash bcrypt.

    bcrypt.checkpw() secara internal:
    1. Mengekstrak salt dari hash yang tersimpan
    2. Menghash password input dengan salt yang sama
    3. Membandingkan hasilnya (timing-safe comparison)
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def verify_admin_credentials(username: str, password: str) -> bool:
    """
    Verifikasi kredensial admin.

    Perubahan dari versi lama:
    - LAMA: hashlib.sha256() + hmac.compare_digest() — rentan rainbow table
    - BARU: bcrypt.checkpw() — tahan brute-force karena cost factor
    """
    if username != ADMIN_USERNAME:
        return False
    return verify_password(password, ADMIN_PASSWORD_BCRYPT)


# ─────────────────────────────────────────────
# ACCOUNT LOCKOUT (Bagian dari FIX-05)
# ─────────────────────────────────────────────
# Mengapa perlu account lockout?
# Meskipun bcrypt membuat brute-force lambat, kita tetap ingin
# MENOLAK percobaan login setelah 5 kali gagal dalam 5 menit.
# Ini menghentikan serangan otomatis seperti Hydra.
# ─────────────────────────────────────────────

def check_account_lockout(username: str, request: Request) -> None:
    """
    Cek apakah akun sedang dikunci karena terlalu banyak percobaan login gagal.

    Mekanisme:
    - Setiap login gagal dicatat dengan timestamp
    - Jika ada ≥5 gagal dalam 5 menit terakhir, akun dikunci
    - Setelah 5 menit tanpa percobaan, kunci otomatis terbuka (sliding window)
    """
    now = time.time()
    attempts = _failed_login_attempts.get(username, [])

    # Bersihkan percobaan yang sudah di luar jendela waktu
    recent_attempts = [t for t in attempts if now - t < LOCKOUT_DURATION_SECONDS]
    _failed_login_attempts[username] = recent_attempts

    if len(recent_attempts) >= MAX_LOGIN_ATTEMPTS:
        log_security_event("ACCOUNT_LOCKED", request, {
            "username": username,
            "failed_attempts": len(recent_attempts),
            "lockout_remaining_seconds": int(
                LOCKOUT_DURATION_SECONDS - (now - recent_attempts[0])
            ),
        })
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Akun '{username}' dikunci selama {LOCKOUT_DURATION_SECONDS // 60} menit "
                f"karena {MAX_LOGIN_ATTEMPTS} percobaan login gagal berturut-turut."
            ),
        )


def record_failed_login(username: str) -> None:
    """Catat percobaan login gagal untuk mekanisme lockout."""
    _failed_login_attempts.setdefault(username, []).append(time.time())


def clear_failed_logins(username: str) -> None:
    """Bersihkan catatan login gagal setelah login berhasil."""
    _failed_login_attempts.pop(username, None)


# ─────────────────────────────────────────────
# TOKEN MANAGEMENT
# ─────────────────────────────────────────────

def create_access_token(username: str, role: str = "admin") -> str:
    """
    Buat token akses baru menggunakan CSPRNG (secrets.token_urlsafe).

    Token ini:
    - 32 bytes random (256 bit entropy) — praktis tidak mungkin ditebak
    - Disimpan di server-side store dengan TTL (bukan JWT yang bisa di-decode klien)
    - Setiap token memiliki CSRF token tersendiri yang harus dikirim bersamaan
    """
    if role not in ALLOWED_ROLES:
        raise ValueError(f"Role tidak valid: {role}")

    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(20)
    _token_store[token] = {
        "username": username,
        "role": role,
        "expires_at": time.time() + TOKEN_TTL_SECONDS,
        "csrf_token": csrf_token,
    }
    return token


def get_token_info(token: str) -> Optional[Dict[str, Any]]:
    """Ambil info token. Return None jika tidak ada atau sudah expired."""
    token_info = _token_store.get(token)

    if not token_info:
        return None
    if time.time() > token_info["expires_at"]:
        _token_store.pop(token, None)
        return None
    return token_info


def is_token_valid(token: str) -> bool:
    return get_token_info(token) is not None


# ─────────────────────────────────────────────
# AUTHENTICATION & AUTHORIZATION DEPENDENCIES
# ─────────────────────────────────────────────

async def verify_api_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """
    FastAPI dependency: Verifikasi Bearer token pada setiap request.

    Mengecek:
    1. Apakah header Authorization ada dan formatnya "Bearer <token>"
    2. Apakah token terdaftar di server dan belum expired
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Gunakan Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    token_info = get_token_info(token)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kedaluwarsa.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {**token_info, "token": token}


def require_roles(*roles: str):
    """
    Factory function: Buat dependency yang memvalidasi role pengguna.

    Contoh penggunaan:
      dependencies=[Depends(require_roles("admin"))]         → hanya admin
      dependencies=[Depends(require_roles("admin", "staff"))] → admin & staff
    """
    def role_checker(
        token_info: Dict[str, Any] = Depends(verify_api_token),
    ) -> Dict[str, Any]:
        if token_info["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak. Role tidak memiliki izin untuk resource ini.",
            )
        return token_info

    return role_checker


# ─────────────────────────────────────────────
# CSRF PROTECTION
# ─────────────────────────────────────────────

async def verify_csrf_token(
    request: Request,
    token_info: Dict[str, Any] = Depends(verify_api_token),
) -> None:
    """
    Validasi CSRF token pada state-changing requests (POST, PUT, PATCH, DELETE).

    Mengapa CSRF token penting?
    Tanpa CSRF token, halaman web lawan bisa membuat form tersembunyi yang
    mengirim POST ke API kita menggunakan cookie/token browser korban.
    Dengan custom header X-CSRF-Token, browser akan menolak cross-origin
    request karena header custom memerlukan CORS preflight.
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    csrf_header = request.headers.get("x-csrf-token")
    if not csrf_header or csrf_header != token_info["csrf_token"]:
        # [FIX-09] Log CSRF violation untuk Wazuh
        log_security_event("CSRF_VIOLATION", request, {
            "expected_token_prefix": token_info["csrf_token"][:8] + "...",
            "received_token": csrf_header[:16] + "..." if csrf_header else "NONE",
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "CSRF token tidak valid atau tidak dikirim. "
                "Tambahkan header X-CSRF-Token yang sesuai."
            ),
        )


# ─────────────────────────────────────────────
# RATE LIMITER
# ─────────────────────────────────────────────

async def rate_limiter(request: Request):
    """
    Rate limiter IP-based dengan sliding window algorithm.

    Cara kerja:
    1. Ambil IP klien (sudah divalidasi via get_client_ip)
    2. Buang timestamp request lama (di luar window 60 detik)
    3. Jika jumlah request dalam window >= 20, tolak dengan 429
    4. Jika lolos, catat timestamp request ini
    """
    client_ip = get_client_ip(request)
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    request_times = _client_request_log.setdefault(client_ip, [])
    request_times[:] = [t for t in request_times if t > window_start]

    if len(request_times) >= RATE_LIMIT_MAX:
        # [FIX-09] Log rate limit hit
        log_security_event("RATE_LIMIT_HIT", request, {
            "client_ip": client_ip,
            "request_count": len(request_times),
            "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
        })
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Terlalu banyak permintaan dari alamat IP {client_ip}. "
                f"Batas {RATE_LIMIT_MAX} request per {RATE_LIMIT_WINDOW_SECONDS} detik."
            ),
        )

    request_times.append(now)


# ─────────────────────────────────────────────
# WAF — Web Application Firewall (FIX-07)
# ─────────────────────────────────────────────
# Perubahan dari versi lama:
# - LAMA: Hanya memeriksa body pada method POST
# - BARU: Memeriksa query parameters pada SEMUA method + body pada POST/PUT/PATCH
#
# Mengapa ini penting?
# Lawan bisa mengirim payload SQLi/XSS melalui URL query parameter
# (contoh: /api/patients?search=<script>alert(1)</script>)
# dan WAF versi lama akan membiarkannya lolos karena hanya cek POST.
# ─────────────────────────────────────────────

async def waf_protect(request: Request):
    """
    Web Application Firewall — inspeksi payload berbahaya.

    Urutan pengecekan:
    1. Periksa query string (berlaku untuk SEMUA HTTP method)
    2. Periksa URL path (deteksi path traversal, SQLi di URL)
    3. Untuk POST/PUT/PATCH: periksa request body (kecuali multipart/file upload)
    """
    # [FIX-07] BARU: Periksa query parameters pada SEMUA request
    query_string = str(request.url.query)
    if query_string and suspicious_regex.search(query_string):
        log_security_event("WAF_BLOCK", request, {
            "blocked_in": "query_string",
            "query": query_string[:200],
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pola berbahaya terdeteksi di query parameter. Permintaan ditolak.",
        )

    # [FIX-07] BARU: Periksa URL path
    url_path = str(request.url.path)
    if suspicious_regex.search(url_path):
        log_security_event("WAF_BLOCK", request, {
            "blocked_in": "url_path",
            "path": url_path[:200],
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pola berbahaya terdeteksi di URL. Permintaan ditolak.",
        )

    # Periksa body hanya untuk method yang membawa body
    # [FIX-07] BARU: Ditambahkan PUT dan PATCH (sebelumnya hanya POST)
    if request.method not in ("POST", "PUT", "PATCH"):
        return

    content_type = request.headers.get("content-type", "")
    # Skip file upload — akan divalidasi terpisah di upload endpoint
    if "multipart/form-data" in content_type:
        return

    try:
        body = await request.body()
        text = body.decode("utf-8", errors="ignore")
    except Exception:
        text = ""

    if suspicious_regex.search(text):
        log_security_event("WAF_BLOCK", request, {
            "blocked_in": "request_body",
            "body_preview": text[:200],
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Payload terdeteksi berisi pola berbahaya. "
                "Permintaan telah ditolak untuk melindungi aplikasi dari injeksi/XSS."
            ),
        )


# ─────────────────────────────────────────────
# CLIENT IP EXTRACTION (FIX-12)
# ─────────────────────────────────────────────
# Perubahan dari versi lama:
# - LAMA: Langsung percaya header X-Forwarded-For dari siapa saja
# - BARU: X-Forwarded-For hanya dipercaya jika berasal dari trusted proxy
#
# Mengapa ini penting?
# Lawan bisa menambahkan header "X-Forwarded-For: 1.2.3.4" pada setiap
# request untuk membuat rate limiter menganggapnya dari IP berbeda-beda.
# Ini membuat rate limiter tidak berguna sama sekali.
# ─────────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    """
    Ambil IP klien yang sebenarnya dengan validasi trusted proxy.

    Logika:
    1. Jika ada header X-Forwarded-For DAN IP yang mengirim request
       ada dalam daftar TRUSTED_PROXIES → gunakan IP dari header
    2. Jika tidak → gunakan IP koneksi langsung (request.client.host)
       Ini mencegah IP spoofing via header manipulation.
    """
    direct_ip = request.client.host if request.client else "unknown"

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for and direct_ip in TRUSTED_PROXIES:
        # Ambil IP pertama (IP asli klien) dari chain proxy
        return x_forwarded_for.split(",")[0].strip()

    # Jika bukan dari trusted proxy, abaikan header dan gunakan IP langsung
    return direct_ip


# ─────────────────────────────────────────────
# SECURITY HEADERS MIDDLEWARE (FIX-04: + CSP)
# ─────────────────────────────────────────────
# Perubahan dari versi lama:
# - LAMA: Tidak ada Content-Security-Policy header
# - BARU: CSP header ditambahkan untuk membatasi sumber script
#
# Mengapa CSP penting?
# Bahkan jika attacker berhasil menyisipkan payload XSS ke database,
# CSP akan MENCEGAH browser mengeksekusi script tersebut karena browser
# hanya akan menjalankan script dari sumber yang diizinkan (self).
# ─────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware yang menambahkan security headers ke setiap response.

    Header yang ditambahkan:
    - X-Content-Type-Options: nosniff → Cegah MIME type sniffing
    - X-Frame-Options: DENY → Cegah clickjacking via iframe
    - Referrer-Policy → Batasi informasi referrer yang dikirim
    - Permissions-Policy → Nonaktifkan akses kamera/mikrofon/geolokasi
    - X-XSS-Protection: 0 → Disable built-in XSS filter (sudah deprecated, pakai CSP)
    - Strict-Transport-Security → Paksa HTTPS selama 1 tahun
    - Content-Security-Policy → [BARU] Batasi sumber script/style/font/gambar
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault("X-XSS-Protection", "0")
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains; preload",
        )
        # [FIX-04] Content Security Policy — BARU
        # - default-src 'self': Hanya izinkan resource dari domain sendiri
        # - script-src 'self': Hanya izinkan script dari domain sendiri (blokir inline script)
        # - style-src 'self' 'unsafe-inline': Izinkan style inline (diperlukan oleh framework CSS)
        # - font-src: Izinkan Google Fonts
        # - img-src 'self' data:: Izinkan gambar dari domain sendiri + data URI (untuk base64)
        # - connect-src 'self': Hanya izinkan AJAX/fetch ke domain sendiri
        # - frame-ancestors 'none': Larang embedding di iframe (anti-clickjacking)
        # - base-uri 'self': Cegah base tag hijacking
        # - form-action 'self': Form hanya boleh submit ke domain sendiri
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';",
        )
        return response
