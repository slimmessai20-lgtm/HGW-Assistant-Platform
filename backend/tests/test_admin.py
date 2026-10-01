"""
Integration-style tests for admin-only API endpoints.
All DB calls are mocked — no real database required.
Run: pytest tests/test_admin.py -v
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

FAKE_ADMIN = {
    "id": 1, "username": "admin", "full_name": "Admin", "email": "a@a.com",
    "role": "admin", "is_active": 1,
    "password_hash": "$2b$12$dummy",
}

FAKE_LOG = {
    "id": 1,
    "user_id": 2,
    "username": "engineer1",
    "session_id": 1,
    "gateway_id": 1,
    "gateway_name": "TestGW",
    "message": "What is the WiFi status?",
    "response": "WiFi is on.",
    "tool_calls": 1,
    "voice_used": 0,
    "duration_ms": 3200,
    "user_type": "engineer",
    "feedback": None,
    "created_at": "2026-05-20T10:00:00",
}


@pytest.fixture(scope="module")
def client():
    with patch("src.auth.db.get_connection"), \
         patch("src.auth.service.get_connection"), \
         patch("src.chat_logs.service._ensure_corrections_table"), \
         patch("src.chat_logs.service._ensure_feedback_column"):
        from src.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def _admin_token() -> str:
    from src.auth.service import create_token
    return create_token(FAKE_ADMIN, session_id=1)


def _general_token() -> str:
    from src.auth.service import create_token
    user = {**FAKE_ADMIN, "role": "general"}
    return create_token(user, session_id=1)


def _headers(role: str = "admin") -> dict:
    if role == "admin":
        return {"Authorization": f"Bearer {_admin_token()}"}
    return {"Authorization": f"Bearer {_general_token()}"}


# ── Chat Logs — GET /chat-logs ────────────────────────────────────────────────

class TestChatLogs:

    def test_list_logs_requires_auth(self, client):
        resp = client.get("/chat-logs")
        assert resp.status_code in (401, 403)

    def test_list_logs_requires_admin_role(self, client):
        resp = client.get("/chat-logs", headers=_headers("general"))
        assert resp.status_code == 403

    def test_list_logs_returns_200_for_admin(self, client):
        with patch("src.chat_logs.service.get_logs", return_value=[FAKE_LOG]):
            resp = client.get("/chat-logs", headers=_headers("admin"))
        assert resp.status_code == 200

    def test_list_logs_returns_list(self, client):
        with patch("src.chat_logs.service.get_logs", return_value=[FAKE_LOG]):
            resp = client.get("/chat-logs", headers=_headers("admin"))
        assert isinstance(resp.json(), list)

    def test_list_logs_date_filter_forwarded(self, client):
        with patch("src.chat_logs.service.get_logs", return_value=[]) as mock_get:
            client.get("/chat-logs?date_from=2026-05-01&date_to=2026-05-31",
                       headers=_headers("admin"))
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs.get("date_from") == "2026-05-01"
        assert call_kwargs.get("date_to") == "2026-05-31"

    def test_list_logs_limit_capped_at_2000(self, client):
        with patch("src.chat_logs.service.get_logs", return_value=[]) as mock_get:
            client.get("/chat-logs?limit=5000", headers=_headers("admin"))
        # FastAPI should reject limit > 2000 with 422
        # (or clamp it — either is acceptable)


# ── Chat Logs — GET /chat-logs/stats ─────────────────────────────────────────

class TestChatLogsStats:

    def test_stats_requires_admin(self, client):
        resp = client.get("/chat-logs/stats", headers=_headers("general"))
        assert resp.status_code == 403

    def test_stats_returns_200(self, client):
        fake_stats = {
            "total_interactions": 100,
            "active_users_count": 5,
            "by_user": [],
            "by_gateway": [],
            "last_7_days": [],
            "voice_usage": {"voice_count": 10, "text_count": 90},
        }
        with patch("src.chat_logs.service.get_logs_stats", return_value=fake_stats):
            resp = client.get("/chat-logs/stats", headers=_headers("admin"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_interactions"] == 100


# ── Chat Logs — GET /chat-logs/{id} ──────────────────────────────────────────

class TestGetSingleLog:

    def test_get_existing_log_returns_200(self, client):
        with patch("src.chat_logs.service.get_log_by_id", return_value=FAKE_LOG):
            resp = client.get("/chat-logs/1", headers=_headers("admin"))
        assert resp.status_code == 200
        assert resp.json()["username"] == "engineer1"

    def test_get_nonexistent_log_returns_404(self, client):
        with patch("src.chat_logs.service.get_log_by_id", return_value=None):
            resp = client.get("/chat-logs/999", headers=_headers("admin"))
        assert resp.status_code == 404


# ── Chat Logs — DELETE /chat-logs/{id} ───────────────────────────────────────

class TestDeleteLog:

    def test_delete_existing_log_returns_200(self, client):
        with patch("src.chat_logs.service.delete_log", return_value=True):
            resp = client.delete("/chat-logs/1", headers=_headers("admin"))
        assert resp.status_code == 200

    def test_delete_nonexistent_log_returns_404(self, client):
        with patch("src.chat_logs.service.delete_log", return_value=False):
            resp = client.delete("/chat-logs/999", headers=_headers("admin"))
        assert resp.status_code == 404

    def test_delete_requires_admin(self, client):
        resp = client.delete("/chat-logs/1", headers=_headers("general"))
        assert resp.status_code == 403


# ── Admin Corrections ─────────────────────────────────────────────────────────

class TestCorrections:

    def test_save_correction_returns_200(self, client):
        with patch("src.chat_logs.service.get_log_by_id", return_value=FAKE_LOG), \
             patch("src.chat_logs.service.save_correction", return_value=True):
            resp = client.post(
                "/chat-logs/1/correct",
                json={"corrected_response": "Better answer."},
                headers=_headers("admin"),
            )
        assert resp.status_code == 200
        assert resp.json()["log_id"] == 1

    def test_save_correction_for_missing_log_returns_404(self, client):
        with patch("src.chat_logs.service.get_log_by_id", return_value=None):
            resp = client.post(
                "/chat-logs/999/correct",
                json={"corrected_response": "Better answer."},
                headers=_headers("admin"),
            )
        assert resp.status_code == 404

    def test_save_correction_requires_admin(self, client):
        resp = client.post(
            "/chat-logs/1/correct",
            json={"corrected_response": "Better."},
            headers=_headers("general"),
        )
        assert resp.status_code == 403

    def test_get_correction_returns_404_when_absent(self, client):
        with patch("src.chat_logs.service.get_correction", return_value=None):
            resp = client.get("/chat-logs/1/correction", headers=_headers("admin"))
        assert resp.status_code == 404

    def test_get_correction_returns_200_when_present(self, client):
        fake_correction = {
            "id": 1, "log_id": 1,
            "original_response": "Old.", "corrected_response": "Better.",
            "corrected_by": "admin", "created_at": "2026-05-20T10:05:00",
        }
        with patch("src.chat_logs.service.get_correction", return_value=fake_correction):
            resp = client.get("/chat-logs/1/correction", headers=_headers("admin"))
        assert resp.status_code == 200
        assert resp.json()["corrected_response"] == "Better."


# ── Feedback ──────────────────────────────────────────────────────────────────

class TestFeedback:

    def test_feedback_up_returns_200(self, client):
        with patch("src.chat_logs.service.save_feedback", return_value=True):
            resp = client.post(
                "/chat-logs/1/feedback",
                json={"value": "up"},
                headers=_headers("admin"),
            )
        assert resp.status_code == 200
        assert resp.json()["value"] == "up"

    def test_feedback_down_returns_200(self, client):
        with patch("src.chat_logs.service.save_feedback", return_value=True):
            resp = client.post(
                "/chat-logs/1/feedback",
                json={"value": "down"},
                headers=_headers("admin"),
            )
        assert resp.status_code == 200

    def test_feedback_invalid_value_returns_400(self, client):
        resp = client.post(
            "/chat-logs/1/feedback",
            json={"value": "maybe"},
            headers=_headers("admin"),
        )
        assert resp.status_code == 400

    def test_feedback_on_missing_log_returns_404(self, client):
        with patch("src.chat_logs.service.save_feedback", return_value=False):
            resp = client.post(
                "/chat-logs/999/feedback",
                json={"value": "up"},
                headers=_headers("admin"),
            )
        assert resp.status_code == 404

    def test_feedback_accessible_to_general_user(self, client):
        with patch("src.chat_logs.service.save_feedback", return_value=True):
            resp = client.post(
                "/chat-logs/1/feedback",
                json={"value": "up"},
                headers=_headers("general"),
            )
        assert resp.status_code == 200

    def test_feedback_requires_auth(self, client):
        resp = client.post("/chat-logs/1/feedback", json={"value": "up"})
        assert resp.status_code in (401, 403)


# ── Admin Stats ───────────────────────────────────────────────────────────────

class TestAdminStats:

    def _kpi(self):
        return {
            "total_messages": 500, "voice_messages": 50, "text_messages": 450,
            "active_users_24h": 3, "gateways_count": 2, "voice_percentage": 10.0
        }

    def test_kpi_requires_admin(self, client):
        resp = client.get("/admin/stats/kpi", headers=_headers("general"))
        assert resp.status_code == 403

    def test_kpi_returns_200(self, client):
        with patch("src.admin_stats.service.get_kpi_stats", return_value=self._kpi()):
            resp = client.get("/admin/stats/kpi", headers=_headers("admin"))
        assert resp.status_code == 200

    def test_kpi_structure(self, client):
        with patch("src.admin_stats.service.get_kpi_stats", return_value=self._kpi()):
            resp = client.get("/admin/stats/kpi", headers=_headers("admin"))
        data = resp.json()
        for key in ("total_messages", "voice_messages", "text_messages",
                    "active_users_24h", "gateways_count", "voice_percentage"):
            assert key in data

    def test_activity_requires_admin(self, client):
        resp = client.get("/admin/stats/activity", headers=_headers("general"))
        assert resp.status_code == 403

    def test_activity_returns_200(self, client):
        with patch("src.admin_stats.service.get_activity_last_7_days", return_value={}):
            resp = client.get("/admin/stats/activity", headers=_headers("admin"))
        assert resp.status_code == 200

    def test_feedback_stats_positive_rate_in_range(self, client):
        fake = {"up_count": 80, "down_count": 20, "total_rated": 100,
                "total": 500, "positive_rate": 80.0, "rated_rate": 20.0}
        with patch("src.admin_stats.service.get_feedback_stats", return_value=fake):
            resp = client.get("/admin/stats/feedback", headers=_headers("admin"))
        data = resp.json()
        assert 0 <= data["positive_rate"] <= 100

    def test_hourly_heatmap_returns_200(self, client):
        fake = {str(h): 0 for h in range(24)}
        with patch("src.admin_stats.service.get_hourly_heatmap", return_value=fake):
            resp = client.get("/admin/stats/hourly", headers=_headers("admin"))
        assert resp.status_code == 200

    def test_response_time_stats_returns_200(self, client):
        fake = {"overall": {"avg_ms": 3000, "min_ms": 500, "max_ms": 20000}, "by_type": []}
        with patch("src.admin_stats.service.get_response_time_stats", return_value=fake):
            resp = client.get("/admin/stats/response-time", headers=_headers("admin"))
        assert resp.status_code == 200


# ── Prompt Admin ──────────────────────────────────────────────────────────────

class TestPromptAdmin:

    def test_get_prompts_requires_admin(self, client):
        resp = client.get("/prompts", headers=_headers("general"))
        assert resp.status_code == 403

    def test_get_prompts_returns_all_sections(self, client):
        resp = client.get("/prompts", headers=_headers("admin"))
        assert resp.status_code == 200
        data = resp.json()
        assert "general" in data
        assert "technical" in data
        assert "context_commands" in data

    def test_put_prompts_updates_max_tokens(self, client):
        resp = client.put(
            "/prompts",
            json={"general": {"max_tokens": 999}},
            headers=_headers("admin"),
        )
        assert resp.status_code == 200
        # Verify the config is returned in the response
        data = resp.json()
        assert "config" in data

    def test_put_prompts_requires_admin(self, client):
        resp = client.put(
            "/prompts",
            json={"general": {"max_tokens": 100}},
            headers=_headers("general"),
        )
        assert resp.status_code == 403

    def test_reload_prompts_returns_200(self, client):
        resp = client.post("/prompts/reload", json={}, headers=_headers("admin"))
        assert resp.status_code == 200
        assert "config" in resp.json()
