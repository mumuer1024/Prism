# -*- coding: utf-8 -*-
"""
使用次数模块 - Pydantic 模型（激活码架构）

定义使用次数相关的请求和响应模型
"""

from typing import Optional
from pydantic import BaseModel, Field


# ==========================================
# 请求模型
# ==========================================

class UsageBalanceRequest(BaseModel):
    """次数余额查询请求"""
    device_id: Optional[str] = Field(None, description="设备 ID（已激活用户）")
    visitor_id: Optional[str] = Field(None, description="访客 ID（匿名用户）")


class UsageConsumeRequest(BaseModel):
    """次数消费请求"""
    device_id: Optional[str] = Field(None, description="设备 ID（已激活用户）")
    visitor_id: Optional[str] = Field(None, description="访客 ID（匿名用户）")
    tool_type: Optional[str] = Field(None, description="工具类型")
    amount: int = Field(default=1, ge=1, description="消费次数")


class UsageCheckRequest(BaseModel):
    """使用权限检查请求"""
    device_id: Optional[str] = Field(None, description="设备 ID（已激活用户）")
    visitor_id: Optional[str] = Field(None, description="访客 ID（匿名用户）")
    tool_type: Optional[str] = Field(None, description="工具类型")


# ==========================================
# 响应数据模型
# ==========================================

class UsageBalanceData(BaseModel):
    """次数余额数据"""
    user_type: str = Field(..., description="用户类型：activated / anonymous")
    paid_remaining: int = Field(default=0, description="付费次数剩余")
    free_remaining: int = Field(default=0, description="今日免费次数剩余")
    free_limit: int = Field(default=3, description="每日免费限额")
    free_reset_at: Optional[str] = Field(None, description="免费次数重置时间")
    referral_code: Optional[str] = Field(None, description="推荐码（已激活用户）")
    referral_count: Optional[int] = Field(None, description="已推荐人数")


class UsageConsumeData(BaseModel):
    """次数消费数据"""
    success: bool = Field(..., description="是否成功")
    source: str = Field(..., description="来源：paid / free")
    remaining: int = Field(..., description="剩余次数")
    referral_rewarded: bool = Field(default=False, description="是否触发推荐奖励")
    referral_bonus: int = Field(default=0, description="推荐奖励次数")


class UsageCheckData(BaseModel):
    """使用权限检查数据"""
    can_use: bool = Field(..., description="是否可以使用")
    source: Optional[str] = Field(None, description="来源：paid / free")
    remaining: int = Field(default=0, description="剩余次数")


class UsageConfigData(BaseModel):
    """使用配置数据"""
    free_daily_limit: int = Field(default=3, description="每日免费限额")
    referral_bonus_count: int = Field(default=3, description="推荐奖励次数")
    device_limit: int = Field(default=3, description="设备数量上限")


# ==========================================
# 响应模型
# ==========================================

class UsageBalanceResponse(BaseModel):
    """次数余额响应"""
    success: bool = Field(default=True, description="是否成功")
    data: UsageBalanceData = Field(..., description="余额数据")


class UsageConsumeResponse(BaseModel):
    """次数消费响应"""
    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="消费成功", description="消息")
    data: UsageConsumeData = Field(..., description="消费数据")


class UsageCheckResponse(BaseModel):
    """使用权限检查响应"""
    success: bool = Field(default=True, description="是否成功")
    data: UsageCheckData = Field(..., description="检查数据")


class UsageConfigResponse(BaseModel):
    """使用配置响应"""
    success: bool = Field(default=True, description="是否成功")
    data: UsageConfigData = Field(..., description="配置数据")