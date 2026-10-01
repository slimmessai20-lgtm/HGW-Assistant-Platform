# src/chat_logs/service.py
# DB functions for chat interaction logging
# Same pattern as gateways/service.py

from src.auth.db import get_connection
from src.auth.service import get_all_users
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ── Corrections table bootstrap ───────────────────────────────────────────────
def _ensure_corrections_table():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_corrections (
                    id               INT AUTO_INCREMENT PRIMARY KEY,
                    log_id           INT NOT NULL,
                    original_response TEXT NOT NULL,
                    corrected_response TEXT NOT NULL,
                    corrected_by     VARCHAR(100),
                    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_log (log_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
    except Exception as e:
        logger.warning(f"[chat_corrections] Table bootstrap warning: {e}")
    finally:
        conn.close()

try:
    _ensure_corrections_table()
except Exception as _boot_err:
    logger.warning(f"[chat_corrections] Skipping table bootstrap (DB unavailable): {_boot_err}")


def _ensure_feedback_column():
    """Add feedback column to chat_logs if it doesn't exist yet."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE chat_logs
                ADD COLUMN IF NOT EXISTS feedback ENUM('up','down') NULL DEFAULT NULL
            """)
            conn.commit()
    except Exception as e:
        logger.warning(f"[chat_logs] feedback column bootstrap: {e}")
    finally:
        conn.close()

try:
    _ensure_feedback_column()
except Exception as _boot_err:
    logger.warning(f"[chat_logs] Skipping feedback column bootstrap (DB unavailable): {_boot_err}")


def save_feedback(log_id: int, value: str) -> bool:
    """Set 'up' or 'down' feedback on a chat log row."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE chat_logs SET feedback = %s WHERE id = %s",
                (value, log_id)
            )
            conn.commit()
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"[chat_logs] save_feedback failed: {e}")
        return False
    finally:
        conn.close()


def save_log(
    message:      str,
    response:     str,
    user_id:      Optional[int]  = None,
    username:     Optional[str]  = None,
    gateway_id:   Optional[int]  = None,
    gateway_name: Optional[str]  = None,
    tool_calls:   int            = 0,
    voice_used:   bool           = False,
    duration_ms:  Optional[int]  = None,
    session_id:   Optional[int]  = None,  # ✅ Multi-user session tracking
    user_type:    str            = 'general',  # ✅ Response adaptation: general, engineer, admin
) -> Optional[int]:
    """
    Insert one chat interaction into chat_logs with session tracking.
    Returns the new row id, or None if insert failed.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chat_logs
                   (user_id, username, gateway_id, gateway_name,
                    message, response, tool_calls, voice_used, duration_ms,
                    session_id, user_type)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, username, gateway_id, gateway_name,
                 message, response, tool_calls,
                 1 if voice_used else 0, duration_ms,
                 session_id, user_type)
            )
            conn.commit()
            return cur.lastrowid
    except Exception as e:
        logger.error(f"[chat_logs] Failed to save log: {e}")
        return None
    finally:
        conn.close()


def get_logs(
    user_id:    Optional[int] = None,
    gateway_id: Optional[int] = None,
    date_from:  Optional[str] = None,   # "YYYY-MM-DD"
    date_to:    Optional[str] = None,   # "YYYY-MM-DD"
    limit:      int           = 100,
    offset:     int           = 0,
) -> list:
    """
    Fetch chat logs with optional filters.
    Admin sees all — filter by user_id/gateway_id/date range.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            conditions = []
            params     = []

            if user_id is not None:
                conditions.append("user_id = %s")
                params.append(user_id)
            if gateway_id is not None:
                conditions.append("gateway_id = %s")
                params.append(gateway_id)
            if date_from:
                conditions.append("DATE(created_at) >= %s")
                params.append(date_from)
            if date_to:
                conditions.append("DATE(created_at) <= %s")
                params.append(date_to)

            where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

            cur.execute(
                f"""SELECT * FROM chat_logs
                    {where}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s""",
                (*params, limit, offset)
            )
            rows = cur.fetchall()

            # Convert datetime to ISO string for JSON serialization
            for r in rows:
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].isoformat()
            return rows
    finally:
        conn.close()


def get_logs_stats() -> dict:
    """
    Aggregate stats for admin dashboard:
    total logs, per user, per gateway, per day (last 7 days).
    """
    # Active users count — live from users table via its own connection
    all_users = get_all_users()
    active_users_count = sum(1 for u in all_users if u.get("is_active"))
    active_usernames   = {u["username"] for u in all_users if u.get("is_active")}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Total interactions
            cur.execute("SELECT COUNT(*) as total FROM chat_logs")
            total = cur.fetchone()["total"]

            # Per user (top 10) — only users that still exist and are active
            cur.execute("""
                SELECT username, COUNT(*) as cnt
                FROM chat_logs
                WHERE username IS NOT NULL
                GROUP BY username
                ORDER BY cnt DESC
                LIMIT 10
            """)
            by_user = [r for r in cur.fetchall() if r["username"] in active_usernames]

            # Per gateway (top 10) — exclude logs with no gateway selected
            cur.execute("""
                SELECT gateway_name as gateway, COUNT(*) as cnt
                FROM chat_logs
                WHERE gateway_name IS NOT NULL
                GROUP BY gateway_name
                ORDER BY cnt DESC
                LIMIT 10
            """)
            by_gateway = cur.fetchall()

            # Last 7 days activity
            cur.execute("""
                SELECT DATE(created_at) as day, COUNT(*) as cnt
                FROM chat_logs
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(created_at)
                ORDER BY day ASC
            """)
            by_day = cur.fetchall()
            for r in by_day:
                if r.get("day"):
                    r["day"] = str(r["day"])

            # Voice usage
            cur.execute("""
                SELECT
                    SUM(voice_used) as voice_count,
                    COUNT(*) - SUM(voice_used) as text_count
                FROM chat_logs
            """)
            voice_stats = cur.fetchone()

            return {
                "total_interactions": total,
                "active_users_count": active_users_count,
                "by_user":           by_user,
                "by_gateway":        by_gateway,
                "last_7_days":       by_day,
                "voice_usage":       voice_stats,
            }
    finally:
        conn.close()


def get_log_by_id(log_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM chat_logs WHERE id = %s", (log_id,))
            row = cur.fetchone()
            if row and row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
            return row
    finally:
        conn.close()


def delete_log(log_id: int) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_logs WHERE id = %s", (log_id,))
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()


# ── Corrections ───────────────────────────────────────────────────────────────

def save_correction(
    log_id: int,
    original_response: str,
    corrected_response: str,
    corrected_by: Optional[str] = None,
) -> bool:
    """Insert or replace a correction for a given log entry."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chat_corrections
                       (log_id, original_response, corrected_response, corrected_by)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                       corrected_response = VALUES(corrected_response),
                       corrected_by       = VALUES(corrected_by),
                       created_at         = CURRENT_TIMESTAMP""",
                (log_id, original_response, corrected_response, corrected_by),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"[chat_corrections] save_correction failed: {e}")
        return False
    finally:
        conn.close()


def get_correction(log_id: int) -> Optional[dict]:
    """Return the correction for a log, or None if none exists."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM chat_corrections WHERE log_id = %s", (log_id,)
            )
            row = cur.fetchone()
            if row and row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
            return row
    finally:
        conn.close()