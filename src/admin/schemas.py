# -*- coding: utf-8 -*-
"""
管理员 API 数据模型

定义管理员相关 API 的请求和响应模型
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ==========================================
# 用户管理相关
# ==========================================

class UserListResponse(BaseModel):
    """用户列表响应"""
    id: int
    email: str
    nickname: Optional[str] = None
    usage_count: int = 0
    invite_code: Optional[str] = None
    is_active: bool = True
    is_banned: bool = False
    banned_at: Optional[datetime] = None
    banned_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListRequest(BaseModel):
    """用户列表请求参数"""
    page: int = Field(default=1, ge=1, description="页码")
    limit: int = Field(default=20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(default=None, description="搜索关键词（邮箱/昵称）")
    is_banned: Optional[bool] = Field(default=None, description="筛选封禁状态")


class UserDetailResponse(BaseModel):
    """用户详情响应"""
    id: int
    email: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    usage_count: int = 0
    invite_code: Optional[str] = None
    invited_by: Optional[int] = None
    has_redeemed_first: bool = False
    is_active: bool = True
    is_verified: bool = False
    is_banned: bool = False
    banned_at: Optional[datetime] = None
    banned_reason: Optional[str] = None
    oauth_provider: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    # 统计信息
    total_topup_count: int = 0
    total_bonus_count: int = 0
    invite_stats: Optional[dict] = None

    class Config:
        from_attributes = True


class BanUserRequest(BaseModel):
    """封禁用户请求"""
    reason: str = Field(default="违规操作", max_length=200, description="封禁原因")


class BanUserResponse(BaseModel):
    """封禁用户响应"""
    success: bool
    message: str
    user_id: int
    banned_at: datetime
    banned_reason: str


class UnbanUserResponse(BaseModel):
    """解禁用户响应"""
    success: bool
    message: str
    user_id: int


class UserStatsResponse(BaseModel):
    """用户统计响应"""
    total_users: int
    active_users: int
    banned_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int


class RevenueStatsResponse(BaseModel):
    """充值统计响应"""
    total_topup_count: int
    total_bonus_count: int
    total_codes_used: int
    total_codes_unused: int
    topup_records_today: int
    topup_records_this_week: int
    topup_records_this_month: int


# ==========================================
# 兑换码管理相关
# ==========================================

class GenerateCodesRequest(BaseModel):
    """批量生成兑换码请求"""
    count: int = Field(ge=1, le=1000, description="生成数量")
    usage_count: int = Field(ge=1, le=1000, description="每个兑换码的使用次数")
    expire_days: Optional[int] = Field(default=365, ge=1, description="有效期天数")
    note: Optional[str] = Field(default=None, max_length=200, description="备注")


class GenerateCodesResponse(BaseModel):
    """批量生成兑换码响应"""
    success: bool
    message: str
    batch_id: str
    codes: List[str]
    count: int
    usage_count_per_code: int
    expires_at: Optional[datetime] = None


class CodeListResponse(BaseModel):
    """兑换码列表响应"""
    id: int
    code: str
    count: int
    batch_id: str
    used: bool
    used_by: Optional[int] = None
    used_by_email: Optional[str] = None
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchListResponse(BaseModel):
    """批次列表响应"""
    batch_id: str
    total_codes: int
    used_codes: int
    unused_codes: int
    total_count: int
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class BatchDetailResponse(BaseModel):
    """批次详情响应"""
    batch_id: str
    description: Optional[str] = None
    total_codes: int
    used_codes: int
    unused_codes: int
    total_count: int
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    codes: List[CodeListResponse]


class ExportCodesResponse(BaseModel):
    """导出兑换码响应"""
    success: bool
    message: str
    batch_id: str
    export_url: Optional[str] = None
    codes: List[dict]


# ==========================================
# 批量操作相关
# ==========================================

class BatchBanRequest(BaseModel):
    """批量封禁请求"""
    user_ids: List[int] = Field(min_length=1, max_length=100, description="用户ID列表")
    reason: str = Field(default="违规操作", max_length=200, description="封禁原因")


class BatchBanResponse(BaseModel):
    """批量封禁响应"""
    success: bool
    message: str
    total: int
    succeeded: int
    failed: int
    failed_ids: List[int] = []
    details: List[dict] = []


# ==========================================
# 审计日志相关
# ==========================================

class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int
    admin_id: Optional[int] = None
    admin_email: str
    action: str
    action_category: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    target_info: Optional[dict] = None
    action_detail: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    limit: int


# 操作类型常量
class AuditAction:
    """审计操作类型常量"""
    # 用户管理
    BAN_USER = "ban_user"
    UNBAN_USER = "unban_user"
    BATCH_BAN_USERS = "batch_ban_users"
    VIEW_USER_DETAIL = "view_user_detail"

    # 兑换码管理
    GENERATE_CODES = "generate_codes"
    VIEW_BATCH = "view_batch"
    EXPORT_CODES = "export_codes"

    # 模板管理
    CREATE_TEMPLATE = "create_template"
    UPDATE_TEMPLATE = "update_template"
    DELETE_TEMPLATE = "delete_template"
    PUBLISH_TEMPLATE = "publish_template"


class AuditCategory:
    """审计操作分类常量"""
    USER_MANAGEMENT = "user_management"
    CODE_MANAGEMENT = "code_management"
    TEMPLATE_MANAGEMENT = "template_management"
    SYSTEM_CONFIG = "system_config"