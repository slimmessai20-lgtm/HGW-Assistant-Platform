
from pydantic import BaseModel

class TelnetSSIDRequest(BaseModel):
    host: str
    port: int = 23
    user: str
    password: str
    ssid: str


class TelnetKeyRequest(BaseModel):
    host: str
    port: int = 23
    user: str
    password: str
    keypassphrase: str
