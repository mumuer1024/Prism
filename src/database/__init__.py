# -*- coding: utf-8 -*-
"""
数据库模块

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
    User,
    VerificationCode,
    RefreshToken,
    RedemptionCode,
    TopupRecord,
    InviteRecord,
    Admin,
    SchemaVersion,
)
from src.database.crud import (
    # 用户相关
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_invite_code,
    update_user_usage_count,
    update_last_login,
    update_password,
    
    # 验证码相关
    create_verification_code,
    get_valid_verification_code,
    mark_code_as_used,
    can_send_code,
    delete_expired_codes,
    
    # Token 相关
    create_refresh_token,
    get_valid_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    revoke_token_by_hash,
    
    # 邀请码相关
    generate_unique_invite_code,
    
    # 兑换码相关
    get_redemption_code,
    use_redemption_code,
    
    # 邀请记录相关
    create_invite_record,
    get_invite_record,
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
    "User",
    "VerificationCode",
    "RefreshToken",
    "RedemptionCode",
    "TopupRecord",
    "InviteRecord",
    "Admin",
    "SchemaVersion",
    
    # CRUD - 用户
    "create_user",
    "get_user_by_email",
    "get_user_by_id",
    "get_user_by_invite_code",
    "update_user_usage_count",
    "update_last_login",
    "update_password",
    
    # CRUD - 验证码
    "create_verification_code",
    "get_valid_verification_code",
    "mark_code_as_used",
    "can_send_code",
    "delete_expired_codes",
    
    # CRUD - Token
    "create_refresh_token",
    "get_valid_refresh_token",
    "revoke_refresh_token",
    "revoke_all_user_tokens",
    "revoke_token_by_hash",
    
    # CRUD - 邀请码
    "generate_unique_invite_code",
    
    # CRUD - 兑换码
    "get_redemption_code",
    "use_redemption_code",
    
    # CRUD - 邀请记录
    "create_invite_record",
    "get_invite_record",
]