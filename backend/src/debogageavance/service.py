
from typing import List, Dict
from src.cnxtelnet.service1 import send_commands


class FaultMonitor:
    @staticmethod
    async def listFaults(host: str, port: int, user: str, password: str) -> Dict:
        """Execute the Telnet command `FaultMonitor.listFaults()` on the device.

        Returns the raw result from `send_commands`.
        """
        cmd = ["FaultMonitor.listFaults()"]
        result = await send_commands(host, port, user, password, cmd)
        return result
    async def listoops(host: str, port: int, user: str, password: str) -> Dict:
        """Execute the Telnet command `FaultMonitor.listoops()` on the device.

        Returns the raw result from `send_commands`.
        """
        cmd = ["OopsTracker.getOopses()"]
        result = await send_commands(host, port, user, password, cmd)
        return result


class Debug:
    @staticmethod
    async def verifyPlugins(host: str, port: int, user: str, password: str) -> Dict:
        """Execute the Telnet command `Debug.verifyPlugins()` on the device.

        Returns the raw result from `send_commands`. Parsing can be added later.
        """
        cmd = ["Debug.verifyPlugins()"]
        result = await send_commands(host, port, user, password, cmd)
        return result
    

    async def listMQTT(host: str, port: int, user: str, password: str) -> Dict:   
        """Execute the Telnet command .

        Returns the raw result from `send_commands`. Parsing can be added later.
        """
        cmd = ["MQTT?"]
        result = await send_commands(host, port, user, password, cmd)
        return result
    




async def get_modem_status(host: str, port: int, user: str, password: str, role: str):
    if role.lower() == "normal":
        # Exécuter les commandes nécessaires pour un utilisateur normal
        commands = [
            "Devices.Device.HGW.Active?",
            "Devices.Device.HGW.Name?",
            "Devices.Device.HGW.LastConnection?",
            "Devices.Device.HGW.LastChanged?"
        ]
        raw = await send_commands(host, port, user, password, commands)

        return {
            "status": "success",
            "modem": {
                "Active": raw["results"][0]["output"].strip(),
                "Name": raw["results"][1]["output"].strip(),
                "LastConnection": raw["results"][2]["output"].strip(),
                "LastChanged": raw["results"][3]["output"].strip()
            }
        }

    elif role.lower() == "technical":
        # Exécuter les commandes nécessaires pour un utilisateur technique
        commands = [
            "Devices.Device.HGW.Active?",
            "FaultMonitor.listFaults()",
            "OopsTracker.getOopses()",
            "Debug.verifyPlugins()",
            "Devices.Device.lan.?"
        ]
        raw = await send_commands(host, port, user, password, commands)

        return {
            "status": "success",
            "modem": {
                "Active": raw["results"][0]["output"].strip(),
                "Faults": raw["results"][1]["output"].strip(),
                "Oopses": raw["results"][2]["output"].strip(),
                "Plugins": raw["results"][3]["output"].strip(),
                "LAN": raw["results"][4]["output"].strip()
            }
        }

    else:
        return {"status": "error", "message": "Invalid role"}
    






async def ping_dns(host: str, port: int, user: str, password: str, role: str):
    if role.lower() == "normal":
        # Exécuter les commandes nécessaires pour un utilisateur normal
        commands = [
            "IPPingDiagnostics.Host?",
            "Device.IP.Diagnostics.IPPing.Host?",
            "DNS.?"
        ]
        raw = await send_commands(host, port, user, password, commands)

        return raw

    elif role.lower() == "technical":
        # Exécuter les commandes nécessaires pour un utilisateur technique
        commands = [
            "IPPingDiagnostics.Host?",
            "Device.IP.Diagnostics.IPPing.Host?",
            "DNS.?",
            "Firewall.Config?"
        ]
        raw = await send_commands(host, port, user, password, commands)

        return raw
           
           

    else:
        return {"status": "error", "message": "Invalid role"}
    
