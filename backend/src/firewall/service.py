import logging
from ..cnxtelnet.service1 import send_commands

logger = logging.getLogger(__name__)

async def enable_firewall(host: str, port: int, user: str, password: str) -> dict:
    commands = [
        'Firewall.setRespondToPing(sourceInterface="ppp_adata", service_enable={"enableIPv4":true,"enableIPv6":true})'
    ]
    return await send_commands(host, port, user, password, commands)


async def disable_firewall(host: str, port: int, user: str, password: str) -> dict:
    commands = [
        'Firewall.setRespondToPing(sourceInterface="ppp_adata", service_enable={"enableIPv4":false,"enableIPv6":false})'
    ]
    return await send_commands(host, port, user, password, commands)



async def set_firewall_level(host: str, port: int, user: str, password: str, level: str) -> dict:
    """
    Définit le niveau du firewall (Low, Medium, High).
    """
    command = f'Firewall.setFirewallLevel(level="{level}")'
    return await send_commands(host, port, user, password, [command])








# The HGW stores the firewall level as a numeric value internally.
# Mapping covers known values; unknown values are shown as-is.
_LEVEL_MAP = {
    "0": "Disabled",
    "1": "Low", "500":  "Low",
    "2": "Medium", "1000": "Medium",
    "3": "High",   "2000": "High",
    # String values returned directly
    "low": "Low", "medium": "Medium", "high": "High",
    "Low": "Low", "Medium": "Medium", "High": "High",
    "Standard": "Low", "standard": "Low",
}


def _level(v: str) -> str:
    return _LEVEL_MAP.get(v, v)   # show raw value if not in map


def _enabled(v: str) -> str:
    return "Yes" if v in ("1", "true", "True") else ("No" if v in ("0", "false", "False") else v)


def _extract_kv(output: str) -> dict:
    """Extract KEY=value pairs from a Telnet output string."""
    fields = {}
    for line in output.splitlines():
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip().replace("Firewall.", "")
            fields[k] = v.strip()
    return fields


async def get_firewall_status(host: str, port: int, user: str, password: str) -> dict:
    """Normal (general user) view — minimal fields."""
    commands = ["Firewall.Enable?", "Firewall.AdvancedLevel?"]
    raw = await send_commands(host, port, user, password, commands)
    f = {}
    for r in raw.get("results", []):
        f.update(_extract_kv(r.get("output", "")))

    enabled = _enabled(f.get("Enable", "?"))
    level   = _level(f.get("AdvancedLevel", "?"))

    return {
        "Firewall Enabled": enabled,
        "Protection Level": level,
        "Recommendation":   _recommend(enabled, level),
    }


_RECOMMENDATIONS = {
    "Low":      "Low protection — consider upgrading to Medium or High for better security.",
    "Medium":   "Good balance of security and usability. Suitable for most home networks.",
    "High":     "Maximum protection enabled. Some services or applications may be restricted.",
    "Disabled": "Firewall is disabled — the network is unprotected. Enable it immediately.",
}


def _recommend(enabled: str, level: str) -> str:
    if enabled != "Yes":
        return _RECOMMENDATIONS["Disabled"]
    return _RECOMMENDATIONS.get(level, f"Level '{level}' — verify the configuration.")


async def get_firewall_config(host: str, port: int, user: str, password: str) -> dict:
    """Technical (engineer/admin) view."""
    commands = [
        "Firewall.Enable?",
        "Firewall.AdvancedLevel?",
        "Firewall.AdvancedIPv6Level?",
    ]
    raw = await send_commands(host, port, user, password, commands)
    f = {}
    for r in raw.get("results", []):
        f.update(_extract_kv(r.get("output", "")))

    enabled = _enabled(f.get("Enable", "?"))
    ipv4    = _level(f.get("AdvancedLevel", "?"))
    ipv6    = _level(f.get("AdvancedIPv6Level", "?"))

    return {
        "Enable":         enabled,
        "IPv4 Level":     ipv4,
        "IPv6 Level":     ipv6,
        "Recommendation": _recommend(enabled, ipv4),
    }

