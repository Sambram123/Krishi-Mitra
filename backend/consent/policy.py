"""
Krishi Mitra — Versioned Consent Policy Configuration & Helpers
DPDP 2023 compliant consent policies and active status evaluation.
"""

import os
import json
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.db.models import Consent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_FILE_PATH = os.path.join(BASE_DIR, "policy_v1.json")

# Current enforced policy version; bumping this value forces all users to re-consent.
CURRENT_POLICY_VERSION = "1.0"


def get_current_policy_version() -> str:
    return CURRENT_POLICY_VERSION


def set_current_policy_version(version: str) -> None:
    """Dynamically adjusts the active policy version (used for re-consent testing)."""
    global CURRENT_POLICY_VERSION
    CURRENT_POLICY_VERSION = version


def get_current_policy() -> Dict[str, Any]:
    """Loads the canonical versioned consent policy JSON."""
    if os.path.exists(POLICY_FILE_PATH):
        with open(POLICY_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["version"] = CURRENT_POLICY_VERSION
            return data
    return {
        "version": CURRENT_POLICY_VERSION,
        "effective_date": "2026-10-31",
        "purposes": {
            "voice_recording": {
                "title_kn": "ಧ್ವನಿ ರೆಕಾರ್ಡಿಂಗ್ ಮತ್ತು ಸಂಸ್ಕರಣಾ ಒಪ್ಪಿಗೆ",
                "title_en": "Voice Recording & Processing Consent",
            }
        }
    }


def is_voice_consent_active(
    user_id: uuid.UUID,
    db: Session,
    policy_version: Optional[str] = None,
) -> bool:
    """
    Evaluates whether the user currently has active, unrevoked consent for voice recording
    under the current (or specified) policy version.
    Follows the append-only audit trail: looks up the latest record for that purpose & version.
    """
    version = policy_version or CURRENT_POLICY_VERSION

    latest_record = (
        db.query(Consent)
        .filter(
            Consent.user_id == user_id,
            Consent.purpose == "voice_recording",
            Consent.policy_version == version,
        )
        .order_by(Consent.created_at.desc())
        .first()
    )

    if not latest_record:
        return False

    return bool(latest_record.granted and latest_record.revoked_at is None)
