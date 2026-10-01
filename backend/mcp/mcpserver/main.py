from mcp.server.fastmcp import FastMCP
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mcpserver import DEFAULT_TELNET_CONFIG

from typing import Any
import httpx

mcp = FastMCP("HomeGateway")

TIMEOUT = 90.0
BASE_URL = "http://127.0.0.1:8000"


async def _post(endpoint: str, body: dict = None, params: dict = None) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{BASE_URL}{endpoint}",
                json=body if body is not None else DEFAULT_TELNET_CONFIG,
                params=params
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError as e:
        return {"error": "Connection failed", "detail": str(e)}
    except httpx.ReadTimeout:
        return {"error": "ReadTimeout", "detail": f"No response from {endpoint} within {TIMEOUT}s"}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}", "detail": e.response.text}
    except Exception as e:
        return {"error": type(e).__name__, "detail": str(e)}


# ═══════════════════════════════════════════════
#  WIFI
# ═══════════════════════════════════════════════

@mcp.tool()
async def wifi_on() -> dict[str, Any]:
    """Active le Wi-Fi principal (2.4 GHz + 5 GHz)."""
    return await _post("/wifi/on")

@mcp.tool()
async def wifi_off() -> dict[str, Any]:
    """Désactive le Wi-Fi principal (2.4 GHz + 5 GHz)."""
    return await _post("/wifi/off")

@mcp.tool()
async def wifi_status() -> dict[str, Any]:
    """Retourne le statut complet du Wi-Fi et des interfaces radio."""
    return await _post("/wifi/status")

@mcp.tool()
async def wifi_extra_2g_on() -> dict[str, Any]:
    """Active le réseau invité Wi-Fi 2.4 GHz."""
    return await _post("/wifi/extra-2g/on")

@mcp.tool()
async def wifi_extra_2g_off() -> dict[str, Any]:
    """Désactive le réseau invité Wi-Fi 2.4 GHz."""
    return await _post("/wifi/extra-2g/off")

@mcp.tool()
async def wifi_extra_5g_on() -> dict[str, Any]:
    """Active le réseau invité Wi-Fi 5 GHz."""
    return await _post("/wifi/extra-5g/on")

@mcp.tool()
async def wifi_extra_5g_off() -> dict[str, Any]:
    """Désactive le réseau invité Wi-Fi 5 GHz."""
    return await _post("/wifi/extra-5g/off")

@mcp.tool()
async def wifi_set_ssid(ssid: str) -> dict[str, Any]:
    """Change le SSID Wi-Fi pour 2.4 GHz et 5 GHz.
    Args:
        ssid: Le nouveau nom du réseau Wi-Fi.
    """
    return await _post("/wifi/ssid", {**DEFAULT_TELNET_CONFIG, "ssid": ssid})

@mcp.tool()
async def wifi_set_password(keypassphrase: str) -> dict[str, Any]:
    """Change le mot de passe Wi-Fi pour 2.4 GHz et 5 GHz.
    Args:
        keypassphrase: Le nouveau mot de passe Wi-Fi.
    """
    return await _post("/wifi/password", {**DEFAULT_TELNET_CONFIG, "keypassphrase": keypassphrase})

@mcp.tool()
async def wifi_get_password() -> dict[str, Any]:
    """Récupère le mot de passe Wi-Fi actuel pour 2.4 GHz et 5 GHz."""
    return await _post("/wifi/get-password")

@mcp.tool()
async def wifi_factory_reset() -> dict[str, Any]:
    """Effectue un factory reset du Wi-Fi. ⚠️ Réinitialise tous les paramètres Wi-Fi."""
    return await _post("/wifi/factory-reset")

@mcp.tool()
async def wifi_reboot() -> dict[str, Any]:
    """Redémarre le Home Gateway. ⚠️ L'appareil sera indisponible quelques minutes."""
    return await _post("/wifi/reboot")

@mcp.tool()
async def wifi_speedtest() -> dict[str, Any]:
    """Lance un test de vitesse internet et retourne ping, download et upload."""
    return await _post("/wifi/speedtest", body={})


# ═══════════════════════════════════════════════
#  DEVICES
# ═══════════════════════════════════════════════

@mcp.tool()
async def devices_list_normal() -> dict[str, Any]:
    """Retourne la liste des appareils connectés (vue normale) : Nom, Type, Source."""
    return await _post("/devices/devices/list", params={"role": "normal"})

@mcp.tool()
async def devices_list_technical() -> dict[str, Any]:
    """Retourne la liste des appareils connectés (vue technique) : MAC, IPv4, IPv6, Interface."""
    return await _post("/devices/devices/list", params={"role": "technical"})

@mcp.tool()
async def devices_hgw_info() -> dict[str, Any]:
    """Retourne les informations complètes du Home Gateway (HGW)."""
    return await _post("/devices/devices/hgw")


# ═══════════════════════════════════════════════
#  WAN
# ═══════════════════════════════════════════════

