# MCP Server — Home Gateway Management

> Serveur MCP (Model Context Protocol) pour le contrôle des passerelles domestiques via Telnet.  
> Utilisé par le backend FastAPI comme **subprocess stdio** — non démarré manuellement.

## Rôle dans l'architecture

Le MCP server n'est **pas un service HTTP persistant**. Il est lancé à la demande par le backend FastAPI pour chaque requête chat :

```
FastAPI (chat/router.py)
    │
    └── subprocess stdio ──► uv run mcpserver/main.py
                                     │
                            48 outils HGW disponibles
                                     │
                            HTTP GET/POST ──► FastAPI HGW endpoints
                                                      │
                                             Telnet ──► HGW physique
```

Les credentials Telnet (host, port, user, password) sont injectés via des **variables d'environnement** au moment du lancement du subprocess.

## Structure

```
MCP/
├── Dockerfile          # Image standalone (référence / déploiement futur)
├── pyproject.toml      # Config uv + dépendances
├── uv.lock
└── mcpserver/
    ├── __init__.py     # DEFAULT_TELNET_CONFIG
    ├── main.py         # Point d'entrée FastMCP (48 outils déclarés)
    ├── wifi.py
    ├── DHCP.py
    ├── Firewall.py
    ├── Guestwifi.py
    ├── IPTV.py
    ├── Voip.py
    ├── Wan.py
    ├── devices.py
    ├── Scheduler.py
    ├── Telnet.py
    └── Debogageavance.py
```

## Outils disponibles (48)

| Domaine | Outils |
|---|---|
| Wi-Fi | on, off, status, set_ssid, set_password, get_password, reboot, factory_reset, speedtest, extra_2g_on/off, extra_5g_on/off |
| Wi-Fi invité | 2g_on/off, 5g_on/off, status, set_ssid, set_password |
| Appareils | list_normal, list_technical, hgw_info |
| WAN | status_normal, status_technical |
| Firewall | ping_enable/disable, set_level, status_normal/technical |
| DHCP | status_normal, status_technical |
| VoIP | status_normal, status_technical |
| IPTV | status_normal, status_technical |
| Scheduler | add, enable, disable |
| Débogage | list_faults, list_oopses, verify_plugins, mqtt_status, modem_status_normal/technical, access_normal/technical |
| Telnet brut | execute |

## Prérequis

- Python 3.12+ (ou 3.14+ selon `.python-version`)
- [`uv`](https://astral.sh/uv) installé

## Installation

```bash
cd MCP

# Créer l'environnement et installer les dépendances
uv sync

# Vérifier que le serveur démarre (test manuel)
uv run mcp run mcpserver/main.py
# Ctrl+C pour arrêter
```

## Configuration dans le backend (`.env`)

```env
# Chemin vers le script principal du MCP server
MCP_SERVER_PATH=C:\Users\slimm\Desktop\MCP\mcpserver\main.py

# Dossier racine du MCP (contient pyproject.toml) — nécessaire pour uv run
MCP_DIR=C:\Users\slimm\Desktop\MCP
```

Sur Linux/macOS :
```env
MCP_SERVER_PATH=/home/user/MCP/mcpserver/main.py
MCP_DIR=/home/user/MCP
```

## Variables d'environnement injectées par le backend

Au moment du lancement du subprocess, le backend injecte :

| Variable | Description |
|---|---|
| `HGW_HOST` | IP Telnet de la passerelle (ex: `192.168.2.254`) |
| `HGW_PORT` | Port Telnet (défaut `23`) |
| `HGW_USER` | Utilisateur Telnet (défaut `root`) |
| `HGW_PASSWORD` | Mot de passe Telnet (défaut `sah`) |

Ces valeurs proviennent de la table `gateways` en base de données, sélectionnée par `gateway_id` dans la requête chat.

## Note sur l'environnement sans HGW physique

Si aucun Home Gateway physique n'est disponible (dev, CI), les outils MCP retourneront une erreur de connexion Telnet. Cela **n'empêche pas** le reste de l'application de fonctionner — seules les réponses du chatbot seront dégradées (l'IA recevra une erreur au lieu de données réelles).

Pour les **tests unitaires**, le MCP server n'est jamais lancé — toute la logique est mockée dans `conftest.py`.

## Docker

Le Dockerfile dans ce dossier sert de **référence** pour un éventuel déploiement standalone du MCP en mode HTTP. Dans le `docker-compose.yml`, le code MCP est directement copié dans l'image du backend FastAPI — pas de container MCP séparé.
