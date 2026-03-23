-- ============================================================
-- Prism V2.0 用户系统数据库迁移脚本
-- 创建时间：2024-01-15
-- 说明：创建用户系统相关的所有表结构
-- ============================================================

-- ============================================================
-- 1. 用户表 (users)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    -- 主键
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 基本信息
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,                    -- 可为空（OAuth 用户）
    
    -- OAuth 信息
    oauth_provider TEXT,                   -- 'github' / 'wechat' / NULL
    oauth_id TEXT,                         -- OAuth 平台的用户 ID
    oauth_name TEXT,                       -- OAuth 用户名
    
    -- 使用次数
    usage_count INTEGER DEFAULT 0,         -- 剩余使用次数
    
    -- 邀请系统
    invited_by INTEGER,                    -- 邀请人 ID
    invite_code TEXT UNIQUE,               -- 用户专属邀请码
    has_redeemed_first BOOLEAN DEFAULT FALSE,  -- 是否已享受首次充值返利
    
    -- 免费用户每日使用（备份用，主要依赖本地存储）
    free_usage_date TEXT,                  -- 免费使用日期 YYYY-MM-DD
    free_usage_count INTEGER DEFAULT 0,    -- 当日免费使用次数
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    
    -- 唯一约束：OAuth 用户唯一
    UNIQUE(oauth_provider, oauth_id),
    
    -- 外键
    FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_invite_code ON users(invite_code);
CREATE INDEX IF NOT EXISTS idx_users_invited_by ON users(invited_by);
CREATE INDEX IF NOT EXISTS idx_users_oauth ON users(oauth_provider, oauth_id);

-- ============================================================
-- 2. 兑换码表 (redemption_codes)
-- ============================================================
CREATE TABLE IF NOT EXISTS redemption_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 兑换码信息
    code TEXT UNIQUE NOT NULL,             -- 兑换码：PRISM-XXXXXXXX
    count INTEGER NOT NULL,                -- 可兑换的使用次数
    
    -- 批次管理
    batch_id TEXT NOT NULL,                -- 批次号：BATCH-YYYYMMDD-NNN
    price DECIMAL(10, 2),                  -- 价格（用于统计）
    description TEXT,                      -- 描述：如"早鸟价100次"
    
    -- 使用状态
    used BOOLEAN DEFAULT FALSE,
    used_by INTEGER,
    used_at DATETIME,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,                   -- 过期时间（可选）
    
    -- 外键
    FOREIGN KEY (used_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 兑换码表索引
CREATE INDEX IF NOT EXISTS idx_rc_code ON redemption_codes(code);
CREATE INDEX IF NOT EXISTS idx_rc_batch ON redemption_codes(batch_id);
CREATE INDEX IF NOT EXISTS idx_rc_used ON redemption_codes(used);
CREATE INDEX IF NOT EXISTS idx_rc_used_by ON redemption_codes(used_by);

-- ============================================================
-- 3. 验证码表 (verification_codes)
-- ============================================================
CREATE TABLE IF NOT EXISTS verification_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    code TEXT NOT NULL,                    -- 6 位验证码
    purpose TEXT NOT NULL,                 -- 'register' / 'reset_password'
    expires_at DATETIME NOT NULL,          -- 过期时间
    used BOOLEAN DEFAULT FALSE,            -- 是否已使用
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 验证码表索引
CREATE INDEX IF NOT EXISTS idx_vc_email_purpose ON verification_codes(email, purpose);
CREATE INDEX IF NOT EXISTS idx_vc_expires ON verification_codes(expires_at);

-- ============================================================
-- 4. 刷新令牌表 (refresh_tokens)
-- ============================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,      -- Token 哈希值
    device_info TEXT,                      -- 设备信息（可选）
    ip_address TEXT,                       -- IP 地址（可选）
    expires_at DATETIME NOT NULL,          -- 过期时间
    revoked BOOLEAN DEFAULT FALSE,         -- 是否已撤销
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 刷新令牌表索引
CREATE INDEX IF NOT EXISTS idx_rt_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_rt_expires ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_rt_token_hash ON refresh_tokens(token_hash);

-- ============================================================
-- 5. 充值记录表 (topup_records)
-- ============================================================
CREATE TABLE IF NOT EXISTS topup_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    -- 充值来源
    source TEXT NOT NULL,                  -- 'redemption_code' / 'wechat_pay'
    code_id INTEGER,                       -- 兑换码 ID（如果来源是兑换码）
    
    -- 充值金额
    count INTEGER NOT NULL,                -- 充值次数
    bonus_count INTEGER DEFAULT 0,         -- 赠送次数（如邀请返利）
    
    -- 返利信息
    invited_by INTEGER,                    -- 邀请人 ID
    invited_bonus_given BOOLEAN DEFAULT FALSE,  -- 是否已发放邀请返利
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (code_id) REFERENCES redemption_codes(id) ON DELETE SET NULL,
    FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 充值记录表索引
CREATE INDEX IF NOT EXISTS idx_tr_user ON topup_records(user_id);
CREATE INDEX IF NOT EXISTS idx_tr_created ON topup_records(created_at);
CREATE INDEX IF NOT EXISTS idx_tr_source ON topup_records(source);

-- ============================================================
-- 6. 邀请记录表 (invite_records) - 用于追踪邀请关系
-- ============================================================
CREATE TABLE IF NOT EXISTS invite_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inviter_id INTEGER NOT NULL,           -- 邀请人 ID
    invitee_id INTEGER NOT NULL,           -- 被邀请人 ID
    invite_code TEXT NOT NULL,             -- 使用的邀请码
    
    -- 奖励状态
    bonus_given BOOLEAN DEFAULT FALSE,     -- 是否已发放奖励
    bonus_count INTEGER DEFAULT 0,         -- 奖励次数
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (inviter_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (invitee_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 邀请记录表索引
CREATE INDEX IF NOT EXISTS idx_ir_inviter ON invite_records(inviter_id);
CREATE INDEX IF NOT EXISTS idx_ir_invitee ON invite_records(invitee_id);

-- ============================================================
-- 7. 管理员表 (admins) - 用于后台管理
-- ============================================================
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,              -- 关联用户 ID
    role TEXT DEFAULT 'admin',             -- 'admin' / 'super_admin'
    permissions TEXT,                      -- JSON 格式的权限列表
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 管理员表索引
CREATE INDEX IF NOT EXISTS idx_admins_user ON admins(user_id);

-- ============================================================
-- 数据库版本记录
-- ============================================================
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- 记录本次迁移
INSERT INTO schema_version (version, description) 
VALUES ('2.0.0', '用户系统基础表：users, redemption_codes, verification_codes, refresh_tokens, topup_records, invite_records, admins');