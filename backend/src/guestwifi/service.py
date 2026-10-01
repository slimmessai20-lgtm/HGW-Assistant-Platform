from ..cnxtelnet.service import send_commands


async def enable_guest_wifi_2g(host: str, port: int, user: str, password: str) -> dict:
    commands = [
        "NeMo.Intf.vap2g0guest.set(Enable=true, PersistentEnable=true)"
    ]
    return await send_commands(host, port, user, password, commands)


async def disable_guest_wifi_2g(host: str, port: int, user: str, password: str) -> dict:
    commands = [
        "NeMo.Intf.vap2g0guest.set(Enable=false, PersistentEnable=false)"
    ]
    return await send_commands(host, port, user, password, commands)


async def enable_guest_wifi_5g(host: str, port: int, user: str, password: str) -> dict:
    commands = [
        "NeMo.Intf.vap5g0guest.set(Enable=true, PersistentEnable=true)"
    ]
    return await send_commands(host, port, user, password, commands)


async def disable_guest_wifi_5g(host: str, port: int, user: str, password: str) -> dict:
    commands = [
        "NeMo.Intf.vap5g0guest.set(Enable=false, PersistentEnable=false)"
    ]
    return await send_commands(host, port, user, password, commands)


async def get_guest_wifi_status(host: str, port: int, user: str, password: str) -> dict:
    """Récupère le statut du Guest Wi‑Fi (2.4 & 5 GHz) et des interfaces associées"""
    commands = [
        "NeMo.Intf.vap2g0guest.get()",
        "NeMo.Intf.vap5g0guest.get()",
       
    ]
    raw = await send_commands(host, port, user, password, commands)


    return raw


async def set_guest_ssid(host: str, port: int, user: str, password: str, ssid: str) -> dict:
    """Change uniquement le SSID du Guest Wi‑Fi (2.4 & 5 GHz)."""
    def quote(v: str) -> str:
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'

    commands = [
        f"NeMo.Intf.vap2g0guest.set(SSID={quote(ssid)})",
        f"NeMo.Intf.vap5g0guest.set(SSID={quote(ssid)})",
    ]
    return await send_commands(host, port, user, password, commands)


async def set_guest_password(host: str, port: int, user: str, password: str, keypassphrase: str) -> dict:
    """Change la passphrase du Guest Wi‑Fi (KeyPassPhrase)."""
    def quote(v: str) -> str:
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'

    commands = [
        f"NeMo.Intf.vap2g0guest.Security.set(KeyPassPhrase={quote(keypassphrase)})",
        f"NeMo.Intf.vap5g0guest.Security.set(KeyPassPhrase={quote(keypassphrase)})",
    ]
    return await send_commands(host, port, user, password, commands)
