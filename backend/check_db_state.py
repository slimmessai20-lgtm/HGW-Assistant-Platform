import mysql.connector

cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='hgw_db'
)
cursor = cnx.cursor(dictionary=True)

# Vérifier les utilisateurs existants
cursor.execute("SELECT id, username, role FROM users LIMIT 10")
print("=== USERS ACTUELS ===")
for row in cursor.fetchall():
    print(f"ID: {row['id']}, Username: {row['username']}, Role: {row['role']}")

# Vérifier les chat_logs
cursor.execute("SELECT COUNT(*) as cnt FROM chat_logs")
print(f"\n=== CHAT LOGS ===")
print(f"Total: {cursor.fetchone()['cnt']}")

# Vérifier les sessions
cursor.execute("SELECT COUNT(*) as cnt FROM sessions")
print(f"\n=== SESSIONS ===")
print(f"Total: {cursor.fetchone()['cnt']}")

cursor.close()
cnx.close()
