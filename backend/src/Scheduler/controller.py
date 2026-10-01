from fastapi import APIRouter
from .models import ScheduleRequest
from .service import add_wlan_schedule ,enable_wlan_schedule
from .models import Requestenable, Requestdisable

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

@router.post("/add")
async def scheduler_add(req: ScheduleRequest):
    """
    Crée un schedule WLAN avec jour/heure/minute dynamiques.
    """
    result = await add_wlan_schedule(
        host=req.host,
        port=req.port,
        user=req.user,
        password=req.password,
        begin_day=req.begin_day,
        begin_hour=req.begin_hour,
        begin_minute=req.begin_minute,
        end_day=req.end_day,
        end_hour=req.end_hour,
        end_minute=req.end_minute,
        schedule_id=req.schedule_id
    )
    return result






@router.post("/enable")
async def scheduler_enable(req: Requestenable):
    """
    Active ou désactive un schedule WLAN.
    """
    result = await enable_wlan_schedule(
        host=req.host,
        port=req.port,
        user=req.user,
        password=req.password,
        schedule_id=req.schedule_id,
        enable=req.enable,
    )
    return result


@router.post("/disable")
async def scheduler_disable(req: Requestdisable):      
    """
    Désactive un schedule WLAN.
    """
    result = await enable_wlan_schedule(
        host=req.host,
        port=req.port,
        user=req.user,
        password=req.password,
        schedule_id=req.schedule_id,
        enable=req.enable,
    )
    return result
