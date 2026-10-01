"""
Admin Statistics API Endpoints - Données temps réel pour dashboard
"""

from fastapi import APIRouter, Depends, HTTPException
from src.auth.router import get_current_user
from src.admin_stats.service import (
    get_kpi_stats,
    get_activity_last_7_days,
    get_voice_vs_text,
    get_top_users,
    get_recent_messages,
    get_top_questions,
    get_feedback_stats,
    get_response_time_stats,
    get_hourly_heatmap,
)

router = APIRouter(prefix="/admin", tags=["admin_stats"])


@router.get("/stats/kpi")
def get_kpi(current_user = Depends(get_current_user)):
    """✅ Récupère les KPI principales (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return get_kpi_stats()


@router.get("/stats/activity")
def get_activity(current_user = Depends(get_current_user)):
    """✅ Activité derniers 7 jours (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return get_activity_last_7_days()


@router.get("/stats/voice-text")
def get_distribution(current_user = Depends(get_current_user)):
    """✅ Distribution voix vs texte (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return get_voice_vs_text()


@router.get("/stats/top-users")
def get_top(limit: int = 5, current_user = Depends(get_current_user)):
    """✅ Top utilisateurs (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return get_top_users(limit=min(limit, 20))


@router.get("/stats/recent-messages")
def get_recent(limit: int = 20, current_user = Depends(get_current_user)):
    """✅ Messages récents avec détails (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    messages = get_recent_messages(limit=min(limit, 100))
    for msg in messages:
        if msg.get('created_at'):
            msg['created_at'] = msg['created_at'].isoformat()
    return messages


@router.get("/stats/top-questions")
def get_questions(limit: int = 10, current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return get_top_questions(limit=min(limit, 20))


@router.get("/stats/feedback")
def get_feedback(current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return get_feedback_stats()


@router.get("/stats/response-time")
def get_rt(current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return get_response_time_stats()


@router.get("/stats/hourly")
def get_hourly(current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return get_hourly_heatmap()
