from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcpserver import DEFAULT_TELNET_CONFIG

mcp = FastMCP("firewall")

TIMEOUT = 90.0
BASE_URL = "http://127.0.0.1:8000"


async def _post(endpoint: str, body: dict = None, params: dict = None) -> dict[str, Any]:
    """Helper générique pour tous les appels POST vers FastAPI."""
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
#  Ping
# ─────────────────────────────────────────────

@mcp.tool()
async def firewall_ping_enable() -> dict[str, Any]:
    """Active la réponse au ping (IPv4 et IPv6) sur le firewall."""
    return await _post("/firewall/respond-to-ping/enable")


@mcp.tool()
async def firewall_ping_disable() -> dict[str, Any]:
    """Désactive la réponse au ping (IPv4 et IPv6) sur le firewall."""
    return await _post("/firewall/respond-to-ping/disable")


# ─────────────────────────────────────────────
#  Niveau du firewall
# ─────────────────────────────────────────────

@mcp.tool()
async def firewall_set_level(level: str) -> dict[str, Any]:
    """Définit le niveau de protection du firewall.

    Args:
        level: Niveau du firewall — valeurs possibles : Low, Medium, High.
    """
    return await _post("/firewall/level", params={"level": level})


# ─────────────────────────────────────────────
#  Statut
# ─────────────────────────────────────────────

@mcp.tool()
async def firewall_status_normal() -> dict[str, Any]:
    """Returns the current firewall state from the gateway. Call this tool to get live data."""
    return await _post("/firewall/firewall/status", params={"role": "normal"})


@mcp.tool()
async def firewall_status_technical() -> dict[str, Any]:
    """Returns the full firewall configuration from the gateway. Call this tool to get live data."""
    return await _post("/firewall/firewall/status", params={"role": "technical"})


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()