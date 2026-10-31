"""
Krishi Mitra — Voice Consent & Privacy Test Suite (DPDP 2023)
Verifies:
  - Voice endpoints blocked without explicit consent (403 with code CONSENT_REQUIRED)
  - Voice endpoints allowed when active consent exists
  - Voice endpoints blocked immediately after withdrawal
  - Voice endpoints blocked after policy version bump (forcing re-consent)
  - Immutable append-only audit trail preservation
  - Data deletion (right to erasure) purges user sessions & transcripts
  - Cross-user consent isolation (User A cannot access User B's consents)
  - History opt-in control (transcripts stored only if save_history=True)
"""

import os
import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.server import app, sessions
from backend.db.database import SessionLocal, init_db
from backend.db.models import User, Consent, OTPCode, RefreshToken
from backend.auth.security import create_access_token
from backend.consent.policy import (
    CURRENT_POLICY_VERSION,
    set_current_policy_version,
)


@pytest.fixture(autouse=True)
def clean_database():
    """Initializes tables and ensures clean test state."""
    init_db()
    set_current_policy_version("1.0")
    db = SessionLocal()
    try:
        db.query(Consent).delete()
        db.query(RefreshToken).delete()
        db.query(OTPCode).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    sessions.clear()
    yield
    set_current_policy_version("1.0")


@pytest.fixture
def client():
    return TestClient(app)


def create_test_user(phone="+919888877777", save_history=False):
    db = SessionLocal()
    user = User(
        id=uuid.uuid4(),
        phone=phone,
        name="Sharanappa",
        preferred_language="kn",
        role="farmer",
        save_history=save_history,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id), user.phone, user.role, user.preferred_language)
    db.close()
    return user, token


