from fastapi import APIRouter , Query
from typing import Any

from pydantic import BaseModel

from src.models import TelnetRequest
from .service import FaultMonitor, Debug ,get_modem_status,ping_dns
router = APIRouter(prefix="/debogageavance", tags=["debogageavance"])


@router.post("/faults")
async def post_faults(request: TelnetRequest) -> Any:
    """Lister les faults du modem via Telnet en appelant `FaultMonitor.listFaults()`.

    Le body doit être un `TelnetRequest` (host/port/user/password).
    """
    result = await FaultMonitor.listFaults(request.host, request.port, request.user, request.password)
    return result.get("results", []) if isinstance(result, dict) else result


@router.post("/verify-plugins")
async def post_verify_plugins(request: TelnetRequest) -> Any:
    """Appelle `Debug.verifyPlugins()` via Telnet; accepte `TelnetRequest`."""
    result = await Debug.verifyPlugins(request.host, request.port, request.user, request.password)
    return result.get("results", []) if isinstance(result, dict) else result


@router.post("/oopses")
async def post_oopses(request: TelnetRequest) -> Any:
    """Lister les oopses du modem via Telnet`.

    Le body doit être un `TelnetRequest` (host/port/user/password).
    """
    result = await FaultMonitor.listoops(request.host, request.port, request.user, request.password)
    return result.get("results", []) if isinstance(result, dict) else result    

@router.post("/mqtt")
async def post_mqtt(request: TelnetRequest) -> Any:
    """Appelle `MQTT?` via Telnet; accepte `TelnetRequest`."""
    result = await Debug.listMQTT(request.host, request.port, request.user, request.password)
    return result.get("results", []) if isinstance(result, dict) else result




@router.post("/devices/modem/status")
async def modem_status(request: TelnetRequest, role: str = Query("normal")):
    return await get_modem_status(
        request.host,
        request.port,
        request.user,
        request.password,
        role
    )

@router.post("/Access")
async def access(request: TelnetRequest, role: str = Query("normal")):
    return await ping_dns(
        request.host,
        request.port,
        request.user,
        request.password,
        role
    )
