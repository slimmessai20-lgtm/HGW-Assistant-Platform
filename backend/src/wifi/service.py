import logging
from ..cnxtelnet.service1 import send_commands
import speedtest

logger = logging.getLogger(__name__)


async def enable_wifi(host: str, port: int, user: str, password: str) -> dict:
    """Active le Wi-Fi sur le serveur Telnet"""
    commands = [
        "NMC.Wifi.set(DisableLocalWiFi=false,Enable=true)",
        "NeMo.Intf.rad5g0.set(Enable=true)",
        "NeMo.Intf.rad2g0.set(Enable=true)",
        "NeMo.Intf.vap2g0priv.set(PersistentEnable=true)",
        "NeMo.Intf.vap5g0priv.set(PersistentEnable=true)"
    ]
    return await send_commands(host, port, user, password, commands)


async def factory_reset(host: str, port: int, user: str, password: str) -> dict:
    """Effectue un factory reset du Wi‑Fi (NMC.Wifi.wififactoryReset())."""
    commands = [
        "NMC.Wifi.wififactoryReset()"
    ]
    return await send_commands(host, port, user, password, commands)


async def reboot_device(host: str, port: int, user: str, password: str) -> dict:
    """Redémarre l'équipement via NMC.GroupFunction.reboot()."""
    commands = [
        "NMC.GroupFunction.reboot()"
    ]
    return await send_commands(host, port, user, password, commands)


async def disable_wifi(host: str, port: int, user: str, password: str) -> dict:
    """Désactive le Wi-Fi sur le serveur Telnet"""
    commands = [
        "NMC.Wifi.Enable=0",
        "NeMo.Intf.rad5g0.Enable=false",
        "NeMo.Intf.rad2g0.Enable=false"
    ]
    return await send_commands(host, port, user, password, commands)


async def enable_wifi_2g_ext(host: str, port: int, user: str, password: str) -> dict:
    """Active le Wi-Fi extra 2.4 GHz (réseau invité)"""
    commands = [
        "NeMo.Intf.vap2g0ext.set(PersistentEnable=true)"
    ]
    return await send_commands(host, port, user, password, commands)


async def disable_wifi_2g_ext(host: str, port: int, user: str, password: str) -> dict:
    """Désactive le Wi-Fi extra 2.4 GHz (réseau invité)"""
    commands = [
        "NeMo.Intf.vap2g0ext.set(PersistentEnable=false)"
    ]
    return await send_commands(host, port, user, password, commands)


async def enable_wifi_5g_ext(host: str, port: int, user: str, password: str) -> dict:
    """Active le Wi-Fi extra 5 GHz (réseau invité)"""
    commands = [
        "NeMo.Intf.vap5g0ext.set(PersistentEnable=true,Enable=true)"
    ]
    return await send_commands(host, port, user, password, commands)


async def disable_wifi_5g_ext(host: str, port: int, user: str, password: str) -> dict:
    """Désactive le Wi-Fi extra 5 GHz (réseau invité)"""
    commands = [
        "NeMo.Intf.vap5g0ext.set(PersistentEnable=false,Enable=false)"
    ]
    return await send_commands(host, port, user, password, commands)


def _kv(output: str) -> dict:
    """Parse KEY=value lines from Telnet output."""
    fields = {}
    for line in output.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            fields[k.strip()] = v.strip()
    return fields


def _yn(v: str) -> str:
    return "Yes" if v in ("1", "true", "True", "enabled", "up", "Up") else (
           "No"  if v in ("0", "false", "False", "disabled", "down") else v)


