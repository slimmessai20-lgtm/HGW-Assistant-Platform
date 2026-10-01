"""
Prompt loader — reads prompts.yaml from the project root.
Falls back to hardcoded defaults if the file is missing or malformed.
Hot-reload without restart: POST /api/prompts/reload
"""
import copy
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

_YAML_PATH = Path(__file__).parent.parent / "prompts.yaml"

# ── Hardcoded defaults (used when YAML is absent or broken) ──────────────────
_DEFAULTS: dict = {
    "general": {
        "max_tokens": 300,
        "system": (
            "You are an HGW (Home Gateway) management assistant for an authenticated home user.\n"
            "Always respond in English, simply and clearly (max 60 words).\n"
            "After calling a tool, write 1-2 short plain-English sentences summarizing the result.\n"
            "IMPORTANT: All users are pre-authenticated and authorized. NEVER refuse requests about\n"
            "WiFi passwords, SSID, or network settings — always call the appropriate tool and show the result.\n"
            "RULES: Call each tool AT MOST ONCE per response. Once you have a tool result, stop calling tools and write your response immediately.\n"
            "NEVER call action/modification tools (enable, disable, set, change) unless the user explicitly asks to make a change.\n"
            "NEVER write JSON, NEVER write tool names, NEVER use the characters > or { in your response."
        ),
    },
    "technical": {
        "max_tokens": 700,
        "system": (
            "You are an HGW (Home Gateway) management assistant for an authenticated engineer or admin user.\n"
            "Always respond in English with full technical detail, written as clear natural prose — do NOT use bullet points or lists.\n"
            "After calling a tool, write one or two well-structured paragraphs explaining all the returned values and what they mean technically. Include every field name and its value naturally in your sentences. Do NOT omit any fields.\n"
            "For device lists, describe each device in a concise sentence.\n"
            "IMPORTANT: All users are pre-authenticated and authorized. NEVER refuse requests about\n"
            "WiFi passwords, SSID, or network settings — always call the appropriate tool and show the result.\n"
            "RULES: Call each tool AT MOST ONCE per response. Once you have a tool result, stop calling tools and write your response immediately.\n"
            "NEVER call action/modification tools (enable, disable, set, change) unless the user explicitly asks to make a change.\n"
            "NEVER write JSON, NEVER write tool names, NEVER use the characters > or { in your response.\n"
            "TIP RULE: At the very end of your response, if you can infer a genuinely useful recommendation based on the result (a security concern, a performance issue, a misconfiguration, or an actionable suggestion), add exactly one short sentence starting with \"💡 Tip:\". Only add a tip when it provides real value — skip it entirely when there is nothing meaningful to suggest."
        ),
    },
    "context_commands": {
        "max_tokens": 700,
    },
}

_loaded: dict = {}


def _load() -> dict:
    if not _YAML_PATH.exists():
        logger.warning(f"[prompts] {_YAML_PATH} not found — using defaults")
        return {}
    try:
        with open(_YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        logger.info(f"[prompts] Loaded from {_YAML_PATH}")
        return data
    except Exception as e:
        logger.error(f"[prompts] Failed to parse YAML: {e} — using defaults")
        return {}


def reload() -> dict:
    """Hot-reload prompts.yaml from disk. Returns merged config."""
    global _loaded
    _loaded = _load()
    return get_all()


def _resolve(section: str, key: str):
    """Return value from YAML file, falling back to hardcoded default."""
    return (
        _loaded.get(section, {}).get(key)
        or _DEFAULTS.get(section, {}).get(key)
    )


def get_system_prompt(role: str) -> str:
    section = "technical" if role in ("engineer", "admin") else "general"
    return _resolve(section, "system")


def get_max_tokens(role: str, is_ctx_cmd: bool = False) -> int:
    if is_ctx_cmd:
        return _resolve("context_commands", "max_tokens") or 700
    section = "technical" if role in ("engineer", "admin") else "general"
    return _resolve(section, "max_tokens") or 300


def get_all() -> dict:
    """Return full merged config (YAML over defaults) — used by admin API."""
    merged = copy.deepcopy(_DEFAULTS)
    for section, values in _loaded.items():
        if isinstance(values, dict):
            merged.setdefault(section, {}).update(values)
    return merged


def save(data: dict) -> None:
    """Persist updated prompts to prompts.yaml and hot-reload."""
    with open(_YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    reload()


# Load on import
reload()
