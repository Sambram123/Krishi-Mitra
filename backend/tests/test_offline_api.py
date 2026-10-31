"""
Tests for Offline Support, App Shell Assets & Idempotent Voice/Chat Recovery
"""

import json
import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.server import app
from backend.idempotency import get_idempotency_store
from backend.db.database import SessionLocal
from backend.db.models import User, Consent, utc_now
from backend.auth.security import create_access_token


@pytest.fixture(autouse=True)
def clean_store():
    store = get_idempotency_store()
    store.clear()
    yield
    store.clear()


@pytest.fixture
def test_user_headers():
    db = SessionLocal()
    phone = f"+9198{uuid.uuid4().hex[:8]}"
    user = User(
        id=uuid.uuid4(),
        phone=phone,
        name="Offline Test Farmer",
        preferred_language="kn",
        role="farmer",
    )
    db.add(user)
    db.commit()
    token = create_access_token(str(user.id), user.phone, user.role)
    db.close()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def voice_user_headers():
    db = SessionLocal()
    phone = f"+9198{uuid.uuid4().hex[:8]}"
    user = User(
        id=uuid.uuid4(),
        phone=phone,
        name="Voice Offline Farmer",
        preferred_language="kn",
        role="farmer",
    )
    db.add(user)
    db.flush()
    consent = Consent(
        id=uuid.uuid4(),
        user_id=user.id,
        purpose="voice_recording",
        policy_version="1.0",
        granted=True,
        granted_at=utc_now(),
    )
    db.add(consent)
    db.commit()
    token = create_access_token(str(user.id), user.phone, user.role)
    db.close()
    return {"Authorization": f"Bearer {token}"}


def test_service_worker_asset_serving():
    client = TestClient(app)
    res = client.get("/sw.js")
    assert res.status_code == 200
    assert "javascript" in res.headers.get("content-type", "")
    assert "no-cache" in res.headers.get("cache-control", "")
    content = res.text
    assert "krishi-shell-v1" in content
    # Verify that authenticated API endpoints are never cached
    assert "url.pathname.startsWith('/api/')" in content


def test_offline_faq_asset_structure():
    client = TestClient(app)
    res = client.get("/offline_faq.json")
    assert res.status_code == 200
    data = res.json()
    assert "schemes" in data
    assert len(data["schemes"]) >= 5
    assert "last_researched" in data
    assert "disclaimer_kn" in data
    assert "disclaimer_en" in data
    
    # Verify key schemes are present
    codes = [s["code"] for s in data["schemes"]]
    assert "PM_KISAN" in codes
    assert "PMFBY" in codes
    assert "PMKSY_DRIP" in codes
    assert "SMAM_MACHINERY" in codes
    assert "GANGA_KALYANA" in codes


def test_idempotent_retry_prevents_duplicate_ai_processing(test_user_headers):
    client = TestClient(app)
    idempotency_key = str(uuid.uuid4())
    headers = {**test_user_headers, "Idempotency-Key": idempotency_key}
    
    payload = {
        "session_id": "test_offline_sess_1",
        "message": "ನನಗೆ ಕಲಬುರಗಿಯಲ್ಲಿ 3 ಎಕರೆ ಜಮೀನಿದೆ, ಬೆಳೆ ವಿಮೆ ಪರಿಹಾರ ಬರುತ್ತಾ?",
        "language": "kn"
    }
    
    # 1. First attempt: processed by backend and stored
    res1 = client.post("/api/chat", json=payload, headers=headers)
    assert res1.status_code == 200
    assert res1.headers.get("Idempotency-Key") == idempotency_key
    assert res1.headers.get("X-Idempotency-Status") == "STORED"
    data1 = res1.json()
    
    # 2. Simulate client reconnecting and auto-sending with identical Idempotency-Key
    res2 = client.post("/api/chat", json=payload, headers=headers)
    assert res2.status_code == 200
    assert res2.headers.get("Idempotency-Key") == idempotency_key
    assert res2.headers.get("X-Idempotency-Status") == "HIT"
    data2 = res2.json()
    assert data1["reply"] == data2["reply"]
    assert data1["session_id"] == data2["session_id"]


def test_voice_turn_idempotent_recovery_after_drop(voice_user_headers):
    client = TestClient(app)
    idempotency_key = str(uuid.uuid4())
    headers = {**voice_user_headers, "Idempotency-Key": idempotency_key}
    
    mock_result = {
        "reply": "ನಿಮ್ಮ 3 ಎಕರೆ ತೊಗರಿ ಬೆಳೆಗೆ ಸಂರಕ್ಷಣೆ ವಿಮೆ ಪರಿಹಾರ ಲಭ್ಯವಿದೆ.",
        "transcript": "ಕಲಬುರಗಿ 3 ಎಕರೆ ತೊಗರಿ ಬೆಳೆ ಒಣಗಿದೆ",
        "detected_language": "kn",
        "audio": "d2F2YXVkaW8xMjM=",
        "mime_type": "audio/wav",
        "model_mode": "groq",
        "profile": {"district": "Kalaburagi", "land_acres": 3.0},
        "evaluations": [],
        "show_evaluations": False,
        "language": "kn",
    }
    
    payload = {
        "session_id": "offline_voice_recovery",
        "audio": "AAAA" * 50,
        "mime_type": "audio/webm",
        "recording_duration_ms": 3500,
        "language": "kn"
    }
    
    with patch("backend.server.handle_voice_turn", return_value=mock_result) as mock_vt:
        # First attempt uploaded
        res1 = client.post("/api/voice-turn", json=payload, headers=headers)
        assert res1.status_code == 200
        assert res1.headers.get("X-Idempotency-Status") == "STORED"
        assert mock_vt.call_count == 1
        
        # Second attempt sent after client reconnects: HIT returned without re-invoking voice processing
        res2 = client.post("/api/voice-turn", json=payload, headers=headers)
        assert res2.status_code == 200
        assert res2.headers.get("X-Idempotency-Status") == "HIT"
        assert mock_vt.call_count == 1
        
        data2 = res2.json()
        assert data2["transcript"] == mock_result["transcript"]
        assert data2["reply"] == mock_result["reply"]
