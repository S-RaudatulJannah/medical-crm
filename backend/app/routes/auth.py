from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.security import (
    ALLOWED_ROLES,
    create_access_token,
    get_token_info,
    require_roles,
    verify_admin_credentials,
    verify_api_token,
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


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    summary="Login admin untuk mendapatkan akses token API",
)
def login(auth: AuthRequest):
    if not verify_admin_credentials(auth.username, auth.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nama pengguna atau kata sandi salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(auth.username, role="admin")
    token_info = get_token_info(token)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "admin",
        "csrf_token": token_info["csrf_token"] if token_info else "",
    }


@router.post(
    "/auth/issue-token",
    response_model=IssueTokenResponse,
    summary="Issue token baru untuk staff atau viewer oleh admin",
    dependencies=[Depends(require_roles("admin"))],
)
def issue_token(payload: IssueTokenRequest):
    if payload.role not in ALLOWED_ROLES or payload.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role tidak valid. Gunakan 'staff' atau 'viewer'.",
        )

    token = create_access_token("admin", role=payload.role)
    token_info = get_token_info(token)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": payload.role,
        "csrf_token": token_info["csrf_token"] if token_info else "",
    }