def test_voice_endpoint_blocked_without_consent(client):
    """Voice turn endpoint must return 403 with code CONSENT_REQUIRED when consent is absent."""
    user, token = create_test_user()

    mock_voice_payload = {
        "audio": "c2FtcGxl",
        "mime_type": "audio/webm",
        "recording_duration_ms": 1500,
        "language": "kn",
    }

    res = client.post(
        "/api/voice-turn",
        json=mock_voice_payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["code"] == "CONSENT_REQUIRED"
    assert "Explicit consent for voice recording and processing is required" in detail["message"]


def test_voice_endpoint_allowed_with_valid_consent(client):
    """Voice endpoint executes normally when explicit consent has been granted for current policy."""
    user, token = create_test_user()

    # Grant voice consent
    grant_res = client.post(
        "/api/consent",
        json={"purpose": "voice_recording", "policy_version": "1.0", "granted": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert grant_res.status_code == 200
    assert grant_res.json()["voice_consent_active"] is True

    mock_result = {
        "transcript": "ನಮಸ್ಕಾರ",
        "detected_language": "kn-IN",
        "reply": "ನಮಸ್ಕಾರ, ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
        "audio": "d2F2",
        "mime_type": "audio/wav",
        "profile": {"district": "Mandya"},
        "evaluations": [],
        "show_evaluations": False,
        "missing_slots": [],
        "model_mode": "Sarvam + Groq",
    }

    with patch("backend.server.handle_voice_turn", return_value=mock_result):
        res = client.post(
            "/api/voice-turn",
            json={
                "audio": "c2FtcGxl",
                "mime_type": "audio/webm",
                "recording_duration_ms": 1500,
                "language": "kn",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert res.status_code == 200
    assert res.json()["transcript"] == "ನಮಸ್ಕಾರ"


def test_voice_endpoint_blocked_after_consent_withdrawal(client):
    """Withdrawing voice consent immediately revokes access to the voice endpoint."""
    user, token = create_test_user()

    # 1. Grant consent
    client.post(
        "/api/consent",
        json={"purpose": "voice_recording", "policy_version": "1.0", "granted": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 2. Withdraw consent
    withdraw_res = client.delete(
        "/api/consent/voice",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert withdraw_res.status_code == 200
    assert withdraw_res.json()["voice_consent_active"] is False

    # 3. Voice endpoint call must now be rejected
    res = client.post(
        "/api/voice-turn",
        json={
            "audio": "c2FtcGxl",
            "mime_type": "audio/webm",
            "recording_duration_ms": 1500,
            "language": "kn",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "CONSENT_REQUIRED"


def test_voice_endpoint_blocked_after_policy_version_bump(client):
    """Bumping policy version from 1.0 to 2.0 forces re-consent."""
    user, token = create_test_user()

    # User consents to policy 1.0
    client.post(
        "/api/consent",
        json={"purpose": "voice_recording", "policy_version": "1.0", "granted": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Admin/system bumps policy version to 2.0
    set_current_policy_version("2.0")

    # Previous consent for 1.0 is no longer valid for 2.0
    res = client.post(
        "/api/voice-turn",
        json={
            "audio": "c2FtcGxl",
            "mime_type": "audio/webm",
            "recording_duration_ms": 1500,
            "language": "kn",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "CONSENT_REQUIRED"
    assert res.json()["detail"]["policy_version"] == "2.0"

    # User re-consents to version 2.0
    reconsent_res = client.post(
        "/api/consent",
        json={"purpose": "voice_recording", "policy_version": "2.0", "granted": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reconsent_res.status_code == 200
    assert reconsent_res.json()["voice_consent_active"] is True


def test_consent_audit_trail_is_append_only(client):
    """Verifies that grant, withdraw, re-grant appends rows and preserves audit history."""
    user, token = create_test_user()

    # Action 1: Grant
    client.post("/api/consent", json={"purpose": "voice_recording", "policy_version": "1.0", "granted": True}, headers={"Authorization": f"Bearer {token}"})
    # Action 2: Withdraw
    client.delete("/api/consent/voice", headers={"Authorization": f"Bearer {token}"})
    # Action 3: Re-grant
    client.post("/api/consent", json={"purpose": "voice_recording", "policy_version": "1.0", "granted": True}, headers={"Authorization": f"Bearer {token}"})

    db = SessionLocal()
    rows = db.query(Consent).filter(Consent.user_id == user.id, Consent.purpose == "voice_recording").order_by(Consent.created_at.asc()).all()
    db.close()

    assert len(rows) == 3
    assert rows[0].granted is True
    assert rows[0].revoked_at is None
    assert rows[1].granted is False
    assert rows[1].revoked_at is not None
    assert rows[2].granted is True
    assert rows[2].revoked_at is None


def test_user_cannot_access_another_users_consents(client):
    """Users can only view their own consent audit trail."""
    user_a, token_a = create_test_user(phone="+919100000001")
    user_b, token_b = create_test_user(phone="+919200000002")

    client.post("/api/consent", json={"purpose": "voice_recording", "policy_version": "1.0", "granted": True}, headers={"Authorization": f"Bearer {token_a}"})

    # User B fetches consents
    res_b = client.get("/api/me/consents", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["user_id"] == str(user_b.id)
    assert len(data_b["audit_trail"]) == 0
    assert data_b["voice_consent_active"] is False


def test_data_deletion_purges_sessions_and_transcripts(client):
    """DELETE /api/me/data purges active sessions, transcripts, and revokes consent."""
    user, token = create_test_user(save_history=True)

    client.post("/api/consent", json={"purpose": "voice_recording", "policy_version": "1.0", "granted": True}, headers={"Authorization": f"Bearer {token}"})

    # Create active session
    sid = "sess_to_delete"
    sessions[sid] = {"user_id": str(user.id), "profile": {}, "history": [{"role": "user", "content": "hello"}]}

    assert sid in sessions

    del_res = client.delete("/api/me/data", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 200
    assert del_res.json()["purged_sessions"] == 1
    assert del_res.json()["voice_consent_active"] is False

    # Session is completely purged
    assert sid not in sessions

    # Consent is now inactive
    consents_res = client.get("/api/me/consents", headers={"Authorization": f"Bearer {token}"})
    assert consents_res.json()["voice_consent_active"] is False


def test_transcript_storage_opt_in_control(client):
    """
    DPDP Data Minimisation:
    When save_history is False (default), transcripts are never saved to session['history'].
    When save_history is True, turns are retained.
    """
    user_no_history, token_no_history = create_test_user(phone="+919300000001", save_history=False)
    user_history, token_history = create_test_user(phone="+919400000002", save_history=True)

    mock_chat = {
        "reply": "ಇದು ಸಹಾಯ ಮಾಡುತ್ತದೆ",
        "language": "kn",
        "profile": {"district": "Hassan"},
        "evaluations": [],
        "show_evaluations": False,
        "missing_slots": [],
    }

    with patch("backend.server.run_groq_chat", return_value=mock_chat):
        # 1. User without history opt-in
        client.post(
            "/api/chat",
            json={"session_id": "sess_no_hist", "message": "ನನ್ನದು 2 ಎಕರೆ", "language": "kn"},
            headers={"Authorization": f"Bearer {token_no_history}"},
        )
        assert len(sessions["sess_no_hist"]["history"]) == 0  # Not stored!

        # 2. User with history opt-in
        client.post(
            "/api/chat",
            json={"session_id": "sess_with_hist", "message": "ನನ್ನದು 2 ಎಕರೆ", "language": "kn"},
            headers={"Authorization": f"Bearer {token_history}"},
        )
        assert len(sessions["sess_with_hist"]["history"]) == 2  # Stored!
