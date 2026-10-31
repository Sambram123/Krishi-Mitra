"""
Krishi Mitra — Authentication APIRouter
Endpoints:
  - POST /api/auth/request-otp
  - POST /api/auth/verify-otp
  - POST /api/auth/refresh
  - POST /api/auth/logout
  - GET /api/auth/me
  - GET /api/admin/stats (Admin only)
"""

import uuid
from datetime import timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User, OTPCode, RefreshToken, utc_now
from datetime import datetime, timezone

def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

from backend.auth.config import (
    IS_PRODUCTION,
    REFRESH_TOKEN_DAYS,
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
)
from backend.auth.sms import get_sms_provider, mask_phone_number
from backend.auth.rate_limiter import check_and_record_rate_limit
from backend.auth.security import (
    normalize_phone,
    is_valid_phone,
    generate_otp,
    generate_refresh_token,
    hash_secret,
    verify_secret,
    create_access_token,
)
from backend.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/auth", tags=["auth"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


class RequestOtpRequest(BaseModel):
    phone: str = Field(..., description="Farmer phone number")


class VerifyOtpRequest(BaseModel):
    phone: str = Field(..., description="Farmer phone number")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    name: Optional[str] = Field(None, description="Farmer name")
    preferred_language: Optional[str] = Field("kn", description="Preferred language (kn or en)")


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Fallback refresh token if cookie unavailable")


def _get_client_ip(request: Request) -> str:
    """Extracts client IP, respecting reverse proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post("/request-otp")
def request_otp(req: RequestOtpRequest, request: Request, db: Session = Depends(get_db)):
    """Generates and dispatches a 6-digit OTP to the requested phone number."""
    phone = normalize_phone(req.phone)
    if not is_valid_phone(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format. Please provide a valid 10-digit mobile number.",
        )

    client_ip = _get_client_ip(request)
    allowed, err_msg = check_and_record_rate_limit(phone, client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=err_msg,
        )

    otp_code = generate_otp()
    code_hash = hash_secret(otp_code)
    expires_at = utc_now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    # Invalidate previous OTP codes for this phone
    db.query(OTPCode).filter(OTPCode.phone == phone).delete()

    otp_record = OTPCode(
        id=uuid.uuid4(),
        phone=phone,
        code_hash=code_hash,
        expires_at=expires_at,
        attempts=0,
    )
    db.add(otp_record)
    db.commit()

    sms_provider = get_sms_provider()
    sms_provider.send_otp(phone, otp_code)

    return {
        "status": "success",
        "message": "OTP sent successfully",
        "phone": mask_phone_number(phone),
    }


@router.post("/verify-otp")
def verify_otp(
    req: VerifyOtpRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Verifies OTP, provisions or retrieves farmer account, issues JWT & rotating refresh token."""
    phone = normalize_phone(req.phone)
    if not is_valid_phone(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format",
        )

    otp_record = (
        db.query(OTPCode)
        .filter(OTPCode.phone == phone)
        .order_by(OTPCode.created_at.desc())
        .first()
    )

    if not otp_record or ensure_utc(otp_record.expires_at) < utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired or was not requested. Please request a new OTP.",
        )

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum verification attempts exceeded. Please request a new OTP.",
        )

    if not verify_secret(req.otp.strip(), otp_record.code_hash):
        otp_record.attempts += 1
        db.commit()
        remaining = max(0, OTP_MAX_ATTEMPTS - otp_record.attempts)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP code. {remaining} attempt(s) remaining.",
        )

    # OTP verified successfully — clean up OTP records for this phone
    db.query(OTPCode).filter(OTPCode.phone == phone).delete()

    # Find or provision user
    user = db.query(User).filter(User.phone == phone).first()
    lang = req.preferred_language if req.preferred_language in ("kn", "en") else "kn"
    if not user:
        user = User(
            id=uuid.uuid4(),
            phone=phone,
            name=req.name or "",
            preferred_language=lang,
            role="farmer",
        )
        db.add(user)
    else:
        if req.name and not user.name:
            user.name = req.name
        if req.preferred_language:
            user.preferred_language = lang

    db.commit()
    db.refresh(user)

    # Issue Access Token
    access_token = create_access_token(
        user_id=str(user.id),
        phone=user.phone,
        role=user.role,
        preferred_language=user.preferred_language,
    )

    # Issue Refresh Token in a new family
    family_id = uuid.uuid4()
    raw_refresh_token = generate_refresh_token()
    token_hash = hash_secret(raw_refresh_token)
    refresh_expires_at = utc_now() + timedelta(days=REFRESH_TOKEN_DAYS)
    user_agent = request.headers.get("user-agent", "")[:250]

    refresh_record = RefreshToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=token_hash,
        family_id=family_id,
        device_info=user_agent,
        expires_at=refresh_expires_at,
    )
    db.add(refresh_record)
    db.commit()

    # Set secure httpOnly cookie
    response.set_cookie(
        key="krishi_refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=REFRESH_TOKEN_DAYS * 86400,
        path="/api/auth",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict(),
    }


