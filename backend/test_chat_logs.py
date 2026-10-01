#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.auth.db import get_connection

def test_chat_logs():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Count conversations
    cursor.execute('SELECT COUNT(*) as cnt FROM chat_logs')
    result = cursor.fetchone()
    count = result['cnt']
    
    print(f"\n📊 CONVERSATION LOG STATUS")
    print(f"   Total conversations: {count}")
    
    if count > 0:
        # Show recent 3
        cursor.execute("""
            SELECT id, username, gateway_name, message, created_at 
            FROM chat_logs 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        recent = cursor.fetchall()
        print(f"\n   ✅ Recent conversations:")
        for log in recent:
            print(f"      - [{log['username']}] {log['message'][:40]}... ({log['created_at']})")
    else:
        print("   ⚠️  No conversations yet")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    test_chat_logs()
