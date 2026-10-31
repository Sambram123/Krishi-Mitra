"""
Krishi Mitra — Authentication Security and Cryptography Utilities
Provides OTP generation, token creation, passwordless hashing, and JWT handling.
"""

import hmac
import hashlib
import secrets
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt

from backend.auth.config import (
    JWT_SECRET,
    ACCESS_TOKEN_MINUTES,
    REFRESH_TOKEN_DAYS,
)

ALGORITHM = "HS256"


def normalize_phone(phone: str) -> str:
    """
    Cleans and normalizes Indian / international phone numbers.
    E.g. "9876543210" -> "+919876543210", "+91 98765 43210" -> "+919876543210".
    """
    cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())
    if cleaned.startswith("0") and len(cleaned) == 11:
        cleaned = "+91" + cleaned[1:]
    elif not cleaned.startswith("+"):
        if len(cleaned) == 10 and cleaned.isdigit():
            cleaned = "+91" + cleaned
        else:
            cleaned = "+" + cleaned
    return cleaned


def is_valid_phone(phone: str) -> bool:
    """Validates normalized E.164 phone format (10-15 digits after +)."""
    return bool(re.match(r"^\+[1-9]\d{9,14}$", phone))


def hash_secret(value: str) -> str:
    """Hashes sensitive data (OTP codes, refresh tokens) at rest with HMAC-SHA256."""
    return hmac.new(
        JWT_SECRET.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def verify_secret(plain_value: str, hashed_value: str) -> bool:
    """Timing-attack-resistant verification of hashed secrets."""
    computed = hash_secret(plain_value)
    return hmac.compare_digest(computed, hashed_value)


def generate_otp() -> str:
    """Generates a secure 6-digit random numeric OTP code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def generate_refresh_token() -> str:
    """Generates a cryptographically strong opaque refresh token."""
    return secrets.token_urlsafe(48)


def create_access_token(
    user_id: str,
    phone: str,
    role: str,
    preferred_language: str = "kn",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a signed JWT access token with 15-minute default lifetime."""
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_MINUTES)
    expire = now + delta

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "phone": phone,
        "role": role,
        "lang": preferred_language,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    Raises jwt.PyJWTError subclasses on invalid or expired token.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
