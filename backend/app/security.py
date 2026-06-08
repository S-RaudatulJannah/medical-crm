import hashlib
import hmac
import re
import secrets
import time
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

API_SECRET_KEY = "blue-team-demo-secret"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "f7bf6a0da54855403723957dfd7db436fb601df3211c5629cc5b93e0e23ff059"
TOKEN_TTL_SECONDS = 60 * 60
RATE_LIMIT_MAX = 20
RATE_LIMIT_WINDOW_SECONDS = 60
ALLOWED_ROLES = ["admin", "staff", "viewer"]

_token_store: Dict[str, Dict[str, Any]] = {}
_client_request_log: Dict[str, List[float]] = {}

security_scheme = HTTPBearer(auto_error=False)

SUSPICIOUS_PATTERNS = [
    r"<script\b",
    r"javascript:\b",
    r"onerror\s*=",
    r"onload\s*=",
    r"union\s+select",
    r"select\s+.*from",
    r"drop\s+table",
    r"--",
    r"or\s+1=1",
]

suspicious_regex = re.compile("|".join(SUSPICIOUS_PATTERNS), re.IGNORECASE)


def _hash_secret(secret: str) -> str:
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    return digest


def verify_admin_credentials(username: str, password: str) -> bool:
    if username != ADMIN_USERNAME:
        return False
    password_hash = _hash_secret(password)
    return hmac.compare_digest(password_hash, ADMIN_PASSWORD_HASH)


def create_access_token(username: str, role: str = "admin") -> str:
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
    token_info = _token_store.get(token)

    if not token_info:
        return None
    if time.time() > token_info["expires_at"]:
        _token_store.pop(token, None)
        return None
    return token_info


def is_token_valid(token: str) -> bool:
    return get_token_info(token) is not None


async def verify_api_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
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
    def role_checker(token_info: Dict[str, Any] = Depends(verify_api_token)) -> Dict[str, Any]:
        if token_info["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak. Role tidak memiliki izin untuk resource ini.",
            )
        return token_info

    return role_checker


async def verify_csrf_token(
    request: Request,
    token_info: Dict[str, Any] = Depends(verify_api_token),
) -> None:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    csrf_header = request.headers.get("x-csrf-token")
    if not csrf_header or csrf_header != token_info["csrf_token"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "CSRF token tidak valid atau tidak dikirim. "
                "Tambahkan header X-CSRF-Token yang sesuai."
            ),
        )


async def rate_limiter(request: Request):
    client_ip = get_client_ip(request)
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    request_times = _client_request_log.setdefault(client_ip, [])
    request_times[:] = [t for t in request_times if t > window_start]

    if len(request_times) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Terlalu banyak permintaan dari alamat IP {client_ip}. "
                f"Batas {RATE_LIMIT_MAX} request per {RATE_LIMIT_WINDOW_SECONDS} detik."
            ),
        )

    request_times.append(now)


async def waf_protect(request: Request):
    if request.method != "POST":
        return

    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        return

    try:
        body = await request.body()
        text = body.decode("utf-8", errors="ignore")
    except Exception:
        text = ""

    if suspicious_regex.search(text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Payload terdeteksi berisi pola berbahaya. "
                "Permintaan telah ditolak untuk melindungi aplikasi dari injeksi/XSS."
            ),
        )


def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
        response.headers.setdefault("X-XSS-Protection", "0")
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
        return response
