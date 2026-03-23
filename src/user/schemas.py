# src/user/schemas.py
"""
用户相关 Schema 定义
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== 用户信息相关 ==========

class UserProfileData(BaseModel):
    """用户信息数据"""
    id: int
    email: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    usage_count: int = 0
    invite_code: Optional[str] = None
    has_redeemed_first: bool = False
    is_verified: bool = False
    oauth_provider: Optional[str] = None
    oauth_name: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InviteStatsBrief(BaseModel):
    """邀请统计简要"""
    total_invited: int = 0
    active_invited: int = 0
    total_bonus: int = 0


class TopupRecordBrief(BaseModel):
    """充值记录简要"""
    id: int
    source: str
    count: int
    bonus_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """用户信息响应"""
    success: bool = True
    data: dict


# ========== 兑换相关 ==========

class RedeemRequest(BaseModel):
    """兑换请求"""
    code: str = Field(..., min_length=1, max_length=50, description="兑换码")


class RedeemData(BaseModel):
    """兑换结果数据"""
    count: int = Field(..., description="兑换码基础次数")
    bonus_count: int = Field(0, description="被邀请人赠送次数")
    total_count: int = Field(..., description="总获得次数")
    inviter_bonus: bool = Field(False, description="邀请人是否获得奖励")
    inviter_bonus_count: int = Field(0, description="邀请人获得奖励次数")


class RedeemResponse(BaseModel):
    """兑换响应"""
    success: bool = True
    message: str
    data: Optional[RedeemData] = None


# ========== 邀请统计相关 ==========

class InviteRecordBrief(BaseModel):
    """邀请记录简要"""
    invitee_id: int
    invitee_email: Optional[str] = None
    created_at: datetime
    bonus_given: bool = False
    bonus_count: int = 0
    bonus_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InviteStatsData(BaseModel):
    """邀请统计数据"""
    invite_code: Optional[str] = None
    total_invited: int = 0
    active_invited: int = 0
    total_bonus: int = 0
    invite_records: List[InviteRecordBrief] = []


class InviteStatsResponse(BaseModel):
    """邀请统计响应"""
    success: bool = True
    data: InviteStatsData


# ========== 通用响应 ==========

class UserOperationResponse(BaseModel):
    """用户操作通用响应"""
    success: bool = True
    message: str
    data: Optional[dict] = None