async def get_wifi_status(host: str, port: int, user: str, password: str) -> dict:
    """Curated WiFi status — SSID, channel, band, standards, security.
    Queries both KPN (vap2g0priv/rad2g0) and Swisscom (wl1/wl0) paths;
    error responses contain no K=V pairs so the wrong-platform paths are ignored.
    Kept to 15 commands to stay within Telnet session budget.
    """
    commands = [
        # Common
        "NMC.Wifi.Enable?",
        # SSID — KPN and Swisscom paths
        "NeMo.Intf.vap2g0priv.SSID?",
        "NeMo.Intf.vap5g0priv.SSID?",
        "NeMo.Intf.wl1.SSID?",
        "NeMo.Intf.wl0.SSID?",
        # Security — KPN and Swisscom paths
        "NeMo.Intf.vap2g0priv.Security.ModeEnabled?",
        "NeMo.Intf.vap5g0priv.Security.ModeEnabled?",
        "NeMo.Intf.wl1.Security.ModeEnabled?",
        "NeMo.Intf.wl0.Security.ModeEnabled?",
        # Radio status — KPN uses rad2g0/rad5g0, Swisscom uses wl1/wl0
        "NeMo.Intf.rad2g0.Status?",
        "NeMo.Intf.rad5g0.Status?",
        "NeMo.Intf.wl1.Status?",
        "NeMo.Intf.wl0.Status?",
        # Channel / bandwidth / standards — KPN only (Swisscom returns "?")
        "NeMo.Intf.rad2g0.Channel?",
        "NeMo.Intf.rad5g0.Channel?",
    ]
    raw = await send_commands(host, port, user, password, commands)

    # Collect all K=V pairs; error lines have no "=" so they are silently skipped
    f = {}
    for r in raw.get("results", []):
        f.update(_kv(r.get("output", "")))

    def g(*keys):
        for k in keys:
            v = f.get(k)
            if v is not None:
                return v
        return "?"

    # Radio 2.4/5 GHz status: KPN uses rad2g0/rad5g0, Swisscom uses wl1/wl0
    r2g = g("NeMo.Intf.rad2g0.Status", "NeMo.Intf.wl1.Status")
    r5g = g("NeMo.Intf.rad5g0.Status", "NeMo.Intf.wl0.Status")

    return {
        "WiFi Enabled":        _yn(g("NMC.Wifi.Enable")),
        "SSID 2.4 GHz":        g("NeMo.Intf.vap2g0priv.SSID",             "NeMo.Intf.wl1.SSID"),
        "SSID 5 GHz":          g("NeMo.Intf.vap5g0priv.SSID",             "NeMo.Intf.wl0.SSID"),
        "Security 2.4 GHz":    g("NeMo.Intf.vap2g0priv.Security.ModeEnabled", "NeMo.Intf.wl1.Security.ModeEnabled"),
        "Security 5 GHz":      g("NeMo.Intf.vap5g0priv.Security.ModeEnabled", "NeMo.Intf.wl0.Security.ModeEnabled"),
        "Radio 2.4 GHz":       _yn(r2g),
        "Radio 5 GHz":         _yn(r5g),
        "Channel 2.4 GHz":     g("NeMo.Intf.rad2g0.Channel"),
        "Channel 5 GHz":       g("NeMo.Intf.rad5g0.Channel"),
        "Bandwidth 2.4 GHz":   g("NeMo.Intf.rad2g0.CurrentOperatingChannelBandwidth"),
        "Bandwidth 5 GHz":     g("NeMo.Intf.rad5g0.CurrentOperatingChannelBandwidth"),
        "Standards 2.4 GHz":   g("NeMo.Intf.rad2g0.OperatingStandards"),
        "Standards 5 GHz":     g("NeMo.Intf.rad5g0.OperatingStandards"),
        "Max Rate 2.4 GHz":    g("NeMo.Intf.rad2g0.MaxBitRate"),
        "Max Rate 5 GHz":      g("NeMo.Intf.rad5g0.MaxBitRate"),
    }


async def set_wifi_ssid(host: str, port: int, user: str, password: str, ssid: str) -> dict:
    """Change uniquement le SSID Wi-Fi pour 2.4 et 5 GHz."""
    def quote(v: str) -> str:
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'

    commands = [
        f"NeMo.Intf.vap2g0priv.set(SSID={quote(ssid)})",
        f"NeMo.Intf.vap5g0priv.set(SSID={quote(ssid)})",
    ]
    return await send_commands(host, port, user, password, commands)


async def set_wifi_password(host: str, port: int, user: str, password: str, keypassphrase: str) -> dict:
    """Change la passphrase (KeyPassPhrase) pour 2.4 et 5 GHz.

    Utilise `NeMo.Intf.<vap>.Security.set(KeyPassPhrase="...")`.
    """
    def quote(v: str) -> str:
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'

    commands = [
        f"NeMo.Intf.vap2g0priv.Security.set(KeyPassPhrase={quote(keypassphrase)})",
        f"NeMo.Intf.vap5g0priv.Security.set(KeyPassPhrase={quote(keypassphrase)})",
    ]
    return await send_commands(host, port, user, password, commands)


async def get_wifi_password(host: str, port: int, user: str, password: str) -> dict:
    """Récupère la passphrase Wi-Fi pour 2.4 et 5 GHz.
    Essaie d'abord les paths KPN (vap2g0priv), puis Swisscom (wl1/wl0).
    """
    commands = [
        "NeMo.Intf.vap2g0priv.Security.KeyPassPhrase?",  # KPN 2.4G
        "NeMo.Intf.vap5g0priv.Security.KeyPassPhrase?",  # KPN 5G
        "NeMo.Intf.wl1.Security.KeyPassPhrase?",          # Swisscom 2.4G
        "NeMo.Intf.wl0.Security.KeyPassPhrase?",          # Swisscom 5G
    ]
    raw = await send_commands(host, port, user, password, commands)

    f = {}
    for r in raw.get("results", []):
        for line in r.get("output", "").splitlines():
            if "KeyPassPhrase=" in line:
                k = r["command"].replace("?", "")
                f[k] = line.split("=", 1)[1].strip().strip(">")

    def pick(*keys):
        for k in keys:
            v = f.get(k)
            if v:
                return v
        return "Non trouvé"

    return {
        "wifi_password_2g": pick(
            "NeMo.Intf.vap2g0priv.Security.KeyPassPhrase",
            "NeMo.Intf.wl1.Security.KeyPassPhrase"
        ),
        "wifi_password_5g": pick(
            "NeMo.Intf.vap5g0priv.Security.KeyPassPhrase",
            "NeMo.Intf.wl0.Security.KeyPassPhrase"
        ),
    }





import asyncio
import speedtest


async def perform_speedtest():
    def run_test():
        st = speedtest.Speedtest()
        st.get_servers([])
        st.get_best_server()
        download = st.download()
        upload = st.upload()
        ping = st.results.ping
        return {
            "ping_ms": ping,
            "download_mbps": round(download / 1e6, 2),
            "upload_mbps": round(upload / 1e6, 2),
            "server": st.results.server.get("host"),
            "timestamp": st.results.timestamp
        }

    try:
        return await asyncio.to_thread(run_test)
    except speedtest.ConfigRetrievalError as e:
        return {"error": f"Speedtest configuration failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}




