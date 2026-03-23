# -*- coding: utf-8 -*-
"""
使用次数 Schema

定义使用次数相关的请求和响应模型
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============== 请求模型 ==============

class UsageCheckRequest(BaseModel):
    """使用权限检查请求"""
    visitor_id: Optional[str] = Field(None, description="匿名用户设备指纹")
    tool_type: str = Field(..., description="工具类型")


class UsageDeductRequest(BaseModel):
    """使用次数扣减请求"""
    visitor_id: Optional[str] = Field(None, description="匿名用户设备指纹")
    tool_type: str = Field(..., description="工具类型")
    amount: int = Field(default=1, ge=1, le=10, description="扣减数量")


class AnonymousRegisterRequest(BaseModel):
    """匿名用户注册请求"""
    visitor_id: str = Field(..., min_length=16, max_length=128, description="设备指纹")


class UsageBalanceRequest(BaseModel):
    """使用次数余额查询请求"""
    visitor_id: Optional[str] = Field(None, description="匿名用户设备指纹")


# ============== 响应数据模型 ==============

class UsageCheckData(BaseModel):
    """使用权限检查结果"""
    can_use: bool = Field(..., description="是否可以使用")
    source: Optional[str] = Field(None, description="使用来源: paid/free/anonymous")
    remaining: int = Field(default=0, description="剩余次数")
    cache_type: Optional[str] = Field(None, description="缓存类型: premium/free")
    cache_hours: int = Field(default=0, description="缓存时长（小时）")
    message: Optional[str] = Field(None, description="提示信息")


class UsageDeductData(BaseModel):
    """使用次数扣减结果"""
    success: bool = Field(..., description="是否成功")
    source: Optional[str] = Field(None, description="使用来源")
    remaining: int = Field(default=0, description="剩余次数")
    cache_type: Optional[str] = Field(None, description="缓存类型")
    cache_expires_at: Optional[str] = Field(None, description="缓存过期时间")
    message: Optional[str] = Field(None, description="提示信息")


class UsageBalanceData(BaseModel):
    """使用次数余额数据"""
    user_type: str = Field(..., description="用户类型: paid/free/anonymous")
    paid_count: int = Field(default=0, description="付费次数余额")
    free_remaining: int = Field(default=0, description="今日剩余免费次数")
    free_limit: int = Field(default=3, description="每日免费上限")
    free_reset_at: Optional[str] = Field(None, description="免费次数重置时间")


class AnonymousRegisterData(BaseModel):
    """匿名用户注册结果"""
    anonymous_id: str = Field(..., description="匿名用户 ID")
    visitor_hash: str = Field(..., description="访客哈希")
    free_remaining: int = Field(default=3, description="剩余免费次数")


# ============== 响应模型 ==============

class UsageCheckResponse(BaseModel):
    """使用权限检查响应"""
    success: bool = True
    data: UsageCheckData


class UsageDeductResponse(BaseModel):
    """使用次数扣减响应"""
    success: bool = True
    message: str
    data: Optional[UsageDeductData] = None


class UsageBalanceResponse(BaseModel):
    """使用次数余额响应"""
    success: bool = True
    data: UsageBalanceData


class AnonymousRegisterResponse(BaseModel):
    """匿名用户注册响应"""
    success: bool = True
    message: str
    data: AnonymousRegisterData