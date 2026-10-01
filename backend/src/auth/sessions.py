# src/auth/sessions.py
# Session management service — tracks user sessions for multi-user support

import hashlib
from typing import Optional
from src.auth.db import get_connection
import logging

logger = logging.getLogger(__name__)


def create_session(user_id: int, token: str, ip_address: str = None, user_agent: str = None) -> dict:
    """
    Create a new session for a user after successful login.
    Returns session dict with session_id.
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO sessions (user_id, token_hash, ip_address, user_agent)
                   VALUES (%s, %s, %s, %s)""",
                (user_id, token_hash, ip_address, user_agent)
            )
            conn.commit()
            session_id = cur.lastrowid
            return {
                "session_id": session_id,
                "user_id": user_id,
                "token_hash": token_hash
            }
    finally:
        conn.close()


def get_session_by_token(token: str) -> Optional[dict]:
    """
    Retrieve session info by token hash.
    Used to validate tokens and get session_id for logging.
    """
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, user_id, created_at, ended_at FROM sessions
                   WHERE token_hash = %s AND ended_at IS NULL""",
                (token_hash,)
            )
            return cur.fetchone()
    finally:
        conn.close()


def end_session(session_id: int) -> bool:
    """
    End a session (logout).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET ended_at = NOW() WHERE id = %s",
                (session_id,)
            )
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()


def get_user_sessions(user_id: int, active_only: bool = True) -> list:
    """
    Get all sessions for a user (for audit trail).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            where = "WHERE user_id = %s"
            if active_only:
                where += " AND ended_at IS NULL"
            cur.execute(
                f"""SELECT id, user_id, created_at, ended_at, ip_address
                   FROM sessions {where}
                   ORDER BY created_at DESC""",
                (user_id,)
            )
            rows = cur.fetchall()
            for r in rows:
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].isoformat()
                if r.get("ended_at"):
                    r["ended_at"] = r["ended_at"].isoformat()
            return rows
    finally:
        conn.close()


def update_session_activity(session_id: int) -> bool:
    """
    Update last_active timestamp for a session.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET last_active = NOW() WHERE id = %s",
                (session_id,)
            )
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()
