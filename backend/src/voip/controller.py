from fastapi import APIRouter, Query
from src.models import TelnetRequest
from .service import get_voip_status

router = APIRouter(prefix="/voip", tags=["voip"])

@router.post("/status")
async def voip_status(request: TelnetRequest, role: str = Query("normal")):
    """
    Endpoint pour obtenir le statut du service VoIP.
    """
    result = await get_voip_status(
        request.host,
        request.port,
        request.user,
        request.password,
        role
    )
    return result
