from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcpserver import DEFAULT_TELNET_CONFIG

mcp = FastMCP("scheduler")

TIMEOUT = 90.0
BASE_URL = "http://127.0.0.1:8000"


async def _post(endpoint: str, body: dict = None) -> dict[str, Any]:
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
#  Scheduler WLAN
# ─────────────────────────────────────────────

@mcp.tool()
async def scheduler_add(
    schedule_id: str,
    begin_day: int,
    begin_hour: int,
    begin_minute: int,
    end_day: int,
    end_hour: int,
    end_minute: int
) -> dict[str, Any]:
    """Crée un schedule WLAN pour activer/désactiver le Wi-Fi automatiquement.

    Args:
        schedule_id: Identifiant du schedule (ex: 'wl0', 'wl1').
        begin_day: Jour de début (0=Lundi, 1=Mardi, ..., 6=Dimanche).
        begin_hour: Heure de début (0-23).
        begin_minute: Minute de début (0-59).
        end_day: Jour de fin (0=Lundi, 1=Mardi, ..., 6=Dimanche).
        end_hour: Heure de fin (0-23).
        end_minute: Minute de fin (0-59).
    """
    body = {
        **DEFAULT_TELNET_CONFIG,
        "schedule_id": schedule_id,
        "begin_day": begin_day,
        "begin_hour": begin_hour,
        "begin_minute": begin_minute,
        "end_day": end_day,
        "end_hour": end_hour,
        "end_minute": end_minute
    }
    return await _post("/scheduler/add", body)


@mcp.tool()
async def scheduler_enable(schedule_id: str) -> dict[str, Any]:
    """Active un schedule WLAN existant.

    Args:
        schedule_id: Identifiant du schedule à activer (ex: 'wl0').
    """
    body = {
        **DEFAULT_TELNET_CONFIG,
        "schedule_id": schedule_id,
        "enable": True
    }
    return await _post("/scheduler/enable", body)


@mcp.tool()
async def scheduler_disable(schedule_id: str) -> dict[str, Any]:
    """Désactive un schedule WLAN existant.

    Args:
        schedule_id: Identifiant du schedule à désactiver (ex: 'wl0').
    """
    body = {
        **DEFAULT_TELNET_CONFIG,
        "schedule_id": schedule_id,
        "enable": False
    }
    return await _post("/scheduler/disable", body)


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()