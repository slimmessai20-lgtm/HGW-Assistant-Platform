"""
Unit tests for the chat pipeline logic.
Covers: tool selection, context enrichment, response cleaning.
No real DB, Groq API, or MCP server required — all I/O is mocked.
Run: pytest tests/test_chat.py -v
"""
import pytest
from unittest.mock import MagicMock, patch


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_tool(name: str) -> MagicMock:
    t = MagicMock()
    t.name = name
    t.description = f"Tool {name}"
    return t


# ── select_tools_for_message ──────────────────────────────────────────────────

class TestSelectToolsForMessage:

    @pytest.fixture(autouse=True)
    def _patch_db(self):
        with patch("src.auth.db.get_connection"), \
             patch("src.auth.service.get_connection"), \
             patch("src.chat_logs.service._ensure_corrections_table"), \
             patch("src.chat_logs.service._ensure_feedback_column"):
            yield

    def _get_fn(self):
        from src.chat.router import select_tools_for_message
        return select_tools_for_message

    def test_wifi_keyword_selects_wifi_tools(self):
        fn = self._get_fn()
        tools = [
            _make_tool("wifi_status_normal"),
            _make_tool("dhcp_status_normal"),
            _make_tool("wan_status_normal"),
        ]
        selected, matched = fn(tools, "what is the wifi status?", "general")
        assert matched is True
        names = [t.name for t in selected]
        assert "wifi_status_normal" in names
        assert "dhcp_status_normal" not in names

    def test_general_role_excludes_technical_tools(self):
        fn = self._get_fn()
        tools = [
            _make_tool("wifi_status_normal"),
            _make_tool("wifi_status_technical"),
        ]
        selected, _ = fn(tools, "wifi status", "general")
        names = [t.name for t in selected]
        assert "wifi_status_normal" in names
        assert "wifi_status_technical" not in names

    def test_engineer_role_excludes_normal_tools(self):
        fn = self._get_fn()
        tools = [
            _make_tool("wifi_status_normal"),
            _make_tool("wifi_status_technical"),
        ]
        selected, _ = fn(tools, "wifi status", "engineer")
        names = [t.name for t in selected]
        assert "wifi_status_technical" in names
        assert "wifi_status_normal" not in names

    def test_admin_role_excludes_normal_tools(self):
        fn = self._get_fn()
        tools = [
            _make_tool("firewall_status_normal"),
            _make_tool("firewall_status_technical"),
        ]
        selected, _ = fn(tools, "firewall status", "admin")
        names = [t.name for t in selected]
        assert "firewall_status_technical" in names
        assert "firewall_status_normal" not in names

    def test_read_only_message_excludes_action_tools(self):
        fn = self._get_fn()
        tools = [
            _make_tool("wifi_status_normal"),
            _make_tool("wifi_on"),
            _make_tool("wifi_off"),
        ]
        selected, _ = fn(tools, "what is the wifi status?", "general")
        names = [t.name for t in selected]
        # wifi_status_normal is a read tool — included
        assert "wifi_status_normal" in names
        # wifi_on / wifi_off are action tools — excluded on read-only query
        assert "wifi_on" not in names
        assert "wifi_off" not in names

    def test_write_message_includes_action_tools(self):
        fn = self._get_fn()
        tools = [
            _make_tool("wifi_status_normal"),
            _make_tool("wifi_on"),
        ]
        selected, _ = fn(tools, "turn on the wifi", "general")
        names = [t.name for t in selected]
        assert "wifi_on" in names

    def test_no_keyword_match_returns_unmatched_false(self):
        fn = self._get_fn()
        tools = [_make_tool("wifi_status_normal")]
        _, matched = fn(tools, "hello how are you", "general")
        assert matched is False

    def test_max_six_tools_returned(self):
        fn = self._get_fn()
        tools = [_make_tool(f"wifi_tool_{i}") for i in range(20)]
        selected, _ = fn(tools, "wifi check", "general")
        assert len(selected) <= 6

    def test_password_keyword_selects_password_tool(self):
        fn = self._get_fn()
        tools = [
            _make_tool("wifi_get_password"),
            _make_tool("dhcp_status_normal"),
        ]
        selected, matched = fn(tools, "what is my wifi password?", "general")
        names = [t.name for t in selected]
        assert matched is True
        assert "wifi_get_password" in names

    def test_device_keyword_selects_device_tools(self):
        fn = self._get_fn()
        tools = [
            _make_tool("devices_list_normal"),
            _make_tool("devices_list_technical"),
            _make_tool("wifi_status_normal"),
        ]
        selected, matched = fn(tools, "show connected devices", "general")
        names = [t.name for t in selected]
        assert matched is True
        assert "devices_list_normal" in names


# ── _enrich_context_message ───────────────────────────────────────────────────

