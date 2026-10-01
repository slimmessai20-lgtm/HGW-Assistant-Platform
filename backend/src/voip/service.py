from ..cnxtelnet.service1 import send_commands


def _yn(v: str) -> str:
    return "Yes" if v in ("1", "true", "True", "enabled", "Ready") else (
           "No"  if v in ("0", "false", "False", "disabled") else v)


def _kv(output: str) -> dict:
    fields = {}
    for line in output.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            fields[k.strip()] = v.strip()
    return fields


async def get_voip_status(host: str, port: int, user: str, password: str, role: str):
    if role.lower() == "normal":
        commands = [
            "Process.sysbus_voipapp.Status?",
            "Process.sysbus_voipapp.Registered?",
            "NeMo.Intf.voip.Status?",
            "Firewall.Policy.Voip2Lan.Status?",
            "Firewall.Policy.Voip2Lan.Enable?",
        ]
        raw = await send_commands(host, port, user, password, commands)
        f = {}
        for r in raw.get("results", []):
            f.update(_kv(r.get("output", "")))

        return {
            "VoIP Service":       f.get("Process.sysbus_voipapp.Status", "?"),
            "Registered":         _yn(f.get("Process.sysbus_voipapp.Registered", "?")),
            "VoIP Interface":     f.get("NeMo.Intf.voip.Status", "?"),
            "Firewall Policy":    f.get("Firewall.Policy.Voip2Lan.Status", "?"),
            "Firewall Enabled":   _yn(f.get("Firewall.Policy.Voip2Lan.Enable", "?")),
        }

    elif role.lower() == "technical":
        commands = [
            "Process.sysbus_voipapp.Status?",
            "Process.sysbus_voipapp.Registered?",
            "Process.sysbus_voipapp.PID?",
            "Process.sysbus_voipapp.Type?",
            "Process.sysbus_voipapp.Connection?",
            "NeMo.Intf.voip.Status?",
            "Firewall.Policy.Voip2Lan.Status?",
            "Firewall.Policy.Voip2Lan.Enable?",
            "Firewall.Policy.Voip2Lan.SourceInterface?",
            "Firewall.Policy.Voip2Lan.DestinationInterface?",
            "QueueManagement.Classification.VoipRtp.Enable?",
            "QueueManagement.Classification.VoipSign.Enable?",
        ]
        raw = await send_commands(host, port, user, password, commands)
        f = {}
        for r in raw.get("results", []):
            f.update(_kv(r.get("output", "")))

        def g(k): return f.get(k, "?")

        result = {
            "VoIP Service":            g("Process.sysbus_voipapp.Status"),
            "Registered":              _yn(g("Process.sysbus_voipapp.Registered")),
            "PID":                     g("Process.sysbus_voipapp.PID"),
            "Process Type":            g("Process.sysbus_voipapp.Type"),
            "Connection":              g("Process.sysbus_voipapp.Connection"),
            "VoIP Interface":          g("NeMo.Intf.voip.Status"),
            "Firewall Policy Status":  g("Firewall.Policy.Voip2Lan.Status"),
            "Firewall Policy Enabled": _yn(g("Firewall.Policy.Voip2Lan.Enable")),
            "Source Interface":        g("Firewall.Policy.Voip2Lan.SourceInterface"),
            "Dest Interface":          g("Firewall.Policy.Voip2Lan.DestinationInterface"),
        }
        # QoS only if returned
        rtp  = _yn(g("QueueManagement.Classification.VoipRtp.Enable"))
        sign = _yn(g("QueueManagement.Classification.VoipSign.Enable"))
        if rtp  != "?": result["QoS RTP"]          = rtp
        if sign != "?": result["QoS Signaling"]     = sign
        return result

    return {"error": "Invalid role"}
