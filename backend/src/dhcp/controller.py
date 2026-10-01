from fastapi import APIRouter, Query
from src.models import TelnetRequest
from .service import get_dhcp_status

router = APIRouter(prefix="/dhcp", tags=["dhcp"])

@router.post("/status")
async def dhcp_status(request: TelnetRequest, role: str = Query("normal")):
    """
    Endpoint DHCP Status
    - Normal User : retourne uniquement Enable et State
    - Technical User : retourne tous les détails du pool DHCP
    """
    return await get_dhcp_status(
        request.host,
        request.port,
        request.user,
        request.password,
        role
    )
