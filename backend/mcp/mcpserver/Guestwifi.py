from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcpserver import DEFAULT_TELNET_CONFIG

mcp = FastMCP("guestwifi")

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
#  Guest Wi-Fi 2.4 GHz
# ─────────────────────────────────────────────

@mcp.tool()
async def guest_wifi_2g_on() -> dict[str, Any]:
    """Active le Wi-Fi Guest 2.4 GHz."""
    return await _post("/guestwifi/2g/on")


@mcp.tool()
async def guest_wifi_2g_off() -> dict[str, Any]:
    """Désactive le Wi-Fi Guest 2.4 GHz."""
    return await _post("/guestwifi/2g/off")


# ─────────────────────────────────────────────
#  Guest Wi-Fi 5 GHz
# ─────────────────────────────────────────────

@mcp.tool()
async def guest_wifi_5g_on() -> dict[str, Any]:
    """Active le Wi-Fi Guest 5 GHz."""
    return await _post("/guestwifi/5g/on")


@mcp.tool()
async def guest_wifi_5g_off() -> dict[str, Any]:
    """Désactive le Wi-Fi Guest 5 GHz."""
    return await _post("/guestwifi/5g/off")


# ─────────────────────────────────────────────
#  Statut & Configuration
# ─────────────────────────────────────────────

@mcp.tool()
async def guest_wifi_status() -> dict[str, Any]:
    """Retourne le statut du Wi-Fi Guest (2.4 GHz et 5 GHz)."""
    return await _post("/guestwifi/status")


@mcp.tool()
async def guest_wifi_set_ssid(ssid: str) -> dict[str, Any]:
    """Change le nom du réseau Guest Wi-Fi (SSID) pour 2.4 GHz et 5 GHz.

    Args:
        ssid: Le nouveau nom du réseau Guest Wi-Fi.
    """
    body = {**DEFAULT_TELNET_CONFIG, "ssid": ssid}
    return await _post("/guestwifi/ssid", body)


@mcp.tool()
async def guest_wifi_set_password(keypassphrase: str) -> dict[str, Any]:
    """Change le mot de passe du réseau Guest Wi-Fi pour 2.4 GHz et 5 GHz.

    Args:
        keypassphrase: Le nouveau mot de passe du réseau Guest Wi-Fi.
    """
    body = {**DEFAULT_TELNET_CONFIG, "keypassphrase": keypassphrase}
    return await _post("/guestwifi/password", body)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()