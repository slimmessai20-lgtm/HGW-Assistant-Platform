
from pydantic import BaseModel


class ScheduleRequest(BaseModel):
    begin_day: int
    begin_hour: int
    begin_minute: int = 0
    end_day: int
    end_hour: int
    end_minute: int = 0
    schedule_id: str = "wl0"
    host: str
    port: int
    user: str
    password: str

class Requestenable(BaseModel):
    schedule_id: str = "wl0"
    enable: bool = True
    host: str
    port: int = 23
    user: str
    password: str

class Requestdisable(BaseModel):
    schedule_id: str = "wl0"
    enable: bool = False
    host: str
    port: int = 23
    user: str
    password: str