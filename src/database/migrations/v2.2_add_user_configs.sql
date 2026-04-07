-- ============================================
-- V2.2 数据库迁移脚本
-- 添加用户配置表（user_configs）
-- ============================================

-- 创建用户配置表
CREATE TABLE IF NOT EXISTS user_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_config_user ON user_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_config_key ON user_configs(config_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_config_user_key ON user_configs(user_id, config_key);

-- ============================================
-- 回滚脚本（如需回滚，请执行以下语句）
-- ============================================
-- DROP TABLE IF EXISTS user_configs;