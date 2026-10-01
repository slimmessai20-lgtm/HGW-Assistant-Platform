from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcpserver import DEFAULT_TELNET_CONFIG

mcp = FastMCP("debogageavance")

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
#  Diagnostics
# ─────────────────────────────────────────────

@mcp.tool()
async def debug_list_faults() -> dict[str, Any]:
    """Liste les faults (erreurs/alarmes) détectés sur le Home Gateway via FaultMonitor.listFaults()."""
    return await _post("/debogageavance/faults")


@mcp.tool()
async def debug_list_oopses() -> dict[str, Any]:
    """Liste les oopses (crashes/erreurs kernel) du Home Gateway via OopsTracker.getOopses()."""
    return await _post("/debogageavance/oopses")


@mcp.tool()
async def debug_verify_plugins() -> dict[str, Any]:
    """Vérifie l'état de tous les plugins du Home Gateway via Debug.verifyPlugins()."""
    return await _post("/debogageavance/verify-plugins")


@mcp.tool()
async def debug_mqtt_status() -> dict[str, Any]:
    """Retourne l'état du broker MQTT du Home Gateway."""
    return await _post("/debogageavance/mqtt")


# ─────────────────────────────────────────────
#  Statut modem
# ─────────────────────────────────────────────

@mcp.tool()
async def modem_status_normal() -> dict[str, Any]:
    """Retourne le statut du modem (vue normale).
    Affiche : Active, Name, LastConnection, LastChanged.
    """
    return await _post("/debogageavance/devices/modem/status", params={"role": "normal"})


@mcp.tool()
async def modem_status_technical() -> dict[str, Any]:
    """Retourne le statut complet du modem (vue technique).
    Affiche : Active, Faults, Oopses, Plugins, LAN.
    """
    return await _post("/debogageavance/devices/modem/status", params={"role": "technical"})


# ─────────────────────────────────────────────
#  Ping & DNS
# ─────────────────────────────────────────────

@mcp.tool()
async def debug_access_normal() -> dict[str, Any]:
    """Vérifie l'accès réseau (vue normale).
    Teste le ping DNS et la connectivité de base.
    """
    return await _post("/debogageavance/Access", params={"role": "normal"})


@mcp.tool()
async def debug_access_technical() -> dict[str, Any]:
    """Vérifie l'accès réseau complet (vue technique).
    Teste ping, DNS et la configuration du firewall.
    """
    return await _post("/debogageavance/Access", params={"role": "technical"})


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()