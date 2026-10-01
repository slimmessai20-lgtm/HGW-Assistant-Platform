import mysql.connector
import bcrypt

cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='hgw_db'
)
cursor = cnx.cursor()

# Créer 3 utilisateurs de démo avec des mots de passe hashés
demo_users = [
    ('admin',    'Admin@2025',    'Administrator', 'admin@hgw.local',    'admin'),
    ('engineer', 'Engineer@2025', 'John Engineer', 'engineer@hgw.local', 'engineer'),
    ('user',     'User@2025',     'Jane User',     'user@hgw.local',     'general'),
]

try:
    for username, password, full_name, email, role in demo_users:
        # Hash le mot de passe
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print(f"⚠️  User '{username}' already exists, skipping...")
            continue
        
        # Insérer l'utilisateur
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, email, role, is_active)
        VALUES (%s, %s, %s, %s, %s, TRUE)
        """, (username, hashed, full_name, email, role))
        
        print(f"✅ Created user: {username} (role: {role})")
    
    cnx.commit()
    print("\n✅ Demo users created successfully!")
    print("\nCredentials for testing:")
    print("  📱 Admin:    admin / Admin@2025")
    print("  🔧 Engineer: engineer / Engineer@2025")
    print("  👤 User:     user / User@2025")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    cnx.close()
