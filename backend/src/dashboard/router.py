"""
Dashboard Summary — fetches live HGW data sequentially for a given gateway_id.
Sequential (not parallel) to avoid overloading the HGW Telnet server.
"""
from fastapi import APIRouter, Depends, HTTPException

from src.auth.router import get_current_user
from src.chat.router import _get_gateway_telnet
from src.wifi.service import get_wifi_status
from src.wan.service import get_wan_status
from src.firewall.service import get_firewall_status
from src.devices.service import get_connected_devices

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def _safe(coro):
    try:
        return await coro
    except Exception as e:
        return {"error": str(e)}


@router.get("/{gateway_id}/summary")
async def dashboard_summary(
    gateway_id: int,
    current_user: dict = Depends(get_current_user),
):
    config = _get_gateway_telnet(gateway_id)
    if not config:
        raise HTTPException(status_code=404, detail="Gateway not found")

    h, p, u, pw = config["host"], config["port"], config["user"], config["password"]

    # Sequential — HGW Telnet servers reject multiple simultaneous sessions
    wifi    = await _safe(get_wifi_status(h, p, u, pw))
    wan_raw = await _safe(get_wan_status(h, p, u, pw, "normal"))
    fw      = await _safe(get_firewall_status(h, p, u, pw))
    devs    = await _safe(get_connected_devices(h, p, u, pw, "normal"))

    wan          = wan_raw.get("wan", {}) if isinstance(wan_raw, dict) else {}
    devices_list = devs.get("devices", []) if isinstance(devs, dict) else []

    return {
        "gateway":      {"id": gateway_id, "name": config.get("name"), "host": h},
        "wifi":         wifi,
        "wan":          wan,
        "firewall":     fw,
        "devices":      devices_list,
        "device_count": len(devices_list),
    }
