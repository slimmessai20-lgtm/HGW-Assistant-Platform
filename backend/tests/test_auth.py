"""
Tests for authentication — service logic + API endpoints.
Run: pytest tests/test_auth.py -v
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── Helpers / fixtures ────────────────────────────────────────────────────────

FAKE_USER = {
    "id": 1,
    "username": "testadmin",
    "full_name": "Test Admin",
    "email": "admin@test.com",
    "role": "admin",
    "is_active": 1,
    "password_hash": "$2b$12$KIXzR5Q3V5Z9Qk4mF3e2ROy9l5A0BzCdEfGhIjKlMnOpQrStUvWx",
}


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient — DB is mocked so no real connection needed."""
    with patch("src.auth.db.get_connection"), \
         patch("src.auth.service.get_connection"):
        from src.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def _make_token(role: str = "admin") -> str:
    """Create a real JWT for use in protected-endpoint tests."""
    from src.auth.service import create_token
    user = {**FAKE_USER, "role": role}
    return create_token(user, session_id=None)


# ── verify_password ───────────────────────────────────────────────────────────

class TestVerifyPassword:

    def test_correct_password_returns_true(self):
        import bcrypt
        from src.auth.service import verify_password
        hashed = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
        assert verify_password("secret123", hashed) is True

    def test_wrong_password_returns_false(self):
        import bcrypt
        from src.auth.service import verify_password
        hashed = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
        assert verify_password("wrongpass", hashed) is False

    def test_empty_password_returns_false(self):
        import bcrypt
        from src.auth.service import verify_password
        hashed = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode()
        assert verify_password("", hashed) is False


# ── create_token / decode_token ───────────────────────────────────────────────

class TestJWT:

    def test_token_is_string(self):
        from src.auth.service import create_token
        token = create_token(FAKE_USER)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decoded_token_contains_username(self):
        from src.auth.service import create_token, decode_token
        token = create_token(FAKE_USER)
        payload = decode_token(token)
        assert payload["username"] == "testadmin"

    def test_decoded_token_contains_role(self):
        from src.auth.service import create_token, decode_token
        token = create_token(FAKE_USER)
        payload = decode_token(token)
        assert payload["role"] == "admin"

    def test_decoded_token_contains_sub(self):
        from src.auth.service import create_token, decode_token
        token = create_token(FAKE_USER)
        payload = decode_token(token)
        assert payload["sub"] == "1"

    def test_invalid_token_raises(self):
        from src.auth.service import decode_token
        import jwt
        with pytest.raises(jwt.InvalidTokenError):
            decode_token("this.is.not.a.valid.token")


# ── Login endpoint ────────────────────────────────────────────────────────────

class TestLoginEndpoint:

    def test_login_success_returns_200(self, client):
        with patch("src.auth.router.authenticate_user", return_value=FAKE_USER), \
             patch("src.auth.router.create_session", return_value=1), \
             patch("src.auth.router.update_session_token_hash"):
            resp = client.post("/auth/login", json={
                "username": "testadmin",
                "password": "secret123"
            })
        assert resp.status_code == 200

    def test_login_success_returns_token(self, client):
        with patch("src.auth.router.authenticate_user", return_value=FAKE_USER), \
             patch("src.auth.router.create_session", return_value=1), \
             patch("src.auth.router.update_session_token_hash"):
            resp = client.post("/auth/login", json={
                "username": "testadmin",
                "password": "secret123"
            })
        data = resp.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)

    def test_login_success_returns_user_info(self, client):
        with patch("src.auth.router.authenticate_user", return_value=FAKE_USER), \
             patch("src.auth.router.create_session", return_value=1), \
             patch("src.auth.router.update_session_token_hash"):
            resp = client.post("/auth/login", json={
                "username": "testadmin",
                "password": "secret123"
            })
        user = resp.json()["user"]
        assert user["username"] == "testadmin"
        assert user["role"] == "admin"

    def test_login_invalid_credentials_returns_401(self, client):
        with patch("src.auth.router.authenticate_user", return_value=None):
            resp = client.post("/auth/login", json={
                "username": "wrong",
                "password": "wrong"
            })
        assert resp.status_code == 401

    def test_login_missing_fields_returns_422(self, client):
        resp = client.post("/auth/login", json={"username": "admin"})
        assert resp.status_code == 422


# ── Protected endpoints ───────────────────────────────────────────────────────

class TestProtectedEndpoints:

    def test_get_prompts_without_token_returns_403(self, client):
        resp = client.get("/prompts")
        assert resp.status_code in (401, 403)

    def test_get_prompts_with_admin_token_returns_200(self, client):
        token = _make_token("admin")
        resp = client.get("/prompts", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_get_prompts_with_general_token_returns_403(self, client):
        token = _make_token("general")
        resp = client.get("/prompts", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_get_prompts_response_has_sections(self, client):
        token = _make_token("admin")
        resp = client.get("/prompts", headers={"Authorization": f"Bearer {token}"})
        data = resp.json()
        assert "general" in data
        assert "technical" in data
        assert "context_commands" in data
