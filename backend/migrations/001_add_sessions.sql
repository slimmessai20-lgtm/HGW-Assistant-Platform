-- ============================================================================
-- Migration 001: Add Sessions and update chat_logs with session tracking
-- ============================================================================

-- ────────────────────────────────────────────────────────────────────────────
-- Table: sessions
-- Purpose: Track user sessions for multi-user support and conversation history
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token_hash VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  ended_at TIMESTAMP NULL,
  ip_address VARCHAR(45),
  user_agent TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX (user_id),
  INDEX (created_at),
  INDEX (ended_at)
);

-- ────────────────────────────────────────────────────────────────────────────
-- Update chat_logs table: add session_id and user_type for response adaptation
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE chat_logs
ADD COLUMN IF NOT EXISTS session_id INT,
ADD COLUMN IF NOT EXISTS user_type ENUM('general', 'engineer', 'admin') DEFAULT 'general',
ADD FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
ADD INDEX (session_id),
ADD INDEX (user_type);

-- ────────────────────────────────────────────────────────────────────────────
-- Verify users table has all required fields
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE users
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS role ENUM('general', 'engineer', 'admin') DEFAULT 'general',
ADD COLUMN IF NOT EXISTS is_active TINYINT DEFAULT 1,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN email VARCHAR(255) UNIQUE NULL;

-- ────────────────────────────────────────────────────────────────────────────
-- Create index on users for performance
-- ────────────────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
