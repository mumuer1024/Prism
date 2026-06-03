# -*- coding: utf-8 -*-
"""
数据库模块（激活码架构）

提供数据库连接、ORM 模型和 CRUD 操作
"""

from src.database.connection import (
    engine,
    SessionLocal,
    get_db,
    init_database,
    close_database,
)
from src.database.models import (
    Base,
    ActivationCode,
    Device,
    ReferralCode,
    AnonymousUsage,
    AdminUser,
    AuditLog,
    MarketplaceTemplate,
    SchemaVersion,
)
from src.database.crud import (
    # 激活码相关
    generate_activation_code,
    create_activation_code,
    create_activation_codes_batch,
    get_activation_code_by_code,
    get_activation_code_by_id,
    get_activation_code_by_device_id,
    update_activation_code,
    add_quota_to_activation_code,
    deduct_activation_code_quota,
    deactivate_activation_code,
    list_activation_codes,

    # 设备相关
    create_device,
    get_devices_by_code_id,
    get_device_by_id,
    delete_device,
    update_device_last_seen,
    count_devices_by_code_id,

    # 推荐码相关
    generate_referral_code,
    create_referral_code,
    get_referral_code_by_code,
    get_referral_code_by_code_id,
    update_referral_stats,

    # 匿名用户相关
    get_or_create_anonymous_usage,
    reset_anonymous_daily_usage,
    increment_anonymous_usage,
    get_anonymous_remaining_quota,

    # 管理员相关
    get_admin_by_username,
    verify_admin_password,
    create_admin_user,
    update_admin_password,

    # 审计日志相关
    create_audit_log,
    get_audit_logs,

    # 预设广场相关
    get_marketplace_templates,
    get_marketplace_template_by_id,
    increment_template_import_count,

    # 用户配置相关
    get_user_prompt_by_code_id,
    create_or_update_user_prompt,
    get_user_sources_by_code_id,
    get_user_config_by_key,
    set_user_config,
    get_dailyhot_configs_by_code_id,
)

__all__ = [
    # 连接
    "engine",
    "SessionLocal",
    "get_db",
    "init_database",
    "close_database",

    # 模型
    "Base",
    "ActivationCode",
    "Device",
    "ReferralCode",
    "AnonymousUsage",
    "AdminUser",
    "AuditLog",
    "MarketplaceTemplate",
    "SchemaVersion",

    # CRUD - 激活码
    "generate_activation_code",
    "create_activation_code",
    "create_activation_codes_batch",
    "get_activation_code_by_code",
    "get_activation_code_by_id",
    "get_activation_code_by_device_id",
    "update_activation_code",
    "add_quota_to_activation_code",
    "deduct_activation_code_quota",
    "deactivate_activation_code",
    "list_activation_codes",

    # CRUD - 设备
    "create_device",
    "get_devices_by_code_id",
    "get_device_by_id",
    "delete_device",
    "update_device_last_seen",
    "count_devices_by_code_id",

    # CRUD - 推荐码
    "generate_referral_code",
    "create_referral_code",
    "get_referral_code_by_code",
    "get_referral_code_by_code_id",
    "update_referral_stats",

    # CRUD - 匿名用户
    "get_or_create_anonymous_usage",
    "reset_anonymous_daily_usage",
    "increment_anonymous_usage",
    "get_anonymous_remaining_quota",

    # CRUD - 管理员
    "get_admin_by_username",
    "verify_admin_password",
    "create_admin_user",
    "update_admin_password",

    # CRUD - 审计日志
    "create_audit_log",
    "get_audit_logs",

    # CRUD - 预设广场
    "get_marketplace_templates",
    "get_marketplace_template_by_id",
    "increment_template_import_count",

    # CRUD - 用户配置
    "get_user_prompt_by_code_id",
    "create_or_update_user_prompt",
    "get_user_sources_by_code_id",
    "get_user_config_by_key",
    "set_user_config",
    "get_dailyhot_configs_by_code_id",
]