import asyncio
import re
import telnetlib3
import logging

logger = logging.getLogger(__name__)

_ANSI_RE   = re.compile(r'\x1b\[[0-9;]*[A-Za-z]|\x1b[()][A-Z0-9]|\r')
_PROMPT_RE = re.compile(r'^(>\s*)+')   # strips leftover "> " prompt echoes


def safe_decode(data):
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="ignore")
    return str(data)


def clean_line(line: str) -> str:
    """Strip ANSI escape codes and leading shell-prompt echoes."""
    return _PROMPT_RE.sub('', _ANSI_RE.sub('', line))


async def read_until(reader, expected_list, timeout=5):
    """
    Lit jusqu'à trouver un des éléments dans expected_list.
    """
    buffer = ""
    try:
        while True:
            chunk = await asyncio.wait_for(reader.read(1024), timeout=timeout)
            if not chunk:
                break
            buffer += safe_decode(chunk)

            for expected in expected_list:
                if expected.lower() in buffer.lower():
                    return buffer

    except asyncio.TimeoutError:
        pass

    return buffer


async def send_commands(host: str, port: int, user: str, password: str, commands: list) -> dict:
    results = []
    debug_logs = []

    try:
        # Connexion
        reader, writer = await asyncio.wait_for(
            telnetlib3.open_connection(host, port),
            timeout=8
        )

        debug_logs.append(f"Connecté à {host}:{port}")

        # ---- LOGIN FLOW CORRECT ----

        # Attendre login prompt
        login_response = await read_until(reader, ["login:"], timeout=5)

        if "login" not in login_response.lower():
            return {
                "status": "error",
                "error": "Login prompt non détecté",
                "debug": login_response
            }

        writer.write(user + "\r\n")

        # Attendre password prompt
        password_response = await read_until(reader, ["assword"], timeout=5)

        writer.write(password + "\r\n")

        # Attendre prompt final après login (>, # ou autre)
        auth_response = await read_until(reader, [">", "#"], timeout=5)

        if "incorrect" in auth_response.lower():
            return {
                "status": "error",
                "error": "Authentification échouée",
                "debug": auth_response
            }

        # ---- ENTRER DANS PCB_CLI ----
        writer.write("pcb_cli\r\n")

        await read_until(reader, ["pcb_cli>"], timeout=5)

        # ---- EXECUTION COMMANDES ----
        for cmd in commands:

            writer.write(cmd + "\r\n")

            output = await read_until(reader, ["pcb_cli>"], timeout=5)

            lines = [clean_line(line) for line in output.splitlines()]

            clean_lines = [
                line for line in lines
                if line.strip()
                and cmd not in line
                and "pcb_cli>" not in line
            ]

            final_output = "\n".join(clean_lines).strip()

            results.append({
                "command": cmd,
                "status": "success" if final_output else "empty",
                "output": final_output
            })

        writer.write("exit\r\n")
        writer.close()

        return {
            "status": "success",
            "host": host,
            "results": results
        }

    except asyncio.TimeoutError:
        return {
            "status": "error",
            "error": f"Timeout connexion {host}:{port}"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }