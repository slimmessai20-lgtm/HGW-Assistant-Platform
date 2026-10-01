"""
pytest configuration — sets env vars and global mocks before any test module is
imported. This allows the full test suite to run without:
  - A physical HGW (no Telnet connection)
  - A MySQL database
  - A Groq API key
  - Google Cloud credentials
  - The MCP server (no uv subprocess)
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# ── Environment variables needed before src.config is imported ─────────────────
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-characters-for-jwt")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key-not-used-in-unit-tests")
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/test_db")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_USER", "root")
os.environ.setdefault("DATABASE_PASSWORD", "")
os.environ.setdefault("DATABASE_NAME", "test_db")
# Point MCP to a dummy path — never actually called in unit tests
os.environ.setdefault("MCP_SERVER_PATH", r"C:\fake\mcp\mcpserver\main.py")
os.environ.setdefault("MCP_DIR", r"C:\fake\mcp")


# ── Patch DB-touching module-level code before any src.* import ────────────────
# chat_logs/service.py calls _ensure_corrections_table() and
# _ensure_feedback_column() at module load time.  Patch them globally.
_patchers = [
    patch("src.chat_logs.service._ensure_corrections_table"),
    patch("src.chat_logs.service._ensure_feedback_column"),
    patch("src.auth.db.get_connection", return_value=MagicMock()),
    patch("src.auth.service.get_connection", return_value=MagicMock()),
]


def pytest_configure(config):
    """Start global patches as early as possible."""
    for p in _patchers:
        p.start()


def pytest_unconfigure(config):
    """Stop global patches after the test session."""
    for p in _patchers:
        try:
            p.stop()
        except RuntimeError:
            pass  # already stopped


# ── Shared fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    """Return the FastAPI app instance (singleton for the test session)."""
    from src.main import app as _app
    return _app


@pytest.fixture(scope="session")
def client(app):
    """TestClient wrapping the FastAPI app — shared across all tests."""
    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def admin_headers():
    """JWT Authorization header for an admin user."""
    from src.auth.service import create_token
    token = create_token({
        "id": 1, "username": "admin", "full_name": "Test Admin",
        "email": "admin@test.com", "role": "admin",
        "is_active": 1, "password_hash": "x",
    }, session_id=1)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def engineer_headers():
    """JWT Authorization header for an engineer user."""
    from src.auth.service import create_token
    token = create_token({
        "id": 2, "username": "eng", "full_name": "Engineer",
        "email": "eng@test.com", "role": "engineer",
        "is_active": 1, "password_hash": "x",
    }, session_id=2)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def general_headers():
    """JWT Authorization header for a general user."""
    from src.auth.service import create_token
    token = create_token({
        "id": 3, "username": "user1", "full_name": "User One",
        "email": "user@test.com", "role": "general",
        "is_active": 1, "password_hash": "x",
    }, session_id=3)
    return {"Authorization": f"Bearer {token}"}
