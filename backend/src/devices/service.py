from ..cnxtelnet.service1 import send_commands
import re


def parse_devices_output(output_text: str):
    devices = []
    raw_blocks = re.split(r"\},\s*\{", output_text.strip()[1:-1])
    for block in raw_blocks:
        device = {}
        for line in block.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip(",")
                if key == "Name" and val in ["name", "source", "Edit Name", "Edit Type", "Device"]:
                    continue
                device[key] = val
        if "DiscoverySource" in device and "Name" in device and "DeviceType" in device:
            devices.append(device)
    return devices


async def get_connected_devices(host: str, port: int, user: str, password: str, role: str) -> dict:
    command = 'Devices.get(expression:"not interface and not self and not voice and .Active==true", flags:"full_links")'
    raw = await send_commands(host, port, user, password, [command])
    output_text = raw["results"][0].get("output", "")

    parsed_devices = parse_devices_output(output_text)
    devices = []

    for d in parsed_devices:
        if d.get("Active") != "1":
            continue

        if role.lower() == "normal":
            devices.append({
                "Device Name":    d.get("Name"),
                "DeviceType":     d.get("DeviceType"),
                "DiscoverySource":d.get("DiscoverySource"),
                "Active":         1
            })
        elif role.lower() == "technical":
            devices.append({
                "Device Name":    d.get("Name"),
                "MAC":            d.get("PhysAddress"),
                "IPv4":           d.get("IPAddress"),
                "IPv6":           d.get("IPv6Address") or None,
                "Interface":      d.get("Layer2Interface") or d.get("InterfaceName"),
                "FirstSeen":      d.get("FirstSeen"),
                "LastConnection": d.get("LastConnection"),
            })

    return {"status": "success", "devices": devices}


from src.cnxtelnet.service import send_commands as _send_v2

async def get_hgw_info(host: str, port: int, user: str, password: str) -> dict:
    command = "Devices.Device.HGW?"
    try:
        raw = await _send_v2(host, port, user, password, [command])
        return raw
    except Exception as e:
        return {"status": "error", "error": str(e)}
