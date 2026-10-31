"""
Krishi Mitra — Authentication and Authorization Test Suite
Verifies:
  - Phone + OTP login flow
  - Rate limiting (per phone and IP)
  - OTP expiry
  - OTP attempt limits (max 5)
  - JWT access token validation
  - Protected endpoints returning 401
  - Rotating refresh tokens & cookie handling
  - Revoked refresh token reuse detection (family-wide revocation)
  - RBAC: require_role('admin') returning 403 for farmers and 200 for admins
  - IDOR prevention: cross-user conversation session access blocked with 403
  - Logout flow
  - Production startup assertions (JWT_SECRET requirement)
"""

import os
import uuid
from datetime import timedelta
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from backend.server import app, sessions
from backend.db.database import get_db, SessionLocal, init_db, Base, engine
from backend.db.models import User, OTPCode, RefreshToken, utc_now
from backend.auth.config import assert_production_config
from backend.auth.rate_limiter import reset_rate_limits
from backend.auth.security import hash_secret, create_access_token
from backend.auth.router import ensure_utc



@pytest.fixture(autouse=True)
def setup_clean_db():
    """Initializes tables and cleans rate limits and DB records between tests."""
    init_db()
    reset_rate_limits()
    db = SessionLocal()
    try:
        db.query(RefreshToken).delete()
        db.query(OTPCode).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    sessions.clear()
    yield


@pytest.fixture
def client():
    # Use real dependency resolution (no override)
    return TestClient(app)


