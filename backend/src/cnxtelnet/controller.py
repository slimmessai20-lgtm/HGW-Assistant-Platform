from fastapi import APIRouter
from pydantic import BaseModel

from src.models import TelnetRequest
from .service import send_commands

router = APIRouter(prefix="/telnet", tags=["telnet"])


class TelnetCommandRequest(BaseModel):
    """Modèle pour exécuter des commandes Telnet génériques"""
    host: str
    port: int = 23
    user: str
    password: str
    commands: list


@router.post("/execute")
async def execute_commands(request: TelnetCommandRequest):
    """🚀 Endpoint générique pour exécuter n'importe quelle commande Telnet"""
    result = await send_commands(
        request.host,
        request.port,
        request.user,
        request.password,
        request.commands,
    )
    return result.get("results", []) if isinstance(result, dict) else result
