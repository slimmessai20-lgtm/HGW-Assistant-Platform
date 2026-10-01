from ..cnxtelnet.service1 import send_commands

# Fields to always include even when empty
_ALWAYS_SHOW = {"LinkState", "LinkType", "ConnectionState", "Protocol"}


async def get_wan_status(host: str, port: int, user: str, password: str, role: str) -> dict:
    raw = await send_commands(host, port, user, password, ["NMC.getWANStatus()"])
    output = raw["results"][0].get("output", "") if raw.get("results") else ""

    fields: dict[str, str] = {}
    if "(" in output and ")" in output:
        inside = output.split("(", 1)[1].rsplit(")", 1)[0]
        for part in inside.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                key = k.strip()
                val = v.strip()
                # Last value wins — deduplicate naturally
                if key not in fields:  # keep first occurrence only
                    fields[key] = val if val not in ("", "null", "None") else "—"

    if role.lower() == "normal":
        return {"status": "success", "LinkState": fields.get("LinkState", "—")}

    # For technical role: show all fields that have a real value,
    # plus the always-show fields even if empty
    result = {}
    for k, v in fields.items():
        if v != "—" or k in _ALWAYS_SHOW:
            result[k] = v
    return {"status": "success", **result}
