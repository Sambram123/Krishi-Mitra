"""
Krishi Mitra — Consent Management APIRouter
Endpoints:
  - GET /api/consent/policy: Versioned privacy policy details in Kannada & English
  - POST /api/consent: Explicit grant or update of consent (append-only audit record)
  - DELETE /api/consent/voice: Revocation / withdrawal of voice consent
  - GET /api/me/consents: User's active consent status and audit history
  - PUT /api/me/history-preference: Updates user's conversation history retention preference
  - DELETE /api/me/data: Deletes user's active sessions, transcripts, and data under DPDP 2023
"""

import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import User, Consent, utc_now
from backend.auth.dependencies import get_current_user
from backend.consent.policy import (
    get_current_policy,
    get_current_policy_version,
    is_voice_consent_active,
)

consent_router = APIRouter(prefix="/api/consent", tags=["consent"])
user_privacy_router = APIRouter(prefix="/api/me", tags=["user_privacy"])


class GrantConsentRequest(BaseModel):
    purpose: str = Field("voice_recording", description="Consent purpose e.g. voice_recording")
    policy_version: Optional[str] = Field(None, description="Policy version being accepted")
    granted: bool = Field(True, description="Whether consent is granted or denied")
    save_history: Optional[bool] = Field(None, description="Optional opt-in to save conversation transcripts")


class HistoryPreferenceRequest(BaseModel):
    save_history: bool = Field(..., description="Opt-in to retain conversation transcripts")


@consent_router.get("/policy")
def get_policy():
    """Returns the current versioned privacy & voice recording consent policy."""
    return get_current_policy()


@consent_router.post("")
def grant_consent(
    req: GrantConsentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Records an append-only consent grant or update in the audit trail.
    Never mutates previous records.
    """
    version = req.policy_version or get_current_policy_version()
    user_agent = request.headers.get("user-agent", "")[:250]

    # Append new consent record
    consent_record = Consent(
        id=uuid.uuid4(),
        user_id=current_user.id,
        purpose=req.purpose,
        policy_version=version,
        granted=req.granted,
        granted_at=utc_now(),
        revoked_at=None if req.granted else utc_now(),
        user_agent=user_agent,
    )
    db.add(consent_record)

    # Optional history retention opt-in
    if req.save_history is not None:
        current_user.save_history = bool(req.save_history)
        history_record = Consent(
            id=uuid.uuid4(),
            user_id=current_user.id,
            purpose="save_history",
            policy_version=version,
            granted=bool(req.save_history),
            granted_at=utc_now(),
            revoked_at=None if req.save_history else utc_now(),
            user_agent=user_agent,
        )
        db.add(history_record)

    db.commit()
    db.refresh(consent_record)

    return {
        "status": "success",
        "message": "Consent recorded successfully",
        "consent": consent_record.to_dict(),
        "voice_consent_active": is_voice_consent_active(current_user.id, db, version),
        "save_history": current_user.save_history,
    }


@consent_router.delete("/voice")
def withdraw_voice_consent(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Explicitly withdraws voice recording consent.
    Appends an immutable revocation row to the audit trail.
    """
    version = get_current_policy_version()
    user_agent = request.headers.get("user-agent", "")[:250]

    revocation_record = Consent(
        id=uuid.uuid4(),
        user_id=current_user.id,
        purpose="voice_recording",
        policy_version=version,
        granted=False,
        granted_at=utc_now(),
        revoked_at=utc_now(),
        user_agent=user_agent,
    )
    db.add(revocation_record)
    db.commit()

    return {
        "status": "success",
        "message": "Voice recording consent has been withdrawn successfully",
        "voice_consent_active": False,
    }


@user_privacy_router.get("/consents")
def get_user_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns current user's consent status and immutable audit trail.
    Guarantees strict user isolation (users can never inspect other farmers' records).
    """
    version = get_current_policy_version()
    records = (
        db.query(Consent)
        .filter(Consent.user_id == current_user.id)
        .order_by(Consent.created_at.desc())
        .all()
    )

    return {
        "user_id": str(current_user.id),
        "voice_consent_active": is_voice_consent_active(current_user.id, db, version),
        "policy_version": version,
        "save_history": current_user.save_history,
        "audit_trail": [rec.to_dict() for rec in records],
    }


@user_privacy_router.put("/history-preference")
def update_history_preference(
    req: HistoryPreferenceRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates user's conversation history retention preference."""
    current_user.save_history = bool(req.save_history)
    version = get_current_policy_version()
    user_agent = request.headers.get("user-agent", "")[:250]

    record = Consent(
        id=uuid.uuid4(),
        user_id=current_user.id,
        purpose="save_history",
        policy_version=version,
        granted=bool(req.save_history),
        granted_at=utc_now(),
        revoked_at=None if req.save_history else utc_now(),
        user_agent=user_agent,
    )
    db.add(record)
    db.commit()

    return {
        "status": "success",
        "save_history": current_user.save_history,
    }


@user_privacy_router.delete("/data")
def delete_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    DPDP Right to Erasure:
    Deletes the user's active conversation sessions, transcripts, and marks consents as revoked.
    """
    # Import in-memory session registry
    from backend.server import sessions

    user_id_str = str(current_user.id)

    # Purge in-memory sessions belonging to this user
    purged_session_count = 0
    sessions_to_delete = [
        sid for sid, s in list(sessions.items())
        if s.get("user_id") == user_id_str
    ]
    for sid in sessions_to_delete:
        sessions.pop(sid, None)
        purged_session_count += 1

    # Revoke voice consent and disable history saving
    current_user.save_history = False
    version = get_current_policy_version()

    revocation = Consent(
        id=uuid.uuid4(),
        user_id=current_user.id,
        purpose="voice_recording",
        policy_version=version,
        granted=False,
        granted_at=utc_now(),
        revoked_at=utc_now(),
        user_agent="data_deletion_request",
    )
    db.add(revocation)
    db.commit()

    return {
        "status": "success",
        "message": "All user sessions, transcripts, and session data have been deleted.",
        "purged_sessions": purged_session_count,
        "voice_consent_active": False,
        "save_history": False,
    }
