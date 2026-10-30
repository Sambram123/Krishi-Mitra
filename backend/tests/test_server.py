"""Tests for FastAPI backend server endpoints."""

from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint returns status, provider, and model info."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "provider" in data
    assert "model" in data
    assert "has_gemini_key" in data


def test_chat_endpoint_turn():
    """Verify chat endpoint accepts message and returns structured response."""
    payload = {
        "session_id": "test_session_unit",
        "message": "ನಮ್ಮದು ಮೂರು ಎಕರೆ ಹೊಲ",
        "language": "kn"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session_unit"
    assert "reply" in data
    assert "farmer_profile" in data
    assert "evaluation_results" in data
    assert "is_profile_complete" in data
    assert isinstance(data["evaluation_results"], list)
