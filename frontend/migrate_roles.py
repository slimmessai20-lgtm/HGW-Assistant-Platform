"""
Migration: rename role 'engineer' → 'technical' in DB
Run once: python migrate_roles.py
"""
import pymysql

conn = pymysql.connect(
    host='127.0.0.1', port=3306,
    user='root', password='',
    database='hgw_db',
    cursorclass=pymysql.cursors.DictCursor
)

try:
    with conn.cursor() as cur:
        # 1. Modify ENUM on users table
        cur.execute("""
            ALTER TABLE users
            MODIFY COLUMN role ENUM('general', 'technical', 'admin')
            NOT NULL DEFAULT 'general'
        """)
        print("✅ users.role ENUM updated")

        # 2. Rename existing engineer rows → technical
        cur.execute("UPDATE users SET role = 'technical' WHERE role = 'engineer'")
        print(f"✅ {cur.rowcount} user(s) updated: engineer → technical")

        # 3. Modify ENUM on chat_logs.user_type if exists
        try:
            cur.execute("""
                ALTER TABLE chat_logs
                MODIFY COLUMN user_type ENUM('general', 'technical', 'admin')
                NOT NULL DEFAULT 'general'
            """)
            cur.execute("UPDATE chat_logs SET user_type = 'technical' WHERE user_type = 'engineer'")
            print(f"✅ chat_logs.user_type updated ({cur.rowcount} rows)")
        except Exception:
            print("⚠️  chat_logs.user_type skipped (column may not exist yet)")

    conn.commit()
    print("\n✅ Migration terminée avec succès !")

    # Verify
    with conn.cursor() as cur:
        cur.execute("SELECT username, role FROM users ORDER BY role")
        users = cur.fetchall()
        print("\nUtilisateurs en DB :")
        for u in users:
            print(f"  • {u['username']} — {u['role']}")

except Exception as e:
    conn.rollback()
    print(f"❌ Erreur: {e}")
finally:
    conn.close()
