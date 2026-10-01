from fastapi import APIRouter, Query
from src.models import TelnetRequest
from .service import get_iptv_status

router = APIRouter(prefix="/IPTV", tags=["IPTV"])

@router.post("/status")
async def iptv_status(request: TelnetRequest, role: str = Query("normal")):
    """
    Endpoint pour obtenir le statut du service IPTV.
    """
    result = await get_iptv_status(
        request.host,
        request.port,
        request.user,
        request.password,
        role
    )
    return result