class TestEnrichContextMessage:

    @pytest.fixture(autouse=True)
    def _patch_db(self):
        with patch("src.auth.db.get_connection"), \
             patch("src.auth.service.get_connection"), \
             patch("src.chat_logs.service._ensure_corrections_table"), \
             patch("src.chat_logs.service._ensure_feedback_column"):
            yield

    def _get_fn(self):
        from src.chat.router import _enrich_context_message
        return _enrich_context_message

    def _history_with_last(self, last_response: str):
        return [{"role": "assistant", "content": last_response}]

    def test_no_history_returns_original_message(self):
        fn = self._get_fn()
        msg, is_ctx = fn("go deeper", [])
        assert msg == "go deeper"
        assert is_ctx is False

    def test_go_deeper_detected(self):
        fn = self._get_fn()
        history = self._history_with_last("WiFi is on. SSID: TestNet.")
        _, is_ctx = fn("go deeper", history)
        assert is_ctx is True

    def test_more_detail_detected(self):
        fn = self._get_fn()
        history = self._history_with_last("DHCP is enabled.")
        _, is_ctx = fn("more details please", history)
        assert is_ctx is True

    def test_simpler_detected(self):
        fn = self._get_fn()
        history = self._history_with_last("WPA2-Personal on channel 100.")
        _, is_ctx = fn("explain simply", history)
        assert is_ctx is True

    def test_explain_again_detected(self):
        fn = self._get_fn()
        history = self._history_with_last("The firewall is active.")
        _, is_ctx = fn("explain again", history)
        assert is_ctx is True

    def test_summarize_detected(self):
        fn = self._get_fn()
        history = self._history_with_last("A long technical response.")
        _, is_ctx = fn("summarize", history)
        assert is_ctx is True

    def test_tldr_detected(self):
        fn = self._get_fn()
        history = self._history_with_last("Detailed answer here.")
        _, is_ctx = fn("tldr", history)
        assert is_ctx is True

    def test_normal_question_not_detected(self):
        fn = self._get_fn()
        history = self._history_with_last("WiFi is on.")
        _, is_ctx = fn("what is the DHCP status?", history)
        assert is_ctx is False

    def test_deeper_enriched_message_contains_no_tool_instruction(self):
        fn = self._get_fn()
        history = self._history_with_last("WiFi is on, channel 100.")
        enriched, _ = fn("go deeper", history)
        assert "DO NOT call any tools" in enriched

    def test_simpler_enriched_message_requests_plain_english(self):
        fn = self._get_fn()
        history = self._history_with_last("WPA2-Personal encryption active.")
        enriched, _ = fn("explain simply", history)
        assert "plain English" in enriched or "Plain English" in enriched or "plain english" in enriched.lower()

    def test_previous_answer_included_in_enriched_message(self):
        fn = self._get_fn()
        last = "The SSID is Livebox-ABCD."
        history = self._history_with_last(last)
        enriched, _ = fn("go deeper", history)
        assert "Livebox-ABCD" in enriched


# ── _clean_response ───────────────────────────────────────────────────────────

class TestCleanResponse:

    @pytest.fixture(autouse=True)
    def _patch_db(self):
        with patch("src.auth.db.get_connection"), \
             patch("src.auth.service.get_connection"), \
             patch("src.chat_logs.service._ensure_corrections_table"), \
             patch("src.chat_logs.service._ensure_feedback_column"):
            yield

    def _get_fn(self):
        from src.chat.router import _clean_response
        return _clean_response

    def test_plain_text_unchanged(self):
        fn = self._get_fn()
        assert fn("WiFi is enabled.") == "WiFi is enabled."

    def test_strips_xml_tags(self):
        fn = self._get_fn()
        result = fn("<answer>WiFi is enabled.</answer>")
        assert "<answer>" not in result
        assert "WiFi is enabled." in result

    def test_strips_lone_tool_name_lines(self):
        fn = self._get_fn()
        result = fn("wifi_status_normal\nWiFi is on.")
        assert "wifi_status_normal" not in result
        assert "WiFi is on." in result

    def test_strips_tool_json_echo(self):
        fn = self._get_fn()
        result = fn('wifi_status_normal>{"Enable": true, "SSID": "Net"}')
        # Should not contain raw JSON or tool name
        assert "wifi_status_normal>" not in result

    def test_returns_string(self):
        fn = self._get_fn()
        assert isinstance(fn("hello"), str)

    def test_empty_input_returns_empty_string(self):
        fn = self._get_fn()
        assert fn("") == ""

    def test_multiple_newlines_collapsed(self):
        fn = self._get_fn()
        result = fn("line1\n\n\n\nline2")
        assert "\n\n\n" not in result


# ── mcp_to_openai_tools ───────────────────────────────────────────────────────

class TestMcpToOpenaiTools:

    @pytest.fixture(autouse=True)
    def _patch_db(self):
        with patch("src.auth.db.get_connection"), \
             patch("src.auth.service.get_connection"), \
             patch("src.chat_logs.service._ensure_corrections_table"), \
             patch("src.chat_logs.service._ensure_feedback_column"):
            yield

    def test_converts_to_openai_format(self):
        from src.chat.router import mcp_to_openai_tools
        tool = _make_tool("wifi_status_normal")
        tool.description = "Returns WiFi status"
        result = mcp_to_openai_tools([tool])
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "wifi_status_normal"

    def test_description_truncated_to_80_chars(self):
        from src.chat.router import mcp_to_openai_tools
        tool = _make_tool("wifi_status_normal")
        tool.description = "A" * 200
        result = mcp_to_openai_tools([tool])
        assert len(result[0]["function"]["description"]) <= 80

    def test_empty_tool_list_returns_empty(self):
        from src.chat.router import mcp_to_openai_tools
        assert mcp_to_openai_tools([]) == []
