import mysql.connector
from mysql.connector import errorcode

cnx = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='hgw_db'
)
cursor = cnx.cursor()

try:
    # 1. Créer la table sessions
    print("1️⃣ Creating sessions table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
      id INT PRIMARY KEY AUTO_INCREMENT,
      user_id INT NOT NULL,
      token_hash VARCHAR(255) NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      ended_at TIMESTAMP NULL,
      ip_address VARCHAR(45),
      user_agent TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      INDEX idx_user_id (user_id),
      INDEX idx_token_hash (token_hash),
      INDEX idx_ended_at (ended_at)
    )
    """)
    print("   ✅ Sessions table created")
    
    # 2. Ajouter session_id à chat_logs
    print("2️⃣ Adding session_id column...")
    cursor.execute("""
    ALTER TABLE chat_logs 
    ADD COLUMN IF NOT EXISTS session_id INT DEFAULT NULL
    """)
    print("   ✅ session_id column added")
    
    # 3. Ajouter la foreign key
    print("3️⃣ Adding foreign key constraint...")
    cursor.execute("""
    ALTER TABLE chat_logs 
    ADD CONSTRAINT fk_session_id 
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
    """)
    print("   ✅ Foreign key added")
    
    # 4. Ajouter index
    print("4️⃣ Adding index...")
    cursor.execute("""
    ALTER TABLE chat_logs 
    ADD INDEX IF NOT EXISTS idx_session_id (session_id)
    """)
    print("   ✅ Index added")
    
    # 5. Vérifier la table users
    print("5️⃣ Verifying users table...")
    cursor.execute("""
    ALTER TABLE users 
    MODIFY COLUMN password_hash VARCHAR(255)
    """)
    cursor.execute("""
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS role ENUM('general', 'engineer', 'admin') DEFAULT 'general'
    """)
    cursor.execute("""
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
    """)
    print("   ✅ Users table verified")
    
    cnx.commit()
    print("\n✅ Migration completed successfully!")
    
except mysql.connector.Error as err:
    print(f"❌ Database Error: {err}")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    cursor.close()
    cnx.close()
