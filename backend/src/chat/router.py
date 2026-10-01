from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from src.auth.router import get_current_user
import asyncio
import json
import threading
import traceback
import logging
import anyio
import os
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.auth.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

from src.config import GROQ_API_KEY, GROQ_MODEL, GROQ_BASE, MCP_SCRIPT, MCP_DIR
from src.prompts import get_system_prompt, get_max_tokens


def _make_mcp_server(telnet_config: dict) -> StdioServerParameters:
    """Create MCP server params with the gateway's telnet config as env vars."""
    env = {**os.environ,
           "HGW_HOST":     telnet_config.get("host", "192.168.2.254"),
           "HGW_PORT":     str(telnet_config.get("port", 23)),
           "HGW_USER":     telnet_config.get("user", "root"),
           "HGW_PASSWORD": telnet_config.get("password", "sah")}
    return StdioServerParameters(
        command="uv",
        args=["--directory", MCP_DIR, "run", "--with", "mcp", "mcp", "run", MCP_SCRIPT],
        env=env
    )


from src.gateways.crypto import decrypt_password

def _get_gateway_telnet(gateway_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT telnet_host, telnet_port, telnet_user, telnet_password, name, 
                          software_version, ipv4_address, ipv6_address, mac_address, 
                          serial_number, base_mac 
                   FROM gateways WHERE id=%s""",
                (gateway_id,)
            )
            row = cur.fetchone()
            if not row:
                return {}
            return {
                "host":     row["telnet_host"] or "192.168.2.254",
                "port":     row["telnet_port"] or 23,
                "user":     row["telnet_user"] or "root",
                "password": decrypt_password(row["telnet_password"]) or "sah",
                "name":     row["name"],
                "software_version": row.get("software_version"),
                "ipv4_address":     row.get("ipv4_address"),
                "ipv6_address":     row.get("ipv6_address"),
                "mac_address":      row.get("mac_address"),
                "serial_number":    row.get("serial_number"),
                "base_mac":         row.get("base_mac"),
            }
    finally:
        conn.close()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    gateway_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    tool_calls_count: int


# ── Context-command detection ─────────────────────────────────────────────────
# When the user says "go deeper", "explain again", etc. we augment the message
# so the LLM understands exactly what is being requested from the conversation.

_CTX_DEEPER  = ["go deeper", "more detail", "more details", "elaborate", "explain more",
                "tell me more", "dig deeper", "expand on that", "more info"]
_CTX_SIMPLER = ["simpler", "explain simply", "in simple terms", "dumb it down",
                "make it simple", "for a beginner"]
_CTX_REPEAT  = ["explain again", "say that again", "repeat", "rephrase",
                "what do you mean", "i don't understand", "clarify"]
_CTX_SUMMARY = ["summarize", "summary", "tldr", "short version", "in brief", "briefly"]


def _enrich_context_message(message: str, history: list) -> tuple[str, bool]:
    """
    Detect context meta-commands and enrich the user message.
    Returns (enriched_message, is_context_command).
    When is_context_command is True the caller must disable tool calls so the
    LLM analyses the existing conversation data instead of re-fetching it.
    """
    msg = message.lower().strip()
    last_assistant = next(
        (h["content"] for h in reversed(history) if h.get("role") == "assistant"),
        None,
    )
    if not last_assistant:
        return message, False

    # Use the full last answer so the LLM has all the data to work with
    data = last_assistant[:800]

    if any(kw in msg for kw in _CTX_DEEPER):
        enriched = (
            "DO NOT call any tools. Work only from the data already retrieved below.\n\n"
            f"Data from previous answer:\n{data}\n\n"
            "Now provide a deeper technical analysis: explain what each value means, "
            "highlight anything unusual or worth noting, and give technical context "
            "(e.g. what channel 100 means for 5 GHz, what WPA2-WPA3-Personal implies, etc.)."
        )
        return enriched, True

    if any(kw in msg for kw in _CTX_SIMPLER):
        enriched = (
            "DO NOT call any tools. Work only from the data already retrieved below.\n\n"
            f"Data from previous answer:\n{data}\n\n"
            "Re-explain this in plain English for a non-technical home user. "
            "No bullet points, no technical jargon. 2-4 friendly sentences maximum."
        )
        return enriched, True

    if any(kw in msg for kw in _CTX_REPEAT):
        enriched = (
            "DO NOT call any tools. Work only from the data already retrieved below.\n\n"
            f"Data from previous answer:\n{data}\n\n"
            "Rephrase this in different words, keeping the same level of detail."
        )
        return enriched, True

    if any(kw in msg for kw in _CTX_SUMMARY):
        enriched = (
            "DO NOT call any tools. Work only from the data already retrieved below.\n\n"
            f"Data from previous answer:\n{data}\n\n"
            "Summarize the key points in 1-2 sentences."
        )
        return enriched, True

    # ── Pronoun/reference resolution ─────────────────────────────────────────
    # Detect short follow-up actions like "change it to X" and resolve "it"
    # to the topic mentioned in the last assistant message.
    _action_words = ("change", "set", "modify", "update", "rename", "reset")
    _pronouns     = (" it ", " it\n", " it to ", "change it", "set it", "modify it")
    has_action  = any(w in msg for w in _action_words)
    has_pronoun = any(p in (" " + msg + " ") for p in _pronouns)

    if has_action and has_pronoun and last_assistant:
        ctx = last_assistant.lower()
        if any(kw in ctx for kw in ("password", "passphrase", "mot de passe", "clé", "keypas")):
            resolved = message.replace("it", "the wifi password").replace("It", "The wifi password")
            return resolved, False
        if any(kw in ctx for kw in ("ssid", "network name", "nom du réseau", "nom wifi")):
            resolved = message.replace("it", "the wifi network name (SSID)").replace("It", "The wifi network name (SSID)")
            return resolved, False
        if any(kw in ctx for kw in ("firewall", "pare-feu", "level")):
            resolved = message.replace("it", "the firewall level").replace("It", "The firewall level")
            return resolved, False

    return message, False


KEYWORD_GROUPS = {
    "wifi":      ["wifi", "wi-fi", "ssid", "réseau wifi", "wireless", "wlan", "radio", "channel",
                  "speedtest", "speed test", "speed", "débit", "bande passante", "bandwidth"],
    "password":  ["password", "mot de passe", "passphrase", "clé wifi", "wifi key", "wpa key"],
    "guest":     ["guest", "invit"],
    "devices":   ["device", "appare", "connect", "client", "mac"],
    "wan":       ["wan", "internet", "connexion", "adsl", "fibre"],
    "firewall":  ["firewall", "pare-feu", "blocage", "block"],
    "dhcp":      ["dhcp", "ip", "adresse"],
    "voip":      ["voip", "telephone", "appel"],
    "iptv":      ["iptv", "tv", "television"],
    "scheduler": ["scheduler", "planif", "horaire"],
    "debug":     ["debug", "ping", "telnet", "diagnostic"],
}

_READ_INTENT  = ("what", "show", "status", "list", "get", "display", "check", "tell", "run", "launch", "start")
_WRITE_INTENT = ("enable", "disable", "turn on", "turn off", "set", "change", "activate",
                 "deactivate", "reset", "reboot", "factory")
_ACTION_SUFFIXES = ("_enable", "_disable", "_on", "_off", "_set", "_reset", "_reboot",
                    "_factory", "set_level", "set_ssid", "set_password")


def _is_read_only(msg: str) -> bool:
    """True when the message clearly asks for information, not a change."""
    m = msg.lower()
    has_read  = any(w in m for w in _READ_INTENT)
    has_write = any(w in m for w in _WRITE_INTENT)
    return has_read and not has_write


def _is_action_tool(name: str) -> bool:
    n = name.lower()
    return any(n.endswith(s) or s in n for s in _ACTION_SUFFIXES)


def select_tools_for_message(all_tools, message: str, user_role: str = "general", history: list = []):
    """Return (relevant_tools, keyword_matched) based on keywords and user role."""
    is_technical = user_role in ("engineer", "admin")
    read_only    = _is_read_only(message)
    # Include last 2 history messages for context-aware tool selection
    # (handles follow-ups like "change it" after "what is the password")
    context = message + " " + " ".join(h.get("content", "") for h in history[-2:])

    # Filter tools by role variant and read/write intent
    filtered_tools = []
    for t in all_tools:
        name = t.name.lower()
        has_normal    = name.endswith("_normal")
        has_technical = name.endswith("_technical")
        if has_normal and is_technical:
            continue
        if has_technical and not is_technical:
            continue
        # For read-only queries, exclude action/modification tools
        if read_only and _is_action_tool(name):
            continue
        filtered_tools.append(t)

    msg = context.lower()
    tool_scores: dict[str, int] = {}
    for group, keywords in KEYWORD_GROUPS.items():
        if any(kw in msg for kw in keywords):
            for t in filtered_tools:
                if group in t.name.lower():
                    tool_scores[t.name] = tool_scores.get(t.name, 0) + 1
    if not tool_scores:
        return [t for t in filtered_tools[:6]], False
    # Sort by score descending so tools matching more groups (more specific) come first
    name_to_tool = {t.name: t for t in filtered_tools}
    sorted_names = sorted(tool_scores, key=lambda n: -tool_scores[n])
    chosen = [name_to_tool[n] for n in sorted_names if n in name_to_tool][:6]
    return chosen, True


def mcp_to_openai_tools(mcp_tools):
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": (t.description or "Tool")[:300],
                "parameters": (t.inputSchema
                               if t.inputSchema
                               else {"type": "object", "properties": {}, "required": []})
            }
        }
        for t in mcp_tools
    ]


async def _run_chat(message, history, telnet_config: dict, user_role: str = "general"):
    from openai import BadRequestError, APIStatusError

    system_prompt = get_system_prompt(user_role)
    if telnet_config.get("name"):
        kpis = []
        if telnet_config.get('software_version'): kpis.append(f"Version: {telnet_config['software_version']}")
        if telnet_config.get('ipv4_address'): kpis.append(f"IP: {telnet_config['ipv4_address']}")
        if telnet_config.get('mac_address'): kpis.append(f"MAC: {telnet_config['mac_address']}")
        if telnet_config.get('serial_number'): kpis.append(f"Serial: {telnet_config['serial_number']}")
        kpis_str = f" Device Details: {', '.join(kpis)}." if kpis else ""
        system_prompt += f"\nYou manage HGW '{telnet_config['name']}' ({telnet_config.get('host', '?')}).{kpis_str}"

    mcp_server = _make_mcp_server(telnet_config)
    async with stdio_client(mcp_server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            all_mcp_tools = (await session.list_tools()).tools
            relevant, keyword_matched = select_tools_for_message(all_mcp_tools, message, user_role, history)
            tools = mcp_to_openai_tools(relevant)
            client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE, max_retries=0)

            enriched, is_ctx_cmd = _enrich_context_message(message, history)
            # Context commands work on already-fetched data — no tools needed
            if is_ctx_cmd:
                tools = []
                keyword_matched = False

            messages = [{"role": "system", "content": system_prompt}]
            for h in history[-2:]:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": enriched})

            tool_calls_count = 0
            retry_count = 0
            max_tokens = get_max_tokens(user_role, is_ctx_cmd)
            MAX_TOOL_CALLS = 4  # prevents infinite loops when HGW is slow
            called_tools: set[str] = set()  # deduplication: skip repeated tool calls

            while True:
                if tool_calls_count >= MAX_TOOL_CALLS:
                    return {"response": "⚠️ Too many tool calls — stopping to avoid timeout.", "tool_calls_count": tool_calls_count}
                try:
                    # Skip tools param entirely when empty (Groq rejects tools=[])
                    if tools:
                        response = await client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=messages,
                            tools=tools,
                            tool_choice="auto",
                            max_tokens=max_tokens,
                            timeout=60.0
                        )
                    else:
                        response = await client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=messages,
                            max_tokens=max_tokens,
                            timeout=60.0
                        )
                except BadRequestError as e:
                    if "tool_use_failed" in str(e):
                        # Model wrote <function=...> as text — retry without tools
                        response = await client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=messages,
                            max_tokens=max_tokens,
                            timeout=60.0
                        )
                    else:
                        raise
                except APIStatusError as e:
                    if e.status_code == 413:
                        return {"response": "⚠️ La requête est trop grande pour le modèle. Réessayez.", "tool_calls_count": tool_calls_count}
                    raise

                choice = response.choices[0]

                # If keyword matched but no tool called, force a retry with tool_choice="required"
                if (choice.finish_reason != "tool_calls"
                        and keyword_matched
                        and tool_calls_count == 0
                        and retry_count == 0):
                    retry_count += 1
                    try:
                        response = await client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=messages,
                            tools=tools,
                            tool_choice="required",
                            max_tokens=max_tokens,
                            timeout=60.0
                        )
                        choice = response.choices[0]
                    except (BadRequestError, APIStatusError):
                        # tool_choice="required" not supported — fall through with original response
                        pass
                    # Don't continue — fall through to handle the (possibly updated) choice

                if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                    messages.append({
                        "role": "assistant",
                        "tool_calls": [
                            {"id": tc.id, "type": "function",
                             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                            for tc in choice.message.tool_calls
                        ]
                    })
                    for tc in choice.message.tool_calls:
                        tool_calls_count += 1
                        # Skip duplicate calls to the same tool in the same turn
                        if tc.function.name in called_tools:
                            content = json.dumps({"note": "Tool already called this turn. Use the previous result."})
                            messages.append({"role": "tool", "tool_call_id": tc.id, "content": content})
                            continue
                        called_tools.add(tc.function.name)
                        try:
                            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                            result = await session.call_tool(tc.function.name, arguments=args)
                            content = "".join(b.text for b in result.content if hasattr(b, "text"))
                        except Exception as e:
                            content = json.dumps({"error": str(e)})
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": content})
                else:
                    return {"response": choice.message.content or "", "tool_calls_count": tool_calls_count}


def _run_in_thread(message, history, telnet_config: dict, user_role: str = "general"):
    result = [None]
    error = [None]

    def target():
        try:
            result[0] = anyio.run(_run_chat, message, history, telnet_config, user_role)
        except BaseException as e:
            error[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout=180)  # Increased to 3 minutes for MCP tool calls

    if t.is_alive():
        raise TimeoutError("MCP chat coroutine timed out after 180s")
    if error[0] is not None:
        raise error[0]
    return result[0]


def _clean_response(text: str) -> str:
    """Remove XML tags and raw tool echoes from LLM response."""
    import re, json

    # If response is only tool echo lines like  wan_status_technical>{"key":"val"}
    # extract and format the JSON as bullet points
    tool_echo_re = re.compile(r'^(\w+)>\s*(\{.+\})\s*$', re.MULTILINE)
    matches = tool_echo_re.findall(text)
    cleaned = tool_echo_re.sub('', text).strip()

    if not cleaned and matches:
        lines = []
        for _tool, json_str in matches:
            try:
                data = json.loads(json_str)
                for k, v in data.items():
                    if v not in (None, '', 'null'):
                        lines.append(f"• {k}: {v}")
            except Exception:
                lines.append(json_str)
        return '\n'.join(lines)

    # Standard cleanup
    text = re.sub(r'<[^>]+/?>|</[^>]+>', '', text)
    text = re.sub(r'(?:function=)?\w+>\s*\{[^\n]+\}', '', text)                                            # toolname>{...}
    text = re.sub(r'^(?:function=)?[a-z][a-z0-9]*(?:_[a-z0-9]+)+\s*>\s*$', '', text, flags=re.MULTILINE)  # function=toolname> alone
    text = re.sub(r'^function=[a-z][a-z0-9_]+\s*\{[^\n]*\}', '', text, flags=re.MULTILINE)                 # function=toolname {}
    text = re.sub(r'^[a-z][a-z0-9]*(?:_[a-z0-9]+)+\s*\{[^\n]*\}', '', text, flags=re.MULTILINE)           # toolname{...}
    text = re.sub(r'^\s*•\s*\w[\w\s]*:\s*\{[^\n]*\}\s*$', '', text, flags=re.MULTILINE)  # • key: {...}
    text = re.sub(r'\n\s*\{[^}]*\}\s*\n', '\n', text)               # isolated JSON blocks
    text = re.sub(r'^[a-z][a-z0-9]*(?:_[a-z0-9]+)+\s*$', '', text, flags=re.MULTILINE)  # lone tool name headers
    text = re.sub(r'\n\s*\n+', '\n', text).strip()
    return text


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    history = [{"role": h.role, "content": h.content} for h in request.history]
    telnet_config: dict = {}
    if request.gateway_id:
        telnet_config = _get_gateway_telnet(request.gateway_id)
    try:
        data = await asyncio.to_thread(_run_in_thread, request.message, history, telnet_config)
        data["response"] = _clean_response(data["response"])
        return ChatResponse(**data)
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except BaseException as e:
        error_detail = traceback.format_exc()
        logger.error(f"Chat endpoint error:\n{error_detail}")
        inner = e
        if hasattr(e, "exceptions") and e.exceptions:
            inner = e.exceptions[0]
            if hasattr(inner, "exceptions") and inner.exceptions:
                inner = inner.exceptions[0]
        raise HTTPException(status_code=500, detail=f"{type(inner).__name__}: {str(inner)}")