@router.post("/refresh")
def refresh_token(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Rotates the refresh token and issues a new access token.
    Enforces automatic revocation of the entire token family upon reuse of a revoked token.
    """
    raw_refresh_token = request.cookies.get("krishi_refresh_token")
    if not raw_refresh_token and body and body.refresh_token:
        raw_refresh_token = body.refresh_token

    if not raw_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    token_hash = hash_secret(raw_refresh_token)
    token_record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if not token_record:
        response.delete_cookie("krishi_refresh_token", path="/api/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # REUSE DETECTION: If this token was already revoked, revoke the ENTIRE token family!
    if token_record.revoked_at is not None:
        db.query(RefreshToken).filter(
            RefreshToken.family_id == token_record.family_id,
            RefreshToken.revoked_at.is_(None),
        ).update({"revoked_at": utc_now()}, synchronize_session=False)
        db.commit()

        response.delete_cookie("krishi_refresh_token", path="/api/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Revoked refresh token reuse detected. All sessions in this family have been terminated.",
        )

    if ensure_utc(token_record.expires_at) < utc_now():
        response.delete_cookie("krishi_refresh_token", path="/api/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Invalidate the consumed refresh token
    token_record.revoked_at = utc_now()

    # Rotate: Issue new refresh token within the same token family
    new_raw_refresh_token = generate_refresh_token()
    new_token_hash = hash_secret(new_raw_refresh_token)
    new_expires_at = utc_now() + timedelta(days=REFRESH_TOKEN_DAYS)
    user_agent = request.headers.get("user-agent", "")[:250]

    new_record = RefreshToken(
        id=uuid.uuid4(),
        user_id=token_record.user_id,
        token_hash=new_token_hash,
        family_id=token_record.family_id,
        device_info=user_agent,
        expires_at=new_expires_at,
    )
    db.add(new_record)
    db.commit()

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Associated user no longer exists",
        )

    # Issue fresh access token
    new_access_token = create_access_token(
        user_id=str(user.id),
        phone=user.phone,
        role=user.role,
        preferred_language=user.preferred_language,
    )

    response.set_cookie(
        key="krishi_refresh_token",
        value=new_raw_refresh_token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=REFRESH_TOKEN_DAYS * 86400,
        path="/api/auth",
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db),
):
    """Revokes the current refresh token and clears the cookie."""
    raw_refresh_token = request.cookies.get("krishi_refresh_token")
    if not raw_refresh_token and body and body.refresh_token:
        raw_refresh_token = body.refresh_token

    if raw_refresh_token:
        token_hash = hash_secret(raw_refresh_token)
        token_record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if token_record and token_record.revoked_at is None:
            token_record.revoked_at = utc_now()
            db.commit()

    response.delete_cookie("krishi_refresh_token", path="/api/auth")
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns profile of currently authenticated user."""
    return current_user.to_dict()


@admin_router.get("/stats")
def get_admin_stats(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin-only monitoring and metrics endpoint."""
    total_users = db.query(User).count()
    active_tokens = db.query(RefreshToken).filter(RefreshToken.revoked_at.is_(None)).count()
    return {
        "total_users": total_users,
        "active_refresh_tokens": active_tokens,
        "admin_caller": current_user.phone,
    }