@mcp.tool()
async def wan_status_normal() -> dict[str, Any]:
    """Retourne l'état de la connexion WAN (vue normale) : LinkState."""
    return await _post("/wan/status", {**DEFAULT_TELNET_CONFIG, "role": "normal"})

@mcp.tool()
async def wan_status_technical() -> dict[str, Any]:
    """Retourne l'état complet de la connexion WAN (vue technique) : IP, DNS, gateway."""
    return await _post("/wan/status", {**DEFAULT_TELNET_CONFIG, "role": "technical"})


# ═══════════════════════════════════════════════
#  GUEST WIFI
# ═══════════════════════════════════════════════

@mcp.tool()
async def guest_wifi_2g_on() -> dict[str, Any]:
    """Active le Wi-Fi Guest 2.4 GHz."""
    return await _post("/guestwifi/2g/on")

@mcp.tool()
async def guest_wifi_2g_off() -> dict[str, Any]:
    """Désactive le Wi-Fi Guest 2.4 GHz."""
    return await _post("/guestwifi/2g/off")

@mcp.tool()
async def guest_wifi_5g_on() -> dict[str, Any]:
    """Active le Wi-Fi Guest 5 GHz."""
    return await _post("/guestwifi/5g/on")

@mcp.tool()
async def guest_wifi_5g_off() -> dict[str, Any]:
    """Désactive le Wi-Fi Guest 5 GHz."""
    return await _post("/guestwifi/5g/off")

@mcp.tool()
async def guest_wifi_status() -> dict[str, Any]:
    """Retourne le statut du Wi-Fi Guest (2.4 GHz et 5 GHz)."""
    return await _post("/guestwifi/status")

@mcp.tool()
async def guest_wifi_set_ssid(ssid: str) -> dict[str, Any]:
    """Change le SSID du réseau Guest Wi-Fi pour 2.4 GHz et 5 GHz.
    Args:
        ssid: Le nouveau nom du réseau Guest.
    """
    return await _post("/guestwifi/ssid", {**DEFAULT_TELNET_CONFIG, "ssid": ssid})

@mcp.tool()
async def guest_wifi_set_password(keypassphrase: str) -> dict[str, Any]:
    """Change le mot de passe du réseau Guest Wi-Fi pour 2.4 GHz et 5 GHz.
    Args:
        keypassphrase: Le nouveau mot de passe du réseau Guest.
    """
    return await _post("/guestwifi/password", {**DEFAULT_TELNET_CONFIG, "keypassphrase": keypassphrase})


# ═══════════════════════════════════════════════
#  FIREWALL
# ═══════════════════════════════════════════════

@mcp.tool()
async def firewall_ping_enable() -> dict[str, Any]:
    """Active la réponse au ping (IPv4 et IPv6) sur le firewall."""
    return await _post("/firewall/respond-to-ping/enable")

@mcp.tool()
async def firewall_ping_disable() -> dict[str, Any]:
    """Désactive la réponse au ping (IPv4 et IPv6) sur le firewall."""
    return await _post("/firewall/respond-to-ping/disable")

@mcp.tool()
async def firewall_set_level(level: str) -> dict[str, Any]:
    """Définit le niveau de protection du firewall.
    Args:
        level: Niveau du firewall — Low, Medium ou High.
    """
    return await _post("/firewall/level", params={"level": level})

@mcp.tool()
async def firewall_status_normal() -> dict[str, Any]:
    """Retourne l'état général du firewall (vue normale) : Enable, Status, Level."""
    return await _post("/firewall/firewall/status", params={"role": "normal"})

@mcp.tool()
async def firewall_status_technical() -> dict[str, Any]:
    """Retourne la configuration complète du firewall (vue technique)."""
    return await _post("/firewall/firewall/status", params={"role": "technical"})


# ═══════════════════════════════════════════════
#  TELNET GÉNÉRIQUE
# ═══════════════════════════════════════════════

@mcp.tool()
async def telnet_execute(commands: list[str]) -> dict[str, Any]:
    """Exécute des commandes Telnet directement sur le Home Gateway.
    Args:
        commands: Liste de commandes Telnet. Ex: ["NMC.Wifi.get()", "Firewall.Enable?"]
    """
    return await _post("/telnet/execute", {**DEFAULT_TELNET_CONFIG, "commands": commands})


# ═══════════════════════════════════════════════
#  DÉBOGAGE AVANCÉ
# ═══════════════════════════════════════════════

@mcp.tool()
async def debug_list_faults() -> dict[str, Any]:
    """Liste les faults (erreurs/alarmes) du Home Gateway."""
    return await _post("/debogageavance/faults")

@mcp.tool()
async def debug_list_oopses() -> dict[str, Any]:
    """Liste les oopses (crashes kernel) du Home Gateway."""
    return await _post("/debogageavance/oopses")

