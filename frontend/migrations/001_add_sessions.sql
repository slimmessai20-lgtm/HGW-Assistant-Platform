-- ── Migration: Sessions Management Table ────────────────────────────────────────

-- ✅ Créer la table sessions pour le suivi multi-utilisateur
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
);

-- ✅ Ajouter session_id et user_type à la table chat_logs
ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS session_id INT DEFAULT NULL;
ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS user_type ENUM('general', 'engineer', 'admin') DEFAULT 'general';
ALTER TABLE chat_logs ADD INDEX IF NOT EXISTS idx_session_id (session_id);

-- Ajouter la foreign key si elle n'existe pas
ALTER TABLE chat_logs 
ADD CONSTRAINT fk_session_id FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL;

-- ✅ Vérifier que la table users a les colonnes nécessaires
ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS role ENUM('general', 'engineer', 'admin') DEFAULT 'general';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

