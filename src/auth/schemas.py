"""
认证模块 Pydantic 数据模型

定义请求和响应的数据结构
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import re


# ============================================================
# 基础响应模型
# ============================================================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: str
    message: str


# ============================================================
# 验证码相关
# ============================================================

class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    email: EmailStr = Field(..., description="邮箱地址")
    purpose: str = Field(default="register", description="用途: register, reset_password")
    
    @validator('purpose')
    def validate_purpose(cls, v):
        if v not in ['register', 'reset_password']:
            raise ValueError('purpose 必须是 register 或 reset_password')
        return v


class SendCodeResponse(BaseModel):
    """发送验证码响应"""
    success: bool = True
    message: str = "验证码已发送，请查收邮件"


# ============================================================
# 注册相关
# ============================================================

class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=64, description="密码")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")
    invite_code: Optional[str] = Field(None, description="邀请码（可选）")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少需要 8 个字符')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码需要包含至少一个字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密码需要包含至少一个数字')
        return v
    
    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('验证码必须是 6 位数字')
        return v


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    email: str
    usage_count: int = 0
    invite_code: Optional[str] = None
    has_redeemed_first: bool = False
    created_at: Optional[datetime] = None
    oauth_provider: Optional[str] = None


class TokenData(BaseModel):
    """Token 数据"""
    access_token: str
    refresh_token: str
    expires_in: int = 7200  # 秒
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    """注册响应"""
    success: bool = True
    data: dict  # 包含 user 和 token 信息


# ============================================================
# 登录相关
# ============================================================

class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool = True
    data: dict  # 包含 user 和 token 信息


# ============================================================
# Token 刷新
# ============================================================

class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str = Field(..., description="Refresh Token")


class RefreshTokenResponse(BaseModel):
    """刷新 Token 响应"""
    success: bool = True
    data: TokenData


# ============================================================
# 密码重置
# ============================================================

class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    email: EmailStr = Field(..., description="邮箱地址")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")
    new_password: str = Field(..., min_length=8, max_length=64, description="新密码")
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少需要 8 个字符')
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('密码需要包含至少一个字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密码需要包含至少一个数字')
        return v


class ResetPasswordResponse(BaseModel):
    """重置密码响应"""
    success: bool = True
    message: str = "密码重置成功，请重新登录"


class LogoutResponse(BaseModel):
    """登出响应"""
    success: bool = True
    message: str = "已成功登出"


# ============================================================
# 用户信息
# ============================================================

class UserProfileResponse(BaseModel):
    """用户信息响应"""
    success: bool = True
    data: UserInfo


class UpdateProfileRequest(BaseModel):
    """更新用户信息请求"""
    # 目前暂无可更新的字段，预留扩展
    pass


# ============================================================
# 使用次数
# ============================================================

class UsageResponse(BaseModel):
    """使用次数响应"""
    success: bool = True
    data: dict


class DeductUsageRequest(BaseModel):
    """扣减使用次数请求"""
    count: int = Field(default=1, ge=1, description="扣减次数")


class DeductUsageResponse(BaseModel):
    """扣减使用次数响应"""
    success: bool = True
    data: dict


# ============================================================
# 兑换码相关
# ============================================================

class RedeemCodeRequest(BaseModel):
    """兑换码充值请求"""
    code: str = Field(..., description="兑换码")


class RedeemCodeResponse(BaseModel):
    """兑换码充值响应"""
    success: bool = True
    data: dict


# ============================================================
# 邀请统计
# ============================================================

class InviteeInfo(BaseModel):
    """被邀请人信息"""
    email: str  # 脱敏后的邮箱
    invited_at: datetime
    has_redeemed: bool
    bonus_given: bool


class InviteStatsResponse(BaseModel):
    """邀请统计响应"""
    success: bool = True
    data: dict


# ============================================================
# 免费用户相关
# ============================================================

class FreeCheckResponse(BaseModel):
    """免费使用检查响应"""
    success: bool = True
    data: dict


class FreeUseRequest(BaseModel):
    """免费使用记录请求"""
    client_id: str = Field(..., description="客户端唯一标识")
    tool: str = Field(..., description="使用的工具")


class FreeUseResponse(BaseModel):
    """免费使用记录响应"""
    success: bool = True
    data: dict


# ============================================================
# OAuth 相关
# ============================================================

class OAuthAuthorizeResponse(BaseModel):
    """OAuth 授权 URL 响应"""
    success: bool = True
    data: dict  # 包含 authorize_url 和 state


class OAuthCallbackData(BaseModel):
    """OAuth 回调数据"""
    user: dict
    access_token: str
    refresh_token: str
    expires_in: int = 7200
    is_new_user: bool = False


class OAuthCallbackResponse(BaseModel):
    """OAuth 回调响应"""
    success: bool = True
    data: OAuthCallbackData


class OAuthProvidersResponse(BaseModel):
    """可用 OAuth 提供商响应"""
    success: bool = True
    data: dict  # 包含 providers 列表


class OAuthLinkResponse(BaseModel):
    """OAuth 绑定响应"""
    success: bool = True
    message: str = "账号绑定成功"