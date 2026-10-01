import mysql.connector

cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='hgw_db'
)
cursor = cnx.cursor()

# Vérifier les colonnes existantes
cursor.execute("DESCRIBE chat_logs;")
print("✅ Columns in chat_logs:")
for col in cursor.fetchall():
    print(f"  - {col[0]}: {col[1]}")

cnx.close()
