"""
Tests for Krishi Mitra Backend Idempotency (Chat & Voice Endpoints)
"""

import time
import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.server import app
from backend.idempotency import get_idempotency_store, InMemoryIdempotencyStore
from backend.db.database import SessionLocal
from backend.db.models import User, Consent, utc_now
from backend.auth.security import create_access_token


@pytest.fixture(autouse=True)
def clean_idempotency():
    store = get_idempotency_store()
    store.clear()
    yield
    store.clear()


@pytest.fixture
def auth_headers():
    db = SessionLocal()
    phone = f"+9198{uuid.uuid4().hex[:8]}"
    user = User(
        id=uuid.uuid4(),
        phone=phone,
        name="Idempotency Farmer",
        preferred_language="kn",
        role="farmer",
    )
    db.add(user)
    db.commit()
    token = create_access_token(str(user.id), user.phone, user.role)
    db.close()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def voice_auth_headers():
    db = SessionLocal()
    phone = f"+9198{uuid.uuid4().hex[:8]}"
    user = User(
        id=uuid.uuid4(),
        phone=phone,
        name="Voice Idempotency Farmer",
        preferred_language="kn",
        role="farmer",
    )
    db.add(user)
    db.flush()
    # Grant active voice consent
    consent = Consent(
        id=uuid.uuid4(),
        user_id=user.id,
        purpose="voice_recording",
        policy_version="1.0",
        granted=True,
        granted_at=utc_now(),
        revoked_at=None,
    )
    db.add(consent)
    db.commit()
    token = create_access_token(str(user.id), user.phone, user.role)
    db.close()
    return {"Authorization": f"Bearer {token}"}


def test_in_memory_idempotency_store_crud():
    store = InMemoryIdempotencyStore()
    key = "test-uuid-001"
    
    assert store.get(key) is None
    assert store.is_in_flight(key) is False
    
    assert store.start_in_flight(key, ttl_seconds=2) is True
    assert store.is_in_flight(key) is True
    # Can't start again while in flight
    assert store.start_in_flight(key, ttl_seconds=2) is False
    
    # Set result
    store.set(key, 200, {"reply": "Namaskara"}, ttl_seconds=1)
    assert store.is_in_flight(key) is False
    
    cached = store.get(key)
    assert cached is not None
    code, data = cached
    assert code == 200
    assert data["reply"] == "Namaskara"
    
    # Wait for TTL expiry
    time.sleep(1.1)
    assert store.get(key) is None


def test_chat_endpoint_idempotency(auth_headers):
    client = TestClient(app)
    key = str(uuid.uuid4())
    headers = {**auth_headers, "Idempotency-Key": key}
    
    payload = {
        "session_id": "idem_chat_sess",
        "message": "ನಮಸ್ಕಾರ, ನನಗೆ 2 ಎಕರೆ ಜಮೀನಿದೆ",
        "language": "kn"
    }
    
    # First request: STORED
    res1 = client.post("/api/chat", json=payload, headers=headers)
    assert res1.status_code == 200
    assert res1.headers.get("Idempotency-Key") == key
    assert res1.headers.get("X-Idempotency-Status") == "STORED"
    data1 = res1.json()
    assert "reply" in data1
    
    # Second request with identical key: HIT with exact same response
    res2 = client.post("/api/chat", json=payload, headers=headers)
    assert res2.status_code == 200
    assert res2.headers.get("Idempotency-Key") == key
    assert res2.headers.get("X-Idempotency-Status") == "HIT"
    data2 = res2.json()
    assert data2["reply"] == data1["reply"]
    assert data2["session_id"] == data1["session_id"]
    
    # Request with different key gets a fresh run
    diff_key = str(uuid.uuid4())
    diff_headers = {**auth_headers, "Idempotency-Key": diff_key}
    res3 = client.post("/api/chat", json=payload, headers=diff_headers)
    assert res3.status_code == 200
    assert res3.headers.get("X-Idempotency-Status") == "STORED"


def test_voice_turn_idempotency(voice_auth_headers):
    client = TestClient(app)
    key = str(uuid.uuid4())
    headers = {**voice_auth_headers, "Idempotency-Key": key}
    
    mock_result = {
        "reply": "ಮಂಡ್ಯದಲ್ಲಿ ಹನಿ ನೀರಾವರಿ ಸಬ್ಸಿಡಿ ಲಭ್ಯವಿದೆ.",
        "transcript": "ಮಂಡ್ಯ ಹನಿ ನೀರಾವರಿ",
        "detected_language": "kn",
        "audio": "d2F2YXVkaW8=",
        "mime_type": "audio/wav",
        "model_mode": "groq",
        "profile": {"district": "Mandya"},
        "evaluations": [],
        "show_evaluations": False,
        "language": "kn",
    }
    
    dummy_audio = "AAAA" * 100
    payload = {
        "session_id": "idem_voice_sess",
        "audio": dummy_audio,
        "mime_type": "audio/webm",
        "language": "kn"
    }
    
    with patch("backend.server.handle_voice_turn", return_value=mock_result) as mock_vt:
        # First request: STORED
        res1 = client.post("/api/voice-turn", json=payload, headers=headers)
        assert res1.status_code == 200
        assert res1.headers.get("Idempotency-Key") == key
        assert res1.headers.get("X-Idempotency-Status") == "STORED"
        data1 = res1.json()
        assert mock_vt.call_count == 1
        
        # Second request with identical key: HIT, mock should NOT be called again!
        res2 = client.post("/api/voice-turn", json=payload, headers=headers)
        assert res2.status_code == 200
        assert res2.headers.get("Idempotency-Key") == key
        assert res2.headers.get("X-Idempotency-Status") == "HIT"
        data2 = res2.json()
        assert data2["reply"] == data1["reply"]
        assert data2["transcript"] == data1["transcript"]
        assert mock_vt.call_count == 1  # Verified: NOT executed twice!
