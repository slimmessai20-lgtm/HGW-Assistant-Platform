# src/chat_logs/router.py
# Admin endpoints to view, filter and delete chat logs
# Pattern identical to gateways/router.py

import asyncio
import traceback
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from src.auth.router import get_current_user, require_admin
from src.chat_logs import service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat-logs", tags=["chat-logs"])


# ── GET /chat-logs  — list with filters (admin only) ──────────────────────────
@router.get("")
def list_logs(
    user_id:    Optional[int] = Query(None, description="Filter by user ID"),
    gateway_id: Optional[int] = Query(None, description="Filter by gateway ID"),
    date_from:  Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_to:    Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    limit:      int           = Query(100, ge=1, le=2000),
    offset:     int           = Query(0,   ge=0),
    _: dict = Depends(require_admin),
):
    """
    Returns chat logs with optional filters.
    Reserved for admins.
    """
    return service.get_logs(
        user_id=user_id,
        gateway_id=gateway_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


# ── GET /chat-logs/stats  — aggregate stats (admin only) ──────────────────────
@router.get("/stats")
def logs_stats(_: dict = Depends(require_admin)):
    """
    Returns aggregate statistics:
    total interactions, per user, per gateway, last 7 days, voice usage.
    """
    return service.get_logs_stats()


# ── GET /chat-logs/{id}  — single log detail (admin only) ─────────────────────
@router.get("/{log_id}")
def get_log(log_id: int, _: dict = Depends(require_admin)):
    log = service.get_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log introuvable")
    return log


# ── DELETE /chat-logs/{id}  — delete single log (admin only) ──────────────────
@router.delete("/{log_id}")
def delete_log(log_id: int, _: dict = Depends(require_admin)):
    deleted = service.delete_log(log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Log introuvable")
    return {"message": "Log supprimé"}


# ── POST /chat-logs/compare  — replay a message as general AND technical ───────
class CompareRequest(BaseModel):
    message: str
    gateway_id: Optional[int] = None


@router.post("/compare")
async def compare_responses(req: CompareRequest, _: dict = Depends(require_admin)):
    """
    Replays the same message against the AI with both 'general' and 'engineer'
    roles and returns both responses side-by-side.  Admin only.
    """
    from src.chat.router import _run_in_thread, _get_gateway_telnet, _clean_response

    telnet_config: dict = {}
    if req.gateway_id:
        telnet_config = _get_gateway_telnet(req.gateway_id)

    try:
        general_raw  = await asyncio.to_thread(_run_in_thread, req.message, [], telnet_config, "general")
        technical_raw = await asyncio.to_thread(_run_in_thread, req.message, [], telnet_config, "engineer")
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except BaseException as e:
        logger.error(f"Compare endpoint error:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

    return {
        "general":        _clean_response(general_raw.get("response", "")),
        "technical":      _clean_response(technical_raw.get("response", "")),
        "general_tools":  general_raw.get("tool_calls_count", 0),
        "technical_tools": technical_raw.get("tool_calls_count", 0),
    }


# ── POST /chat-logs/{id}/correct  — save an admin correction ──────────────────
class CorrectionRequest(BaseModel):
    corrected_response: str


@router.post("/{log_id}/correct")
def save_correction(
    log_id: int,
    req: CorrectionRequest,
    user: dict = Depends(require_admin),
):
    """
    Admin saves a corrected response for a chat log entry.
    Stored in chat_corrections as evaluation data.
    """
    log = service.get_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    ok = service.save_correction(
        log_id=log_id,
        original_response=log["response"],
        corrected_response=req.corrected_response,
        corrected_by=user.get("sub") or user.get("username"),
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save correction")
    return {"message": "Correction saved", "log_id": log_id}


# ── GET /chat-logs/{id}/correction  — get correction for a log ────────────────
@router.get("/{log_id}/correction")
def get_correction(log_id: int, _: dict = Depends(require_admin)):
    """Return the admin correction for a given log, or 404 if none."""
    row = service.get_correction(log_id)
    if not row:
        raise HTTPException(status_code=404, detail="No correction found")
    return row


# ── POST /chat-logs/{id}/feedback  — thumbs up / down ─────────────────────────
class FeedbackRequest(BaseModel):
    value: str  # 'up' or 'down'


@router.post("/{log_id}/feedback")
def post_feedback(
    log_id: int,
    body:   FeedbackRequest,
    user:   dict = Depends(get_current_user),
):
    """Any authenticated user can rate an AI response."""
    if body.value not in ("up", "down"):
        raise HTTPException(status_code=400, detail="value must be 'up' or 'down'")
    ok = service.save_feedback(log_id, body.value)
    if not ok:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"message": "Feedback saved", "log_id": log_id, "value": body.value}