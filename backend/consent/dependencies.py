"""
Krishi Mitra — Server-Side Consent Enforcement Dependency
Guarantees that no voice processing or audio upload can execute without explicit,
unrevoked consent for the active policy version under DPDP 2023.
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User
from backend.auth.dependencies import get_current_user
from backend.consent.policy import (
    is_voice_consent_active,
    get_current_policy_version,
)


def require_voice_consent(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """
    Server-side gatekeeper for all voice/audio processing endpoints.
    Enforces active, unrevoked consent matching the active policy version.
    Returns 403 with code CONSENT_REQUIRED when consent is absent, revoked, or outdated.
    """
    current_version = get_current_policy_version()

    if not is_voice_consent_active(current_user.id, db, current_version):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "CONSENT_REQUIRED",
                "error": "CONSENT_REQUIRED",
                "message": (
                    "Explicit consent for voice recording and processing is required. "
                    "Please review and accept the voice privacy policy before using audio features."
                ),
                "policy_version": current_version,
            },
        )

    return current_user
