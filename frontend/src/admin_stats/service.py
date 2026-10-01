"""
Admin Statistics Service - Données temps réel pour le dashboard
"""

from datetime import datetime, timedelta
from src.auth.db import get_connection


def get_kpi_stats():
    """✅ Retourne les KPI principales (total messages, voix, utilisateurs, gateways)"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Total messages
        cursor.execute("SELECT COUNT(*) as total FROM chat_logs")
        total_msgs = cursor.fetchone()['total']
        
        # Messages voix
        cursor.execute("SELECT COUNT(*) as total FROM chat_logs WHERE voice_used = TRUE")
        voice_msgs = cursor.fetchone()['total']
        
        # Utilisateurs actifs (dernières 24h)
        cursor.execute("""
        SELECT COUNT(DISTINCT user_id) as total 
        FROM chat_logs 
        WHERE created_at >= NOW() - INTERVAL 1 DAY
        """)
        active_users = cursor.fetchone()['total']
        
        # Gateways utilisées
        cursor.execute("SELECT COUNT(DISTINCT gateway_id) as total FROM chat_logs")
        gateways = cursor.fetchone()['total']
        
        return {
            'total_messages': total_msgs,
            'voice_messages': voice_msgs,
            'text_messages': total_msgs - voice_msgs,
            'active_users_24h': active_users,
            'gateways_count': gateways,
            'voice_percentage': round((voice_msgs / total_msgs * 100) if total_msgs > 0 else 0, 1)
        }
    finally:
        cursor.close()
        conn.close()


def get_activity_last_7_days():
    """✅ Activité des 7 derniers jours (pour le graphique bar)"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count,
            SUM(CASE WHEN voice_used = TRUE THEN 1 ELSE 0 END) as voice_count
        FROM chat_logs
        WHERE created_at >= NOW() - INTERVAL 7 DAY
        GROUP BY DATE(created_at)
        ORDER BY date ASC
        """)
        
        rows = cursor.fetchall()
        
        # Remplir les jours manquants avec 0
        today = datetime.now().date()
        result = {}
        
        for i in range(7, -1, -1):
            day = today - timedelta(days=i)
            result[day.isoformat()] = {'count': 0, 'voice': 0}
        
        for row in rows:
            date_str = row['date'].isoformat()
            result[date_str] = {
                'count': row['count'],
                'voice': row['voice_count'] or 0
            }
        
        return result
    finally:
        cursor.close()
        conn.close()


def get_voice_vs_text():
    """✅ Distribution voix vs texte"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
        SELECT 
            voice_used,
            COUNT(*) as count
        FROM chat_logs
        GROUP BY voice_used
        """)
        
        rows = cursor.fetchall()
        text_count = 0
        voice_count = 0
        
        for row in rows:
            if row['voice_used']:
                voice_count = row['count']
            else:
                text_count = row['count']
        
        return {
            'text': text_count,
            'voice': voice_count
        }
    finally:
        cursor.close()
        conn.close()


def get_top_users(limit=5):
    """✅ Top N utilisateurs par nombre de messages"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(f"""
        SELECT 
            u.username,
            COUNT(c.id) as message_count,
            SUM(CASE WHEN c.voice_used = TRUE THEN 1 ELSE 0 END) as voice_count
        FROM chat_logs c
        JOIN users u ON c.user_id = u.id
        GROUP BY c.user_id, u.username
        ORDER BY message_count DESC
        LIMIT {limit}
        """)
        
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_recent_messages(limit=20):
    """✅ Derniers messages (pour le tableau detail)"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(f"""
        SELECT 
            c.id,
            u.username,
            c.gateway_name,
            c.message,
            c.response,
            c.tool_calls,
            c.voice_used,
            c.duration_ms,
            c.created_at,
            c.user_type
        FROM chat_logs c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.created_at DESC
        LIMIT {limit}
        """)
        
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
