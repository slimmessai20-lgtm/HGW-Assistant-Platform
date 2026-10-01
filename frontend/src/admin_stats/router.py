"""
Admin Statistics API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from src.auth.router import get_current_user
from src.admin_stats.service import (
    get_kpi_stats,
    get_activity_last_7_days,
    get_voice_vs_text,
    get_top_users,
    get_recent_messages
)

router = APIRouter(prefix="/api/admin", tags=["admin_stats"])


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
    """✅ Messages récents (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Convertir les datetime en strings
    messages = get_recent_messages(limit=min(limit, 100))
    for msg in messages:
        if msg.get('created_at'):
            msg['created_at'] = msg['created_at'].isoformat()
    
    return messages
