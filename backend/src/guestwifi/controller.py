from fastapi import APIRouter

from src.models import TelnetRequest
from .models import TelnetSSIDRequest, TelnetKeyRequest
from .service import (
    enable_guest_wifi_2g,
    disable_guest_wifi_2g,
    enable_guest_wifi_5g,
    disable_guest_wifi_5g,
)
from pydantic import BaseModel



router = APIRouter(prefix="/guestwifi", tags=["guestwifi"])


@router.post("/2g/on")
async def guest_2g_on(request: TelnetRequest):
    result = await enable_guest_wifi_2g(request.host, request.port, request.user, request.password)
    return result.get("results", []) if isinstance(result, dict) else result


@router.post("/2g/off")
async def guest_2g_off(request: TelnetRequest):
    result = await disable_guest_wifi_2g(request.host, request.port, request.user, request.password)
    return result.get("results", []) if isinstance(result, dict) else result


@router.post("/5g/on")
async def guest_5g_on(request: TelnetRequest):
    result = await enable_guest_wifi_5g(request.host, request.port, request.user, request.password)
    return result.get("results", []) if isinstance(result, dict) else result


@router.post("/5g/off")
async def guest_5g_off(request: TelnetRequest):
    result = await disable_guest_wifi_5g(request.host, request.port, request.user, request.password)
    return result.get("results", []) if isinstance(result, dict) else result


@router.post("/status")
async def guest_status(request: TelnetRequest):
    """🔎 Retourne le statut Guest Wi‑Fi"""
    from .service import get_guest_wifi_status
    result = await get_guest_wifi_status(request.host, request.port, request.user, request.password)
    return result.get("results", []) if isinstance(result, dict) else result


@router.post("/ssid")
async def guest_set_ssid(request: TelnetSSIDRequest):
    """Change uniquement le SSID du Guest Wi‑Fi (2.4 & 5 GHz)."""
    from .service import set_guest_ssid
    result = await set_guest_ssid(request.host, request.port, request.user, request.password, request.ssid)
    return result.get("results", []) if isinstance(result, dict) else result


@router.post("/password")
async def guest_set_password(request: TelnetKeyRequest):
    """Change la passphrase du Guest Wi‑Fi (KeyPassPhrase)."""
    from .service import set_guest_password
    result = await set_guest_password(request.host, request.port, request.user, request.password, request.keypassphrase)
    return result.get("results", []) if isinstance(result, dict) else result
