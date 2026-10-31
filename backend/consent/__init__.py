"""
Krishi Mitra — Consent Management Package
"""

from backend.consent.policy import (
    CURRENT_POLICY_VERSION,
    get_current_policy_version,
    set_current_policy_version,
    get_current_policy,
    is_voice_consent_active,
)
from backend.consent.dependencies import require_voice_consent
from backend.consent.router import consent_router, user_privacy_router

__all__ = [
    "CURRENT_POLICY_VERSION",
    "get_current_policy_version",
    "set_current_policy_version",
    "get_current_policy",
    "is_voice_consent_active",
    "require_voice_consent",
    "consent_router",
    "user_privacy_router",
]
