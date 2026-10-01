import asyncio
import telnetlib3
import logging

logger = logging.getLogger(__name__)

def safe_decode(data):
    """Convertit les bytes en string de manière sécurisée"""
    if isinstance(data, bytes):
        return data.decode('utf-8', errors='ignore')
    return str(data)

def nettoyer_output(cmd: str, output: str) -> str:
    """
    Supprime les lignes parasites (login, password, pcb_cli, prompt, etc.)
    et garde uniquement le résultat utile de la commande.
    """
    lignes = output.splitlines()
    lignes_filtrees = []
    for l in lignes:
        # ignorer les lignes qui contiennent login, password, pcb_cli ou prompt
        if any(x in l.lower() for x in [
            "login", "password", "pcb_cli", "/cfg/system/root",
            "copyright", "connected to pcb"
        ]):
            continue
        # ignorer l'echo de la commande
        if cmd in l:
            continue
        lignes_filtrees.append(l.strip())
    return "\n".join(lignes_filtrees).strip()

async def send_commands(host: str, port: int, user: str, password: str, commands: list) -> dict:
    results = []
    try:
        reader, writer = await asyncio.wait_for(
            telnetlib3.open_connection(host, port),
            timeout=10
        )
        await asyncio.sleep(1)

        # login
        writer.write(user + "\r\n")
        await asyncio.sleep(0.8)
        writer.write(password + "\r\n")
        await asyncio.sleep(0.8)

        # entrer pcb_cli
        writer.write("pcb_cli\r\n")
        await asyncio.sleep(1)

        # exécuter les commandes
        for cmd in commands:
            try:
                writer.write(cmd + "\r\n")
                await asyncio.sleep(0.8)
                
                try:
                    output = await asyncio.wait_for(reader.read(4096), timeout=3)
                    output_str = safe_decode(output).strip()
                    
                    final_output = nettoyer_output(cmd, output_str)
                    
                    results.append({
                        "command": cmd,
                        "status": "success",
                        "output": final_output
                    })
                except asyncio.TimeoutError:
                    results.append({
                        "command": cmd,
                        "status": "timeout",
                        "output": "Timeout lors de l'exécution"
                    })
            except Exception as e:
                results.append({
                    "command": cmd,
                    "status": "error",
                    "output": str(e)
                })

        writer.write("exit\r\n")
        writer.close()
        
        # Retourne uniquement les résultats
        return {"results": results}
        
    except Exception as e:
        return {
            "results": [{
                "command": None,
                "status": "error",
                "output": str(e)
            }]
        }
