-- ============================================
-- V2.1 数据库迁移脚本
-- 新增审计日志表
-- ============================================

-- 创建审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 操作者信息
    admin_id INTEGER NOT NULL,
    admin_email TEXT NOT NULL,
    
    -- 操作类型
    action TEXT NOT NULL,              -- ban_user, unban_user, generate_codes, etc.
    action_category TEXT NOT NULL,     -- user_management, code_management, etc.
    
    -- 操作目标
    target_type TEXT,                  -- user, code, batch, etc.
    target_id TEXT,                    -- 目标ID（可能是多个，用逗号分隔）
    target_info TEXT,                  -- JSON格式的目标信息
    
    -- 操作详情
    action_detail TEXT,                -- JSON格式的详细操作信息
    
    -- 请求信息
    ip_address TEXT,
    user_agent TEXT,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin ON audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_category ON audit_logs(action_category);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target ON audit_logs(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- ============================================
-- 回滚脚本（如需回滚，请执行以下语句）
-- ============================================
-- DROP TABLE IF EXISTS audit_logs;
-- DROP INDEX IF EXISTS idx_audit_logs_admin;
-- DROP INDEX IF EXISTS idx_audit_logs_action;
-- DROP INDEX IF EXISTS idx_audit_logs_category;
-- DROP INDEX IF EXISTS idx_audit_logs_target;
-- DROP INDEX IF EXISTS idx_audit_logs_created;