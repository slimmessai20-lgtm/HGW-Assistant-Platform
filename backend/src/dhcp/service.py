from ..cnxtelnet.service import send_commands

async def get_dhcp_status(host: str, port: int, user: str, password: str, role: str = "normal") -> dict:
    if role.lower() == "normal":
        # Commandes pour un utilisateur normal
        commands = [
            "DHCPv4.Server.Enable?",
            "DHCPv4.Server.Stats.State?"
        ]
    else:
        # Commandes pour un utilisateur technique
        commands = [
            "DHCPv4.Server.Enable?",
            "DHCPv4.Server.Stats.State?",
            "DHCPv4.Server.Pool.default.Enable?",
            "DHCPv4.Server.Pool.default.MinAddress?",
            "DHCPv4.Server.Pool.default.MaxAddress?",
            "DHCPv4.Server.Pool.default.LeaseTime?",
            "DHCPv4.Server.Pool.default.LeaseNumberOfEntries?"
        ]

    raw = await send_commands(host, port, user, password, commands)

    # Construire la réponse
    results = {}
    for idx, cmd in enumerate(commands):
        results[cmd] = raw["results"][idx]["output"].strip()

    return {"status": "success", "dhcp": results}
