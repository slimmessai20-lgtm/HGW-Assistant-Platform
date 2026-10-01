from pydantic import BaseModel



class TelnetRequestrole(BaseModel):
    host: str
    port: int
    user: str
    password: str
    role: str

