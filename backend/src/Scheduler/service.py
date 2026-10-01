from ..cnxtelnet.service import send_commands

def convert_to_seconds(day: int, hour: int, minute: int = 0) -> int:
    """Convertit jour+heure+minute en secondes depuis début semaine."""
    seconds_per_day = 24 * 3600
    return day * seconds_per_day + hour * 3600 + minute * 60

async def add_wlan_schedule(
    host: str,
    port: int,
    user: str,
    password: str,
    begin_day: int,
    begin_hour: int,
    begin_minute: int,
    end_day: int,
    end_hour: int,
    end_minute: int,
    schedule_id: str = "wl0"
) -> dict:
    begin = convert_to_seconds(begin_day, begin_hour, begin_minute)
    end = convert_to_seconds(end_day, end_hour, end_minute)

    command = (
        f'Scheduler.addSchedule(type:"WLAN", '
        f'info:{{base:"Weekly", def:"Enable", ID:"{schedule_id}", '
        f'schedule:[{{state:"Disable", begin:{begin}, end:{end}}}], '
        f'enable:true, override:""}})'
    )
    raw = await send_commands(host, port, user, password, [command])
    return {"command": command, "raw": raw}




async def enable_wlan_schedule(host: str, port: int, user: str, password: str,
                               schedule_id: str = "wl0", enable: bool = False) -> dict:
    """
    Active ou désactive un schedule WLAN.
    """
    command = (
        f'Scheduler.enableSchedule(type:"WLAN", ID:"{schedule_id}", enable:{str(enable).lower()})'
    )

    raw = await send_commands(host, port, user, password, [command])
    return {
        "command": command,
        "raw": raw
    }
