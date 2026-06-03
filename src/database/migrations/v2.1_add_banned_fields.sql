-- ============================================
-- V2.1 数据库迁移脚本
-- 添加用户封禁字段
-- ============================================

-- 添加封禁相关字段到 users 表
ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN banned_at DATETIME;
ALTER TABLE users ADD COLUMN banned_reason TEXT;

-- 创建索引以提高查询效率
CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned);

-- ============================================
-- 回滚脚本（如需回滚，请执行以下语句）
-- ============================================
-- ALTER TABLE users DROP COLUMN is_banned;
-- ALTER TABLE users DROP COLUMN banned_at;
-- ALTER TABLE users DROP COLUMN banned_reason;
-- DROP INDEX IF EXISTS idx_users_banned;