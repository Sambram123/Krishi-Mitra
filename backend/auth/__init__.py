"""
Krishi Mitra — Authentication Package
"""

from backend.auth.config import (
    JWT_SECRET,
    ACCESS_TOKEN_MINUTES,
    REFRESH_TOKEN_DAYS,
    OTP_PROVIDER,
    IS_PRODUCTION,
    assert_production_config,
)
from backend.auth.dependencies import get_current_user, require_role
from backend.auth.router import router as auth_router, admin_router
from backend.auth.security import (
    create_access_token,
    decode_access_token,
    generate_otp,
    generate_refresh_token,
    hash_secret,
    verify_secret,
    normalize_phone,
)
from backend.auth.sms import SMSProvider, ConsoleProvider, get_sms_provider

__all__ = [
    "JWT_SECRET",
    "ACCESS_TOKEN_MINUTES",
    "REFRESH_TOKEN_DAYS",
    "OTP_PROVIDER",
    "IS_PRODUCTION",
    "assert_production_config",
    "get_current_user",
    "require_role",
    "auth_router",
    "admin_router",
    "create_access_token",
    "decode_access_token",
    "generate_otp",
    "generate_refresh_token",
    "hash_secret",
    "verify_secret",
    "normalize_phone",
    "SMSProvider",
    "ConsoleProvider",
    "get_sms_provider",
]
