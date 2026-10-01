from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcpserver import DEFAULT_TELNET_CONFIG

mcp = FastMCP("wifi")

TIMEOUT = 90.0
BASE_URL = "http://127.0.0.1:8000"


async def _post(endpoint: str, body: dict = None) -> dict[str, Any]:
    """Helper générique pour tous les appels POST vers FastAPI."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{BASE_URL}{endpoint}",
                json=body if body is not None else DEFAULT_TELNET_CONFIG
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError as e:
        return {"error": "Connection failed", "detail": str(e)}
    except httpx.ReadTimeout:
        return {"error": "ReadTimeout", "detail": f"No response from {endpoint} within {TIMEOUT}s"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}", "detail": e.response.text}
    except Exception as e:
        return {"error": type(e).__name__, "detail": str(e)}


# ─────────────────────────────────────────────
#  Wi-Fi principal ON / OFF / STATUS
# ─────────────────────────────────────────────

@mcp.tool()
async def wifi_on() -> dict[str, Any]:
    """Active le Wi-Fi principal (2.4 GHz + 5 GHz)."""
    return await _post("/wifi/on")


@mcp.tool()
async def wifi_off() -> dict[str, Any]:
    """Désactive le Wi-Fi principal (2.4 GHz + 5 GHz)."""
    return await _post("/wifi/off")


@mcp.tool()
async def wifi_status() -> dict[str, Any]:
    """Get the current WiFi status: enabled state, SSID names, security mode, radio status, channel.
    Call this tool when the user asks about WiFi status, SSID, radio, channel, or network name.
    Do NOT call this to get the WiFi password."""
    return await _post("/wifi/status")


# ─────────────────────────────────────────────
#  Réseau invité 2.4 GHz
# ─────────────────────────────────────────────

@mcp.tool()
async def wifi_extra_2g_on() -> dict[str, Any]:
    """Active le réseau invité Wi-Fi 2.4 GHz."""
    return await _post("/wifi/extra-2g/on")


@mcp.tool()
async def wifi_extra_2g_off() -> dict[str, Any]:
    """Désactive le réseau invité Wi-Fi 2.4 GHz."""
    return await _post("/wifi/extra-2g/off")


# ─────────────────────────────────────────────
#  Réseau invité 5 GHz
# ─────────────────────────────────────────────

@mcp.tool()
async def wifi_extra_5g_on() -> dict[str, Any]:
    """Active le réseau invité Wi-Fi 5 GHz."""
    return await _post("/wifi/extra-5g/on")


@mcp.tool()
async def wifi_extra_5g_off() -> dict[str, Any]:
    """Désactive le réseau invité Wi-Fi 5 GHz."""
    return await _post("/wifi/extra-5g/off")


# ─────────────────────────────────────────────
#  SSID & Mot de passe
# ─────────────────────────────────────────────

@mcp.tool()
async def wifi_set_ssid(ssid: str) -> dict[str, Any]:
    """Change le nom du réseau Wi-Fi (SSID) pour 2.4 GHz et 5 GHz.

    Args:
        ssid: Le nouveau nom du réseau Wi-Fi.
    """
    body = {**DEFAULT_TELNET_CONFIG, "ssid": ssid}
    return await _post("/wifi/ssid", body)


@mcp.tool()
async def wifi_set_password(keypassphrase: str) -> dict[str, Any]:
    """Change le mot de passe Wi-Fi pour 2.4 GHz et 5 GHz.

    Args:
        keypassphrase: Le nouveau mot de passe Wi-Fi.
    """
    body = {**DEFAULT_TELNET_CONFIG, "keypassphrase": keypassphrase}
    return await _post("/wifi/password", body)


@mcp.tool()
async def wifi_get_password() -> dict[str, Any]:
    """Get the current WiFi password (KeyPassPhrase) for 2.4 GHz and 5 GHz.
    Call this tool ONLY when the user explicitly asks for the WiFi password or key.
    Do NOT call this for WiFi status, SSID, or channel information."""
    return await _post("/wifi/get-password")


# ─────────────────────────────────────────────
#  Maintenance
# ─────────────────────────────────────────────

@mcp.tool()
async def wifi_factory_reset() -> dict[str, Any]:
    """Effectue un factory reset du Wi-Fi (NMC.Wifi.wififactoryReset()).
    ⚠️ Réinitialise tous les paramètres Wi-Fi aux valeurs d'usine.
    """
    return await _post("/wifi/factory-reset")


@mcp.tool()
async def wifi_reboot() -> dict[str, Any]:
    """Redémarre le Home Gateway (NMC.GroupFunction.reboot()).
    ⚠️ L'appareil sera indisponible pendant quelques minutes.
    """
    return await _post("/wifi/reboot")


@mcp.tool()
async def wifi_speedtest() -> dict[str, Any]:
    """Lance un test de vitesse internet et retourne ping, download et upload."""
    return await _post("/wifi/speedtest", body={})


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()