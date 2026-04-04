-- ============================================
-- V2.1 数据库回滚脚本
-- 移除用户封禁字段
-- ============================================

-- SQLite 不支持 DROP COLUMN，需要重建表
-- 以下是完整的回滚步骤

-- 1. 创建临时表（不含封禁字段）
CREATE TABLE users_backup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    oauth_provider TEXT,
    oauth_id TEXT,
    oauth_name TEXT,
    oauth_avatar TEXT,
    usage_count INTEGER DEFAULT 0,
    invited_by INTEGER,
    invite_code TEXT UNIQUE,
    has_redeemed_first BOOLEAN DEFAULT FALSE,
    free_usage_date TEXT,
    free_usage_count INTEGER DEFAULT 0,
    nickname TEXT,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    FOREIGN KEY (invited_by) REFERENCES users(id)
);

-- 2. 复制数据到临时表
INSERT INTO users_backup 
SELECT 
    id, email, password_hash, oauth_provider, oauth_id, oauth_name, oauth_avatar,
    usage_count, invited_by, invite_code, has_redeemed_first,
    free_usage_date, free_usage_count, nickname, avatar_url,
    is_active, is_verified, created_at, updated_at, last_login_at
FROM users;

-- 3. 删除原表
DROP TABLE users;

-- 4. 重命名临时表为原表名
ALTER TABLE users_backup RENAME TO users;

-- 5. 重建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_invite_code ON users(invite_code);