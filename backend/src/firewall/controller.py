from fastapi import APIRouter, HTTPException, Query
from .service import enable_firewall, disable_firewall ,set_firewall_level,get_firewall_status,get_firewall_config
from src.models import TelnetRequest


router = APIRouter(prefix="/firewall", tags=["firewall"])

@router.post("/respond-to-ping/enable")
async def enable_ping(request: TelnetRequest):
    """
    Endpoint pour activer la réponse au ping (IPv4 et IPv6).
    """
    result = await enable_firewall(request.host, request.port, request.user, request.password)
    return {"status": "success", "action": "ping enabled", "result": result}


@router.post("/respond-to-ping/disable")
async def disable_ping(request: TelnetRequest):
    """
    Endpoint pour désactiver la réponse au ping (IPv4 et IPv6).
    """
    result = await disable_firewall(request.host, request.port, request.user, request.password)
    return {"status": "success", "action": "ping disabled", "result": result}

@router.post("/level")
async def set_level(request: TelnetRequest, level: str):
    """
    Endpoint pour définir le niveau du firewall (Low, Medium, High).
    """
    result = await set_firewall_level(request.host, request.port, request.user, request.password, level)
    return {"status": "success", "action": f"firewall level set to {level}", "result": result}








@router.post("/firewall/status")
async def firewall_status(request: TelnetRequest, role: str = Query(..., description="normal or technical")):
    try:
        if role.lower() == "technical":
            return await get_firewall_config(request.host, request.port, request.user, request.password)
        return await get_firewall_status(request.host, request.port, request.user, request.password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
