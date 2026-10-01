"""Central configuration — loads .env once for the whole app."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── JWT ───────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in .env — server refused to start.")
ALGORITHM          = os.environ.get("ALGORITHM", "HS256")
TOKEN_EXPIRE_HOURS = int(os.environ.get("TOKEN_EXPIRE_HOURS", "8"))

# ── Groq LLM ─────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_BASE    = "https://api.groq.com/openai/v1"

# ── MCP Server ────────────────────────────────────────────────────────────────
MCP_SCRIPT = os.environ.get("MCP_SERVER_PATH", r"C:\Users\slimm\Desktop\MCP\mcpserver\main.py")
# MCP_DIR can be set explicitly (needed in Docker where pyproject.toml lives one level above main.py)
MCP_DIR    = os.environ.get("MCP_DIR", os.path.dirname(MCP_SCRIPT))

# ── SMTP (Emails) ─────────────────────────────────────────────────────────────
SMTP_SERVER   = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER     = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
