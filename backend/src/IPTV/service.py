from ..cnxtelnet.service import send_commands

async def get_iptv_status(host: str, port: int, user: str, password: str, role: str):
    if role.lower() == "normal":
        commands = [
            "NeMo.Intf.iptv.Status?",
            "Firewall.Policy.IPTV2Lan.Status?"
        ]
        return await send_commands(host, port, user, password, commands)

    elif role.lower() == "technical":
        commands = [
            "Firewall.Chain.IPTV_In? ",
            "Firewall.Chain.IPTV_Out?",
            "Firewall.Policy.IPTV2Lan?",
            "NeMo.Intf.atm_iptv?",
            "NeMo.Intf.vvlan_iptv?"


        ]
        return await send_commands(host, port, user, password, commands)

    else:
        return {"status": "error", "message": "Invalid role"}
