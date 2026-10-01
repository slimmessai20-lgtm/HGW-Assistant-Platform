from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcpserver import DEFAULT_TELNET_CONFIG

mcp = FastMCP("iptv")

TIMEOUT = 90.0
BASE_URL = "http://127.0.0.1:8000"


async def _post(endpoint: str, body: dict = None, params: dict = None) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{BASE_URL}{endpoint}",
                json=body if body is not None else DEFAULT_TELNET_CONFIG,
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
#  IPTV
# ─────────────────────────────────────────────

@mcp.tool()
async def iptv_status_normal() -> dict[str, Any]:
    """Retourne le statut du service IPTV (vue normale).
    Affiche : état interface IPTV et politique firewall.
    """
    return await _post("/IPTV/status", params={"role": "normal"})


@mcp.tool()
async def iptv_status_technical() -> dict[str, Any]:
    """Retourne le statut complet du service IPTV (vue technique).
    Affiche : chaînes firewall IPTV, politique, interfaces ATM et VLAN IPTV.
    """
    return await _post("/IPTV/status", params={"role": "technical"})


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()