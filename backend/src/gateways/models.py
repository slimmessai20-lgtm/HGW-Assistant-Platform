from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GatewayCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    surname: Optional[str] = None
    mac_address: Optional[str] = None
    ipv4_address: Optional[str] = None
    ipv6_address: Optional[str] = None
    telnet_host: Optional[str] = None
    telnet_port: Optional[int] = 23
    telnet_user: Optional[str] = None
    telnet_password: Optional[str] = None
    software_version: Optional[str] = None
    serial_number: Optional[str] = None
    base_mac: Optional[str] = None
    status: Optional[str] = "unknown"
    notes: Optional[str] = None


class GatewayUpdate(GatewayCreate):
    pass


class GatewayOut(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    surname: Optional[str]
    mac_address: Optional[str]
    ipv4_address: Optional[str]
    ipv6_address: Optional[str]
    telnet_host: Optional[str]
    telnet_port: Optional[int]
    telnet_user: Optional[str]
    software_version: Optional[str]
    serial_number: Optional[str]
    base_mac: Optional[str]
    status: str
    notes: Optional[str]
    created_by: Optional[int]
    created_at: Optional[datetime]
