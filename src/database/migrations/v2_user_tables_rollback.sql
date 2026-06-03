-- ============================================================
-- Prism V2.0 用户系统数据库回滚脚本
-- 创建时间：2024-01-15
-- 警告：执行此脚本将删除所有用户相关数据，不可恢复！
-- ============================================================

-- 删除版本记录
DELETE FROM schema_version WHERE version = '2.0.0';

-- 删除表（注意顺序，先删除有外键依赖的表）
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS invite_records;
DROP TABLE IF EXISTS topup_records;
DROP TABLE IF EXISTS refresh_tokens;
DROP TABLE IF EXISTS verification_codes;
DROP TABLE IF EXISTS redemption_codes;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS schema_version;

-- 回滚完成提示
SELECT 'Rollback completed. All V2.0 user tables have been dropped.' AS message;