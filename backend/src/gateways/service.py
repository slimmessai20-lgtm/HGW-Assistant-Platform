from src.auth.db import get_connection
from src.gateways.models import GatewayCreate, GatewayUpdate
from src.gateways.crypto import encrypt_password, decrypt_password


def get_all(user_id: int = None, role: str = None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if role == "user" and user_id:
                cur.execute(
                    "SELECT * FROM gateways WHERE created_by = %s ORDER BY created_at DESC",
                    (user_id,)
                )
            else:
                cur.execute("SELECT * FROM gateways ORDER BY created_at DESC")
            rows = cur.fetchall()
            for row in rows:
                if row.get("telnet_password"):
                    row["telnet_password"] = decrypt_password(row["telnet_password"])
            return rows
    finally:
        conn.close()


def get_by_id(gw_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM gateways WHERE id = %s", (gw_id,))
            row = cur.fetchone()
            if row and row.get("telnet_password"):
                row["telnet_password"] = decrypt_password(row["telnet_password"])
            return row
    finally:
        conn.close()


def create(data: GatewayCreate, created_by: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO gateways
                   (name, brand, surname, mac_address, ipv4_address, ipv6_address,
                    telnet_host, telnet_port, telnet_user, telnet_password,
                    software_version, serial_number, base_mac, status, notes, created_by)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (data.name, data.brand, data.surname, data.mac_address,
                 data.ipv4_address, data.ipv6_address,
                 data.telnet_host, data.telnet_port, data.telnet_user, encrypt_password(data.telnet_password),
                 data.software_version, data.serial_number, data.base_mac,
                 data.status, data.notes, created_by)
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def update(gw_id: int, data: GatewayUpdate):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE gateways SET
                   name=%s, brand=%s, surname=%s, mac_address=%s,
                   ipv4_address=%s, ipv6_address=%s,
                   telnet_host=%s, telnet_port=%s, telnet_user=%s, telnet_password=%s,
                   software_version=%s, serial_number=%s, base_mac=%s,
                   status=%s, notes=%s
                   WHERE id=%s""",
                (data.name, data.brand, data.surname, data.mac_address,
                 data.ipv4_address, data.ipv6_address,
                 data.telnet_host, data.telnet_port, data.telnet_user, encrypt_password(data.telnet_password),
                 data.software_version, data.serial_number, data.base_mac,
                 data.status, data.notes, gw_id)
            )
            conn.commit()
    finally:
        conn.close()


def update_device_info(gw_id: int, serial_number: str = None, base_mac: str = None, software_version: str = None, ipv4_address: str = None, ipv6_address: str = None, mac_address: str = None):
    """Met à jour les champs récupérés via Auto-fetch."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE gateways SET
                   serial_number = COALESCE(%s, serial_number),
                   base_mac      = COALESCE(%s, base_mac),
                   software_version = COALESCE(%s, software_version),
                   ipv4_address  = COALESCE(%s, ipv4_address),
                   ipv6_address  = COALESCE(%s, ipv6_address),
                   mac_address   = COALESCE(%s, mac_address)
                   WHERE id = %s""",
                (serial_number, base_mac, software_version, ipv4_address, ipv6_address, mac_address, gw_id)
            )
            conn.commit()
    finally:
        conn.close()


def delete(gw_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM gateways WHERE id = %s", (gw_id,))
            conn.commit()
    finally:
        conn.close()
