from fastapi import APIRouter, HTTPException, Query

from .models import DevicesRequest
from .service import get_connected_devices ,get_hgw_info
from src.models import TelnetRequest

router = APIRouter(prefix="/devices", tags=["devices"])



@router.post("/devices/list")
async def device_list(request: TelnetRequest, role: str = Query(..., description="normal or technical")):
    """
    Endpoint Device List Scenario
    - Normal User : retourne uniquement Name, DeviceType, Active
    - Technical User : retourne détails avancés (MAC, IPv4, IPv6, Interface, etc.)
    """
    try:
        result = await get_connected_devices(
            request.host,
            request.port,
            request.user,
            request.password,
            role
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message", "Unknown error"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






@router.post("/devices/hgw")
async def hgw_info(req: DevicesRequest):
    """
    Endpoint indépendant pour récupérer les infos du HGW (Home Gateway).
    """
    result = await get_hgw_info(
        host=req.host,
        port=req.port,
        user=req.user,
        password=req.password
    )
    return result
