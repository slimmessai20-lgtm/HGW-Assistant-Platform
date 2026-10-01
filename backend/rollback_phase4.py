import mysql.connector
import bcrypt

cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='hgw_db'
)
cursor = cnx.cursor(dictionary=True)

try:
    print("🔄 ROLLBACK - Restauration config d'avant Phase 4\n")
    
    # 1. Supprimer les nouveaux utilisateurs créés
    print("1️⃣ Suppression users créés en Phase 4...")
    cursor.execute("DELETE FROM users WHERE username IN ('admin', 'engineer', 'user')")
    print(f"   ✅ Supprimé {cursor.rowcount} utilisateurs")
    
    # 2. Rétablir les VRAIS utilisateurs d'avant
    print("\n2️⃣ Création des anciens utilisateurs...")
    old_users = [
        ('admin', 'Admin@2025', 'Administrator', 'admin@hgw.local', 'admin'),
        ('user', 'User@2025', 'General User', 'user@hgw.local', 'general'),
    ]
    
    for username, password, full_name, email, role in old_users:
        # Vérifier s'il existe
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if not cursor.fetchone():
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role, is_active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            """, (username, hashed, full_name, email, role))
            print(f"   ✅ Créé: {username} / {password}")
    
    # 3. SUPPRIMER sessions table (inutile - on garde juste les logs)
    print("\n3️⃣ Suppression table sessions (non utilisée)...")
    try:
        cursor.execute("DROP TABLE IF EXISTS sessions")
        print("   ✅ Table sessions supprimée")
    except:
        pass
    
    # 4. SUPPRIMER les colonnes nouvelles de chat_logs
    print("\n4️⃣ Suppression colonnes session_id et user_type de chat_logs...")
    try:
        cursor.execute("ALTER TABLE chat_logs DROP COLUMN session_id")
        print("   ✅ Colonne session_id supprimée")
    except:
        pass
    
    try:
        cursor.execute("ALTER TABLE chat_logs DROP COLUMN user_type")
        print("   ✅ Colonne user_type supprimée")
    except:
        pass
    
    cnx.commit()
    print("\n✅ ROLLBACK COMPLÉTÉ - Retour à l'état d'avant Phase 4")
    print("\n📝 Credentials restaurés:")
    print("   - admin / Admin@2025")
    print("   - user / User@2025")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
finally:
    cursor.close()
    cnx.close()