@mcp.tool()
async def debug_verify_plugins() -> dict[str, Any]:
    """Vérifie l'état de tous les plugins du Home Gateway."""
    return await _post("/debogageavance/verify-plugins")

@mcp.tool()
async def debug_mqtt_status() -> dict[str, Any]:
    """Retourne l'état du broker MQTT du Home Gateway."""
    return await _post("/debogageavance/mqtt")

@mcp.tool()
async def modem_status_normal() -> dict[str, Any]:
    """Retourne le statut du modem (vue normale) : Active, Name, LastConnection."""
    return await _post("/debogageavance/devices/modem/status", params={"role": "normal"})

@mcp.tool()
async def modem_status_technical() -> dict[str, Any]:
    """Retourne le statut complet du modem (vue technique) : Faults, Oopses, Plugins, LAN."""
    return await _post("/debogageavance/devices/modem/status", params={"role": "technical"})

@mcp.tool()
async def debug_access_normal() -> dict[str, Any]:
    """Vérifie l'accès réseau (vue normale) : ping et DNS."""
    return await _post("/debogageavance/Access", params={"role": "normal"})

@mcp.tool()
async def debug_access_technical() -> dict[str, Any]:
    """Vérifie l'accès réseau complet (vue technique) : ping, DNS et firewall."""
    return await _post("/debogageavance/Access", params={"role": "technical"})


# ═══════════════════════════════════════════════
#  VOIP
# ═══════════════════════════════════════════════

@mcp.tool()
async def voip_status_normal() -> dict[str, Any]:
    """Retourne le statut du service VoIP (vue normale)."""
    return await _post("/voip/status", params={"role": "normal"})

@mcp.tool()
async def voip_status_technical() -> dict[str, Any]:
    """Retourne le statut complet du service VoIP (vue technique) : QoS, firewall."""
    return await _post("/voip/status", params={"role": "technical"})


# ═══════════════════════════════════════════════
#  SCHEDULER
# ═══════════════════════════════════════════════

@mcp.tool()
async def scheduler_add(
    schedule_id: str,
    begin_day: int,
    begin_hour: int,
    begin_minute: int,
    end_day: int,
    end_hour: int,
    end_minute: int
) -> dict[str, Any]:
    """Crée un schedule WLAN pour activer/désactiver le Wi-Fi automatiquement.
    Args:
        schedule_id: Identifiant du schedule (ex: 'wl0').
        begin_day: Jour de début (0=Lundi ... 6=Dimanche).
        begin_hour: Heure de début (0-23).
        begin_minute: Minute de début (0-59).
        end_day: Jour de fin (0=Lundi ... 6=Dimanche).
        end_hour: Heure de fin (0-23).
        end_minute: Minute de fin (0-59).
    """
    body = {
        **DEFAULT_TELNET_CONFIG,
        "schedule_id": schedule_id,
        "begin_day": begin_day,
        "begin_hour": begin_hour,
        "begin_minute": begin_minute,
        "end_day": end_day,
        "end_hour": end_hour,
        "end_minute": end_minute
    }
    return await _post("/scheduler/add", body)

@mcp.tool()
async def scheduler_enable(schedule_id: str) -> dict[str, Any]:
    """Active un schedule WLAN existant.
    Args:
        schedule_id: Identifiant du schedule à activer (ex: 'wl0').
    """
    return await _post("/scheduler/enable", {**DEFAULT_TELNET_CONFIG, "schedule_id": schedule_id, "enable": True})

@mcp.tool()
async def scheduler_disable(schedule_id: str) -> dict[str, Any]:
    """Désactive un schedule WLAN existant.
    Args:
        schedule_id: Identifiant du schedule à désactiver (ex: 'wl0').
    """
    return await _post("/scheduler/disable", {**DEFAULT_TELNET_CONFIG, "schedule_id": schedule_id, "enable": False})


# ═══════════════════════════════════════════════
#  IPTV
# ═══════════════════════════════════════════════

@mcp.tool()
async def iptv_status_normal() -> dict[str, Any]:
    """Retourne le statut du service IPTV (vue normale)."""
    return await _post("/IPTV/status", params={"role": "normal"})

@mcp.tool()
async def iptv_status_technical() -> dict[str, Any]:
    """Retourne le statut complet du service IPTV (vue technique) : firewall, ATM, VLAN."""
    return await _post("/IPTV/status", params={"role": "technical"})


# ═══════════════════════════════════════════════
#  DHCP
# ═══════════════════════════════════════════════

@mcp.tool()
async def dhcp_status_normal() -> dict[str, Any]:
    """Retourne le statut du serveur DHCP (vue normale) : Enable et State."""
    return await _post("/dhcp/status", params={"role": "normal"})

@mcp.tool()
async def dhcp_status_technical() -> dict[str, Any]:
    """Retourne le statut complet du serveur DHCP (vue technique) : pool, baux, adresses."""
    return await _post("/dhcp/status", params={"role": "technical"})


# ═══════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()