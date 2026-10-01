from fastapi import APIRouter, HTTPException, Depends
from src.auth.router import get_current_user
from src.gateways.models import GatewayCreate, GatewayUpdate, GatewayOut
from src.gateways import service
from typing import List
import socket
import asyncio
import time

router = APIRouter(prefix="/gateways", tags=["gateways"])


@router.get("/resolve-surname")
def resolve_surname(ipv4: str, _: dict = Depends(get_current_user)):
    """Auto-fill surname from IPv4 via reverse DNS."""
    try:
        hostname = socket.gethostbyaddr(ipv4)[0]
    except Exception:
        hostname = f"HGW-{ipv4.replace('.', '-')}"
    return {"surname": hostname}


@router.get("", response_model=List[GatewayOut])
def list_gateways(current_user: dict = Depends(get_current_user)):
    return service.get_all(
        user_id=int(current_user["sub"]),
        role=current_user["role"]
    )


@router.get("/{gw_id}", response_model=GatewayOut)
def get_gateway(gw_id: int, current_user: dict = Depends(get_current_user)):
    gw = service.get_by_id(gw_id)
    if not gw:
        raise HTTPException(status_code=404, detail="Entrée introuvable")
    return gw


@router.post("", response_model=dict)
def create_gateway(data: GatewayCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("admin", "engineer"):
        raise HTTPException(status_code=403, detail="Accès refusé")
    try:
        new_id = service.create(data, created_by=int(current_user["sub"]))
        return {"id": new_id, "message": "Entrée créée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{gw_id}")
def update_gateway(gw_id: int, data: GatewayUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("admin", "engineer"):
        raise HTTPException(status_code=403, detail="Accès refusé")
    if not service.get_by_id(gw_id):
        raise HTTPException(status_code=404, detail="Entrée introuvable")
    service.update(gw_id, data)
    return {"message": "Entrée mise à jour"}


@router.get("/{gw_id}/ping")
async def ping_gateway(gw_id: int, _: dict = Depends(get_current_user)):
    """TCP ping (port 23) to measure gateway latency."""
    gw = service.get_by_id(gw_id)
    if not gw:
        raise HTTPException(status_code=404, detail="Entrée introuvable")
    host = gw.get("telnet_host") or gw.get("ipv4_address")
    port = gw.get("telnet_port") or 23
    if not host:
        return {"status": "unknown", "latency_ms": None, "error": "No host configured"}
    start = time.time()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=5.0
        )
        writer.close()
        await writer.wait_closed()
        latency = round((time.time() - start) * 1000, 1)
        return {"status": "reachable", "latency_ms": latency, "host": host}
    except asyncio.TimeoutError:
        return {"status": "timeout", "latency_ms": None, "host": host}
    except Exception as e:
        return {"status": "unreachable", "latency_ms": None, "host": host, "error": str(e)}


@router.post("/{gw_id}/fetch-device-info")
async def fetch_device_info(gw_id: int, current_user: dict = Depends(get_current_user)):
    """
    Se connecte au HGW via Telnet, exécute DeviceInfo.get() et IP.get() (ou similaire)
    pour récupérer la version, IPv4, IPv6, SerialNumber et BaseMAC.
    """
    if current_user["role"] not in ("admin", "engineer"):
        raise HTTPException(status_code=403, detail="Accès refusé")

    gw = service.get_by_id(gw_id)
    if not gw:
        raise HTTPException(status_code=404, detail="Entrée introuvable")

    host     = gw.get("telnet_host") or gw.get("ipv4_address")
    port     = gw.get("telnet_port") or 23
    user     = gw.get("telnet_user") or "root"
    password = gw.get("telnet_password") or "sah"

    if not host:
        raise HTTPException(status_code=400, detail="Aucun host Telnet configuré pour ce gateway")

    from src.cnxtelnet.service import send_commands
    # DeviceInfo.get() donne Serial, BaseMAC, SoftwareVersion, ExternalIPAddress
    # On ajoute aussi IP.Interface.1.IPv6Address.1.IPAddress? au cas où
    result = await send_commands(
        host=host, port=port, user=user, password=password,
        commands=["DeviceInfo.get()", "IP.Interface.1.IPv6Address.1.IPAddress?"]
    )

    serial_number = None
    base_mac      = None
    software_version = None
    ipv4_address  = None
    ipv6_address  = None
    mac_address   = None

    for item in result.get("results", []):
        output = item.get("output", "")
        for line in output.splitlines():
            line = line.strip()
            # Nettoyage pour les résultats de get() qui ont des espaces et deux points ex: "SerialNumber : N724..."
            if ":" in line:
                key, val = [part.strip() for part in line.split(":", 1)]
                if key == "SerialNumber":
                    serial_number = val.strip(",")
                elif key == "BaseMAC":
                    base_mac = val.strip(",")
                elif key == "SoftwareVersion":
                    software_version = val.strip(",")
                elif key == "ExternalIPAddress":
                    ipv4_address = val.strip(",")
            # Pour les commandes avec ? qui retournent "Clé=Valeur"
            if "=" in line:
                key, val = [part.strip() for part in line.split("=", 1)]
                if "IPv6Address" in key and "IPAddress=" in line:
                    ipv6_address = val
                elif "SerialNumber=" in line:
                    serial_number = val
                elif "BaseMAC=" in line:
                    base_mac = val
                elif "SoftwareVersion=" in line:
                    software_version = val

    if not serial_number and not base_mac and not software_version:
        raise HTTPException(
            status_code=502,
            detail="Impossible de récupérer les valeurs depuis le HGW. Vérifiez la connexion Telnet."
        )

    # Si mac_address actuel est vide (ou factice), on le remplit avec BaseMAC
    current_mac = gw.get("mac_address", "")
    if not current_mac or current_mac == "00:00:00:00:00:00":
        mac_address = base_mac

    # Sauvegarder en base
    service.update_device_info(
        gw_id,
        serial_number=serial_number,
        base_mac=base_mac,
        software_version=software_version,
        ipv4_address=ipv4_address,
        ipv6_address=ipv6_address,
        mac_address=mac_address
    )

    return {
        "serial_number": serial_number,
        "base_mac":      base_mac,
        "software_version": software_version,
        "ipv4_address": ipv4_address,
        "ipv6_address": ipv6_address,
        "mac_address": mac_address,
        "message":       "Valeurs récupérées et sauvegardées avec succès"
    }


@router.delete("/{gw_id}")
def delete_gateway(gw_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    if not service.get_by_id(gw_id):
        raise HTTPException(status_code=404, detail="Entrée introuvable")
    service.delete(gw_id)
    return {"message": "Entrée supprimée"}
