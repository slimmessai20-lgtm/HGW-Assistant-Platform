from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from src.wifi.controller import router as wifi_router
from src.cnxtelnet.controller import router as telnet_router
from src.guestwifi.controller import router as guestwifi_router
from src.debogageavance.controller import router as debogageavance_router
from src.Scheduler.controller import router as scheduler_router
from src.devices.controller import router as devices_router
from src.firewall.controller import router as firewall_router
from src.wan.controller import router as wan_router
from src.voip.controller import router as voip_router
from src.IPTV.controller import router as iptv_router
from src.dhcp.controller import router as dhcp_router
from src.chat.router import router as chat_router
from src.voice.controller import router as voice_router
from src.chat_voice.router import router as chat_voice_router
from src.chat_logs.router import router as chat_logs_router      # ← NEW
from src.admin_stats.router import router as admin_stats_router
from src.auth.router import router as auth_router
from src.gateways.router import router as gateways_router
from src.dashboard.router import router as dashboard_router
from src.prompts_admin.router import router as prompts_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Home Gateway API",
    description="API pour contrôler les appareils réseau (Wi-Fi, Telnet, etc)",
    version="1.0.0"
)

from fastapi.responses import JSONResponse

def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        {"error": "Too many attempts. Please try again after 1 minute."},
        status_code=429
    )

# Setup SlowAPI Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wifi_router)
app.include_router(telnet_router)
app.include_router(guestwifi_router)
app.include_router(debogageavance_router)
app.include_router(scheduler_router)
app.include_router(devices_router)
app.include_router(firewall_router)
app.include_router(wan_router)
app.include_router(voip_router)
app.include_router(iptv_router)
app.include_router(dhcp_router)
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(chat_voice_router)
app.include_router(chat_logs_router)                             # ✅ Conversations page
app.include_router(admin_stats_router)
app.include_router(auth_router)
app.include_router(gateways_router)
app.include_router(dashboard_router)
app.include_router(prompts_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 