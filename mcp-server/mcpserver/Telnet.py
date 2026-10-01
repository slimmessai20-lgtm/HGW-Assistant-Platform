from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcpserver import DEFAULT_TELNET_CONFIG

mcp = FastMCP("telnet")

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
#  Telnet générique
# ─────────────────────────────────────────────

@mcp.tool()
async def telnet_execute(commands: list[str]) -> dict[str, Any]:
    """Exécute une ou plusieurs commandes Telnet directement sur le Home Gateway.
    Utile pour des commandes avancées non couvertes par les autres tools.

    Args:
        commands: Liste de commandes Telnet à exécuter.
                  Exemple : ["NMC.Wifi.get()", "Firewall.Enable?"]
    """
    body = {
        **DEFAULT_TELNET_CONFIG,
        "commands": commands
    }
    return await _post("/telnet/execute", body)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()