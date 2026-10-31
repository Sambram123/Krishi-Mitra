"""Tests for FastAPI backend server endpoints."""

import uuid
from unittest.mock import patch
import pytest

from fastapi.testclient import TestClient
from backend.server import app, sessions
from backend.db.models import User
from backend.auth import get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_auth():
    """Provides a default authenticated farmer user for endpoint integration tests."""
    test_user = User(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        phone="+919876543210",
        name="Test Farmer",
        preferred_language="kn",
        role="farmer",
    )
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_health_endpoint():
    """Verify health endpoint returns status, provider, and model info."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "provider" in data
    assert "model" in data
    assert "has_groq_key" in data
    assert "has_sarvam_key" in data


def test_chat_endpoint_turn():
    """Verify chat endpoint accepts message and returns structured response."""
    payload = {
        "session_id": "test_session_unit",
        "message": "ನಮ್ಮದು ಮೂರು ಎಕರೆ ಹೊಲ",
        "language": "kn"
    }
    with patch.dict("os.environ", {"GROQ_API_KEY": "", "SARVAM_API_KEY": ""}):
        response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session_unit"
    assert "reply" in data
    assert "farmer_profile" in data
    assert "evaluation_results" in data
    assert "is_profile_complete" in data
    assert isinstance(data["evaluation_results"], list)


def test_chat_endpoint_uses_groq_adapter_and_preserves_response_contract():
    sessions.pop("groq_adapter_test", None)
    result = {
        "reply": "Tell me your district.",
        "profile": {"district": "Mandya", "land_acres": 2.5, "crops": ["Sugarcane"]},
        "evaluations": [{"scheme_name_en": "Example"}],
        "show_evaluations": True,
        "missing_slots": ["irrigation type"],
        "audio": None,
        "mime_type": None,
        "model_mode": "Groq",
    }
    with patch("backend.server.run_groq_chat", return_value=result) as chat:
        response = client.post("/api/chat", json={
            "session_id": "groq_adapter_test",
            "message": "Can I get a subsidy?",
            "language": "en",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Tell me your district."
    assert data["farmer_profile"]["district"] == "Mandya"
    assert data["evaluation_results"] == [{"scheme_name_en": "Example"}]
    assert data["missing_slots"] == ["irrigation type"]
    assert data["model_mode"] == "Groq"
    assert chat.call_args.args[0]["history"] == []


def test_voice_endpoint_passes_recording_to_sarvam_adapter():
    sessions.pop("voice_adapter_test", None)
    result = {
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
    with patch("backend.server.handle_voice_turn", return_value=result) as voice:
        response = client.post("/api/voice-turn", json={
            "session_id": "voice_adapter_test",
            "audio": "c2FtcGxl",
            "mime_type": "audio/webm",
            "recording_duration_ms": 1800,
            "language": "kn",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == "ನಮಸ್ಕಾರ"
    assert data["audio"] == "d2F2"
    assert data["farmer_profile"]["district"] == "Mandya"
    assert voice.call_args.args[0]["audio"] == "c2FtcGxl"
    assert voice.call_args.args[0]["recording_duration_ms"] == 1800


def test_chat_endpoint_keeps_profile_and_recent_turns_for_follow_ups():
    session_id = "chat_follow_up_test"
    sessions.pop(session_id, None)
    results = [
        {
            "reply": "What district is your farm in?",
            "language": "en",
            "profile": {"land_acres": 2.5, "crops": ["Sugarcane"]},
            "evaluations": [],
            "show_evaluations": False,
            "missing_slots": [],
        },
        {
            "reply": "Thanks, I have those details.",
            "language": "en",
            "profile": {"district": "Mandya", "land_acres": 2.5, "crops": ["Sugarcane"]},
            "evaluations": [],
            "show_evaluations": False,
            "missing_slots": [],
        },
    ]
    with patch("backend.server.run_groq_chat", side_effect=results) as chat:
        client.post("/api/chat", json={
            "session_id": session_id,
            "message": "I have 2.5 acres of sugarcane.",
            "language": "en",
        })
        response = client.post("/api/chat", json={
            "session_id": session_id,
            "message": "My farm is in Mandya.",
            "language": "en",
        })

    assert response.status_code == 200
    second_payload = chat.call_args_list[1].args[0]
    assert second_payload["profile"]["land_acres"] == 2.5
    assert second_payload["profile"]["crops"] == ["Sugarcane"]
    assert second_payload["history"] == [
        {"role": "user", "content": "I have 2.5 acres of sugarcane."},
        {"role": "assistant", "content": "What district is your farm in?"},
    ]
