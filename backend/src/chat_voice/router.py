# src/chat_voice/router.py
# Combined Chat + Voice — saves every interaction to chat_logs

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import logging
import asyncio
import base64
import io
import re
import time

from src.chat.router import _run_in_thread, _clean_response, _get_gateway_telnet
from src.chat_logs import service as logs_service
from src.auth.router import get_current_user
from src.auth.service import touch_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat-voice", tags=["chat-voice"])

# Optional JWT parsing — we extract user info if token is present
security = HTTPBearer(auto_error=False)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatVoiceRequest(BaseModel):
    message:       str
    history:       List[ChatMessage] = []
    gateway_id:    Optional[int]     = None
    with_voice:    bool              = True
    language_code: str               = "fr"

    # ✅ AJOUT IMPORTANT
    is_voice_input: bool = False   # 👈 TRUE seulement si micro utilisé


class ChatVoiceResponse(BaseModel):
    response:        str
    tool_calls_count: int            = 0
    audio_base64:    Optional[str]   = None
    voice_available: bool            = False
    log_id:          Optional[int]   = None


def _text_to_speech_base64(text: str, lang: str = "fr") -> Optional[str]:
    """Convert text to MP3 using gTTS, return as base64. Returns None on failure."""
    try:
        from gtts import gTTS
        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"[*_`#]", "", clean)
        clean = re.sub(r"\n+", ". ", clean).strip()
        if len(clean) > 500:
            clean = clean[:500] + "..."

        tts = gTTS(text=clean, lang=lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    except Exception as e:
        logger.warning(f"[TTS] gTTS failed: {e}")
        return None


def _extract_user_from_token(credentials: Optional[HTTPAuthorizationCredentials]) -> dict:
    """Extract user_id, username, role and session_id from JWT token."""
    if not credentials:
        return {}
    try:
        import jwt
        from src.auth.service import SECRET_KEY, ALGORITHM
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user_id":    int(payload.get("sub", 0)) or None,
            "username":   payload.get("username"),
            "role":       payload.get("role", "general"),
            "session_id": payload.get("session_id"),
        }
    except Exception:
        return {}


@router.post("/", response_model=ChatVoiceResponse)
async def chat_with_voice(
    request:     ChatVoiceRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    start_time = time.time()

    try:
        # ── 1. Resolve user from JWT (optional) ──────────────────────────────
        user_info  = _extract_user_from_token(credentials)
        user_id    = user_info.get("user_id")
        username   = user_info.get("username")
        user_role  = user_info.get("role", "general")
        session_id = user_info.get("session_id")

        # ── 2. Resolve gateway info ───────────────────────────────────────────
        history        = [{"role": h.role, "content": h.content} for h in request.history]
        telnet_config: dict = {}
        gateway_name:  Optional[str] = None

        if request.gateway_id:
            telnet_config = _get_gateway_telnet(request.gateway_id)
            gateway_name  = telnet_config.get("name")

        # ── 3. Run chat pipeline ──────────────────────────────────────────────
        data             = await asyncio.to_thread(_run_in_thread, request.message, history, telnet_config, user_role)
        chat_response    = _clean_response(data["response"])
        tool_calls_count = data.get("tool_calls_count", 0)

        # ── 4. Generate audio (gTTS) ──────────────────────────────────────────
        audio_base64    = None
        voice_available = False

        if request.with_voice:
            lang         = request.language_code.split("-")[0]   # "fr-FR" → "fr"
            audio_base64 = await asyncio.to_thread(_text_to_speech_base64, chat_response, lang)
            voice_available = audio_base64 is not None

        # ── 5. Log the interaction to DB ──────────────────────────────────────
        duration_ms = int((time.time() - start_time) * 1000)
        
        log_id = None
        try:
            log_id = logs_service.save_log(
                message      = request.message,
                response     = chat_response,
                user_id      = user_id,
                username     = username,
                gateway_id   = request.gateway_id,
                gateway_name = gateway_name,
                tool_calls   = tool_calls_count,
                voice_used   = request.is_voice_input,
                duration_ms  = duration_ms,
                session_id   = session_id,
                user_type    = user_role,
            )
            if session_id:
                touch_session(session_id)
        except Exception as log_err:
            logger.error(f"[chat_logs] save_log failed: {log_err}")

        # ── 6. Return response ────────────────────────────────────────────────
        return ChatVoiceResponse(
            response         = chat_response,
            tool_calls_count = tool_calls_count,
            audio_base64     = audio_base64,
            voice_available  = voice_available,
            log_id           = log_id,
        )

    except Exception as e:
        logger.error(f"[chat-voice] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))