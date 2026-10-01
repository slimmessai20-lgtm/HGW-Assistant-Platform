from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcpserver import DEFAULT_TELNET_CONFIG

mcp = FastMCP("devices")

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


async def _get(endpoint: str, params: dict = None) -> dict[str, Any]:
    """Helper générique pour les appels POST avec query params."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{BASE_URL}{endpoint}",
                json=DEFAULT_TELNET_CONFIG,
                params=params
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
#  Devices
# ─────────────────────────────────────────────

@mcp.tool()
async def devices_list_normal() -> dict[str, Any]:
    """Retourne la liste des appareils connectés au HGW (vue normale).
    Affiche uniquement : Nom, Type d'appareil, Source de découverte.
    """
    return await _get("/devices/devices/list", params={"role": "normal"})


@mcp.tool()
async def devices_list_technical() -> dict[str, Any]:
    """Retourne la liste des appareils connectés au HGW (vue technique).
    Affiche les détails avancés : MAC, IPv4, IPv6, Interface, FirstSeen, LastConnection.
    """
    return await _get("/devices/devices/list", params={"role": "technical"})


@mcp.tool()
async def devices_hgw_info() -> dict[str, Any]:
    """Retourne les informations complètes du Home Gateway (HGW)."""
    return await _post("/devices/devices/hgw")


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()