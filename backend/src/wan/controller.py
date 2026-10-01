
from fastapi import APIRouter, Query

from .models import TelnetRequestrole
from .service import (
    get_wan_status,
)

router = APIRouter(prefix="/wan", tags=["wan"])

@router.post("/status")
async def wan_status(request: TelnetRequestrole ):
    """
    Endpoint WAN Status
    - Normal User : retourne uniquement LinkState
    - Technical User : retourne tous les détails
    """
    return await get_wan_status(
        request.host,
        request.port,
        request.user,
        request.password,
        request.role
    )
