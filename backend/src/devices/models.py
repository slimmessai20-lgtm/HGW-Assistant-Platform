from pydantic import BaseModel


class DevicesRequest(BaseModel):
    host: str
    port: int = 23
    user: str
    password: str