def test_request_otp_success_and_stored_hashed(client):
    """Verify requesting OTP generates 6 digits, stores hashed code, and does not store plaintext."""
    res = client.post("/api/auth/request-otp", json={"phone": "+919876543210"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "9876543210" not in data["phone"]  # Masked in response

    db = SessionLocal()
    otp_record = db.query(OTPCode).filter(OTPCode.phone == "+919876543210").first()
    db.close()

    assert otp_record is not None
    assert otp_record.attempts == 0
    assert len(otp_record.code_hash) == 64  # SHA-256 hash length
    assert ensure_utc(otp_record.expires_at) > utc_now()


def test_request_otp_invalid_phone(client):
    """Verify invalid phone numbers are rejected."""
    res = client.post("/api/auth/request-otp", json={"phone": "123"})
    assert res.status_code == 400
    assert "Invalid phone number format" in res.json()["detail"]


def test_request_otp_rate_limiting(client):
    """Verify rate limiter blocks excessive requests from same phone or IP."""
    phone = "+919811122233"
    for _ in range(5):
        r = client.post("/api/auth/request-otp", json={"phone": phone})
        assert r.status_code == 200

    # 6th request should hit 429
    r6 = client.post("/api/auth/request-otp", json={"phone": phone})
    assert r6.status_code == 429
    assert "Too many OTP requests" in r6.json()["detail"]


def test_verify_otp_success_provisions_user_and_tokens(client):
    """Verify valid OTP provisions farmer user, returns access token and sets refresh cookie."""
    phone = "+919988776655"
    client.post("/api/auth/request-otp", json={"phone": phone})

    db = SessionLocal()
    otp_record = db.query(OTPCode).filter(OTPCode.phone == phone).first()
    # Find OTP by testing code or seed known OTP
    known_code = "789123"
    otp_record.code_hash = hash_secret(known_code)
    db.commit()
    db.close()

    res = client.post("/api/auth/verify-otp", json={
        "phone": phone,
        "otp": known_code,
        "name": "Basavaraj",
        "preferred_language": "kn"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["name"] == "Basavaraj"
    assert data["user"]["phone"] == phone
    assert data["user"]["role"] == "farmer"

    # Verify refresh cookie was set
    assert "krishi_refresh_token" in res.cookies

    # Verify OTP was consumed
    db = SessionLocal()
    assert db.query(OTPCode).filter(OTPCode.phone == phone).count() == 0
    db.close()


def test_verify_otp_attempt_limits(client):
    """Verify wrong OTP increments attempts and locks out after 5 failures."""
    phone = "+919123456780"
    client.post("/api/auth/request-otp", json={"phone": phone})

    db = SessionLocal()
    otp_record = db.query(OTPCode).filter(OTPCode.phone == phone).first()
    otp_record.code_hash = hash_secret("123456")
    db.commit()
    db.close()

    # 4 bad attempts
    for attempt in range(1, 5):
        res = client.post("/api/auth/verify-otp", json={"phone": phone, "otp": "000000"})
        assert res.status_code == 400
        assert f"{5 - attempt} attempt(s) remaining" in res.json()["detail"]

    # 5th bad attempt
    res5 = client.post("/api/auth/verify-otp", json={"phone": phone, "otp": "000000"})
    assert res5.status_code == 400
    assert "0 attempt(s) remaining" in res5.json()["detail"]

    # 6th attempt should be blocked due to maximum attempts reached
    res6 = client.post("/api/auth/verify-otp", json={"phone": phone, "otp": "123456"})
    assert res6.status_code == 400
    assert "Maximum verification attempts exceeded" in res6.json()["detail"]


def test_verify_otp_expired(client):
    """Verify expired OTP is rejected."""
    phone = "+919555444333"
    client.post("/api/auth/request-otp", json={"phone": phone})

    db = SessionLocal()
    otp_record = db.query(OTPCode).filter(OTPCode.phone == phone).first()
    otp_record.expires_at = utc_now() - timedelta(minutes=1)
    db.commit()
    db.close()

    res = client.post("/api/auth/verify-otp", json={"phone": phone, "otp": "123456"})
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()


def test_refresh_token_rotation(client):
    """Verify refresh token rotation returns a new access token and new cookie, revoking the old token."""
    phone = "+919777888999"
    client.post("/api/auth/request-otp", json={"phone": phone})

    db = SessionLocal()
    otp_record = db.query(OTPCode).filter(OTPCode.phone == phone).first()
    otp_record.code_hash = hash_secret("654321")
    db.commit()
    db.close()

    login_res = client.post("/api/auth/verify-otp", json={"phone": phone, "otp": "654321"})
    initial_cookie = login_res.cookies.get("krishi_refresh_token")
    assert initial_cookie is not None

    refresh_res = client.post("/api/auth/refresh", cookies={"krishi_refresh_token": initial_cookie})
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    new_cookie = refresh_res.cookies.get("krishi_refresh_token")
    assert new_cookie is not None
    assert new_cookie != initial_cookie

    # Old token in DB must now be revoked
    db = SessionLocal()
    old_record = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_secret(initial_cookie)).first()
    assert old_record.revoked_at is not None
    db.close()


def test_refresh_token_reuse_detection_revokes_token_family(client):
    """Verify reuse of an already-revoked refresh token revokes all active tokens in that family."""
    phone = "+919444333222"
    client.post("/api/auth/request-otp", json={"phone": phone})

    db = SessionLocal()
    otp_record = db.query(OTPCode).filter(OTPCode.phone == phone).first()
    otp_record.code_hash = hash_secret("112233")
    db.commit()
    db.close()

    login_res = client.post("/api/auth/verify-otp", json={"phone": phone, "otp": "112233"})
    token_v1 = login_res.cookies.get("krishi_refresh_token")

    # Rotate once: v1 -> v2
    res_v2 = client.post("/api/auth/refresh", cookies={"krishi_refresh_token": token_v1})
    token_v2 = res_v2.cookies.get("krishi_refresh_token")

    # Attacker presents old token_v1
    reuse_res = client.post("/api/auth/refresh", cookies={"krishi_refresh_token": token_v1})
    assert reuse_res.status_code == 401
    assert "reuse detected" in reuse_res.json()["detail"].lower()

    # Now legitimate token_v2 must ALSO be revoked because the entire family was compromised!
    legit_res = client.post("/api/auth/refresh", cookies={"krishi_refresh_token": token_v2})
    assert legit_res.status_code == 401


def test_protected_routes_require_authentication(client):
    """Verify /api/chat and /api/auth/me return 401 without Bearer token."""
    res_me = client.get("/api/auth/me")
    assert res_me.status_code == 401
    assert "Authentication required" in res_me.json()["detail"]

    res_chat = client.post("/api/chat", json={"message": "ಯಾವ ಯೋಜನೆ ಇದೆ?"})
    assert res_chat.status_code == 401


def test_auth_me_returns_profile_with_valid_jwt(client):
    """Verify GET /api/auth/me returns farmer info when authenticated."""
    db = SessionLocal()
    user = User(
        id=uuid.uuid4(),
        phone="+919666555444",
        name="Chennappa",
        preferred_language="kn",
        role="farmer",
    )
    db.add(user)
    db.commit()
    token = create_access_token(str(user.id), user.phone, user.role, user.preferred_language)
    db.close()

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Chennappa"
    assert data["phone"] == "+919666555444"
    assert data["role"] == "farmer"


def test_role_based_access_control_admin_route(client):
    """Verify require_role blocks farmer (403) and allows admin (200)."""
    db = SessionLocal()
    farmer = User(
        id=uuid.uuid4(),
        phone="+919000000001",
        name="Farmer Dan",
        role="farmer",
    )
    admin = User(
        id=uuid.uuid4(),
        phone="+919000000002",
        name="Admin Priya",
        role="admin",
    )
    db.add_all([farmer, admin])
    db.commit()

    farmer_token = create_access_token(str(farmer.id), farmer.phone, farmer.role)
    admin_token = create_access_token(str(admin.id), admin.phone, admin.role)
    db.close()

    # Farmer gets 403 Forbidden
    res_farmer = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {farmer_token}"})
    assert res_farmer.status_code == 403
    assert "Forbidden" in res_farmer.json()["detail"]

    # Admin gets 200 OK
    res_admin = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "total_users" in data
    assert data["admin_caller"] == "+919000000002"


def test_session_idor_prevention_cross_user_denied(client):
    """
    IDOR Prevention:
    Verify User B receives 403 Forbidden when trying to access or tamper with User A's session.
    """
    db = SessionLocal()
    user_a = User(id=uuid.uuid4(), phone="+919111111111", name="User A", role="farmer")
    user_b = User(id=uuid.uuid4(), phone="+919222222222", name="User B", role="farmer")
    db.add_all([user_a, user_b])
    db.commit()

    token_a = create_access_token(str(user_a.id), user_a.phone, user_a.role)
    token_b = create_access_token(str(user_b.id), user_b.phone, user_b.role)
    db.close()

    shared_session_id = "session-idor-test-123"

    mock_chat_result = {
        "reply": "ನಮಸ್ಕಾರ ಯೂಸರ್ ಎ",
        "language": "kn",
        "profile": {"district": "Dharwad"},
        "evaluations": [],
        "show_evaluations": False,
        "missing_slots": [],
    }

    # User A initiates conversation turn
    with patch("backend.server.run_groq_chat", return_value=mock_chat_result):
        res_a = client.post(
            "/api/chat",
            json={"session_id": shared_session_id, "message": "ನಮಸ್ಕಾರ", "language": "kn"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res_a.status_code == 200

    # User B attempts to access User A's session
    with patch("backend.server.run_groq_chat", return_value=mock_chat_result):
        res_b = client.post(
            "/api/chat",
            json={"session_id": shared_session_id, "message": "Can I see User A's session?", "language": "en"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_b.status_code == 403
        assert "belongs to another user" in res_b.json()["detail"].lower()


def test_logout_revokes_token_and_clears_cookie(client):
    """Verify logout revokes the active refresh token and deletes cookie."""
    phone = "+919333333333"
    client.post("/api/auth/request-otp", json={"phone": phone})

    db = SessionLocal()
    otp_record = db.query(OTPCode).filter(OTPCode.phone == phone).first()
    otp_record.code_hash = hash_secret("998877")
    db.commit()
    db.close()

    login_res = client.post("/api/auth/verify-otp", json={"phone": phone, "otp": "998877"})
    cookie = login_res.cookies.get("krishi_refresh_token")

    logout_res = client.post("/api/auth/logout", cookies={"krishi_refresh_token": cookie})
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "success"

    # Token in DB should be revoked
    db = SessionLocal()
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_secret(cookie)).first()
    assert record.revoked_at is not None
    db.close()


def test_production_mode_fails_if_jwt_secret_missing():
    """Verify system fails startup if JWT_SECRET is missing in production mode."""
    with patch.dict(os.environ, {"APP_ENV": "production", "JWT_SECRET": ""}):
        with pytest.raises(RuntimeError) as exc_info:
            assert_production_config()
        assert "JWT_SECRET environment variable is missing" in str(exc_info.value)
