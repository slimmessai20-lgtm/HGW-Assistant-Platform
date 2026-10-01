from fastapi import APIRouter

from src.models import TelnetRequest
from .models import TelnetSSIDRequest, TelnetKeyRequest
from .service import (
    enable_wifi,
    disable_wifi,
    enable_wifi_2g_ext,
    disable_wifi_2g_ext,
    enable_wifi_5g_ext,
    disable_wifi_5g_ext,
    set_wifi_ssid,
    perform_speedtest,
    get_wifi_password,
    get_wifi_status,
)

router = APIRouter(prefix="/wifi", tags=["wifi"])


# ─────────────────────────────────────────────
#  Wi-Fi principal ON / OFF / STATUS
# ─────────────────────────────────────────────

@router.post("/on")
async def enable_wifi_endpoint(request: TelnetRequest):
    result = await enable_wifi(request.host, request.port, request.user, request.password)
    if isinstance(result, dict):
        return {"success": True, "action": "wifi_on", "result": result.get("results", result)}
    return {"success": True, "action": "wifi_on", "result": result}


@router.post("/off")
async def disable_wifi_endpoint(request: TelnetRequest):
    result = await disable_wifi(request.host, request.port, request.user, request.password)
    if isinstance(result, dict):
        return {"success": True, "action": "wifi_off", "result": result.get("results", result)}
    return {"success": True, "action": "wifi_off", "result": result}


@router.post("/status")
async def wifi_status(request: TelnetRequest):
    """Retourne le statut Wi-Fi et des interfaces"""
    result = await get_wifi_status(request.host, request.port, request.user, request.password)
    return {
        "success": True,
        "action": "wifi_status",
        "result": result.get("results", result) if isinstance(result, dict) else result
    }


# ─────────────────────────────────────────────
#  Réseau invité 2.4 GHz
# ─────────────────────────────────────────────

@router.post("/extra-2g/on")
async def enable_wifi_2g_ext_endpoint(request: TelnetRequest):
    """Active le Wi-Fi extra 2.4 GHz (réseau invité)"""
    result = await enable_wifi_2g_ext(request.host, request.port, request.user, request.password)
    return {
        "success": True,
        "action": "wifi_extra_2g_on",
        "result": result.get("results", result) if isinstance(result, dict) else result
    }


@router.post("/extra-2g/off")
async def disable_wifi_2g_ext_endpoint(request: TelnetRequest):
    """Désactive le Wi-Fi extra 2.4 GHz (réseau invité)"""
    result = await disable_wifi_2g_ext(request.host, request.port, request.user, request.password)
    return {
        "success": True,
        "action": "wifi_extra_2g_off",
        "result": result.get("results", result) if isinstance(result, dict) else result
    }


# ─────────────────────────────────────────────
#  Réseau invité 5 GHz
# ─────────────────────────────────────────────

@router.post("/extra-5g/on")
async def enable_wifi_5g_ext_endpoint(request: TelnetRequest):
    """Active le Wi-Fi extra 5 GHz (réseau invité)"""
    result = await enable_wifi_5g_ext(request.host, request.port, request.user, request.password)
    return {
        "success": True,
        "action": "wifi_extra_5g_on",
        "result": result.get("results", result) if isinstance(result, dict) else result
    }


@router.post("/extra-5g/off")
async def disable_wifi_5g_ext_endpoint(request: TelnetRequest):
    """Désactive le Wi-Fi extra 5 GHz (réseau invité)"""
    result = await disable_wifi_5g_ext(request.host, request.port, request.user, request.password)
    return {
        "success": True,
        "action": "wifi_extra_5g_off",
        "result": result.get("results", result) if isinstance(result, dict) else result
    }


# ─────────────────────────────────────────────
#  SSID & Mot de passe
# ─────────────────────────────────────────────

@router.post("/ssid")
async def set_ssid(request: TelnetSSIDRequest):
    """Change le SSID Wi-Fi (2.4 & 5 GHz)."""
    result = await set_wifi_ssid(request.host, request.port, request.user, request.password, request.ssid)
    return {
        "success": True,
        "action": "wifi_set_ssid",
        "result": result.get("results", result) if isinstance(result, dict) else result
    }


@router.post("/password")
async def set_password(request: TelnetKeyRequest):
    """Change la passphrase Wi-Fi (KeyPassPhrase) pour 2.4 & 5 GHz."""
    from .service import set_wifi_password
    result = await set_wifi_password(request.host, request.port, request.user, request.password, request.keypassphrase)
    return {
        "success": True,
        "action": "wifi_set_password",
        "result": result.get("results", result) if isinstance(result, dict) else result
    }


@router.post("/get-password")
async def wifi_get_password_endpoint(req: TelnetRequest):
    """Récupère le mot de passe Wi-Fi actuel (KeyPassPhrase) pour 2.4 & 5 GHz."""
    result = await get_wifi_password(
        host=req.host,
        port=req.port,
        user=req.user,
        password=req.password
    )
    return result


# ─────────────────────────────────────────────
#  Maintenance
# ─────────────────────────────────────────────

@router.post("/factory-reset")
async def wifi_factory_reset(request: TelnetRequest):
    """Effectue un factory reset Wi-Fi: NMC.Wifi.wififactoryReset()"""
    from .service import factory_reset
    result = await factory_reset(request.host, request.port, request.user, request.password)
    return {
        "success": True,
        "action": "wifi_factory_reset",
        "result": result.get("results", result) if isinstance(result, dict) else result
    }


@router.post("/reboot")
async def wifi_reboot(request: TelnetRequest):
    """Redémarre l'appareil: NMC.GroupFunction.reboot()"""
    from .service import reboot_device
    result = await reboot_device(request.host, request.port, request.user, request.password)
    return {
        "success": True,
        "action": "wifi_reboot",
        "result": result.get("results", result) if isinstance(result, dict) else result
    }


# ─────────────────────────────────────────────
#  Speedtest
# ─────────────────────────────────────────────

@router.post("/speedtest")
async def wifi_speedtest():
    """Lance un test de vitesse internet."""
    result = await perform_speedtest()
    # perform_speedtest retourne déjà un dict propre
    return {"success": True, "action": "wifi_speedtest", **result}