# -*- coding: utf-8 -*-
"""
激活码模块 - Pydantic 模型

定义激活码相关的请求和响应模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field


# ==========================================
# 请求模型
# ==========================================

class ActivateRequest(BaseModel):
    """激活请求"""
    code: str = Field(..., description="激活码（PRISM-XXXX-XXXX-XXXX）")
    device_id: str = Field(..., description="设备 ID（crypto.randomUUID()）")
    device_name: Optional[str] = Field(None, description="设备名称（如 Chrome on Windows）")
    referral_code: Optional[str] = Field(None, description="推荐码（REF-XXXXXX）")


class StatusRequest(BaseModel):
    """状态查询请求"""
    device_id: str = Field(..., description="设备 ID")


class DeviceListRequest(BaseModel):
    """设备列表请求"""
    device_id: str = Field(..., description="设备 ID")


class DeviceDeleteRequest(BaseModel):
    """设备解绑请求"""
    device_id: str = Field(..., description="当前设备 ID（用于验证）")
    device_db_id: int = Field(..., description="要解绑的设备数据库 ID")


class ReferralRequest(BaseModel):
    """推荐码查询请求"""
    device_id: str = Field(..., description="设备 ID")


# ==========================================
# 响应数据模型
# ==========================================

class ActivationData(BaseModel):
    """激活成功数据"""
    code_id: int = Field(..., description="激活码 ID")
    code: str = Field(..., description="激活码")
    quota: int = Field(..., description="购买次数")
    remaining: int = Field(..., description="剩余次数")
    is_activated: bool = Field(..., description="是否已激活")
    referral_code: Optional[str] = Field(None, description="专属推荐码")
    device_count: int = Field(..., description="已绑定设备数量")
    device_limit: int = Field(default=3, description="设备数量上限")


class StatusData(BaseModel):
    """激活状态数据"""
    is_activated: bool = Field(..., description="是否已激活")
    code_id: Optional[int] = Field(None, description="激活码 ID")
    code: Optional[str] = Field(None, description="激活码")
    quota: Optional[int] = Field(None, description="购买次数")
    remaining: Optional[int] = Field(None, description="剩余次数")
    referral_code: Optional[str] = Field(None, description="专属推荐码")
    device_count: Optional[int] = Field(None, description="已绑定设备数量")
    referral_count: Optional[int] = Field(None, description="已推荐人数")
    total_rewarded: Optional[int] = Field(None, description="累计奖励次数")


class DeviceData(BaseModel):
    """设备信息"""
    id: int = Field(..., description="设备数据库 ID")
    device_id: str = Field(..., description="设备唯一 ID")
    device_name: Optional[str] = Field(None, description="设备名称")
    last_seen: Optional[str] = Field(None, description="最后活跃时间")
    created_at: str = Field(..., description="绑定时间")
    is_current: bool = Field(default=False, description="是否当前设备")


class DeviceListData(BaseModel):
    """设备列表数据"""
    devices: List[DeviceData] = Field(..., description="设备列表")
    total: int = Field(..., description="设备总数")
    limit: int = Field(default=3, description="设备上限")
    current_device_id: str = Field(..., description="当前设备 ID")


class ReferralData(BaseModel):
    """推荐码数据"""
    referral_code: str = Field(..., description="专属推荐码")
    referral_count: int = Field(..., description="已推荐人数")
    total_rewarded: int = Field(..., description="累计奖励次数")
    code_id: int = Field(..., description="关联激活码 ID")


class QuotaSpecData(BaseModel):
    """次数规格数据"""
    spec: str = Field(..., description="规格名称（S/M/L/XL/XXL/XXXL）")
    quota: int = Field(..., description="次数")


# ==========================================
# 响应模型
# ==========================================

class ActivateResponse(BaseModel):
    """激活响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="激活成功", description="消息")
    data: Optional[ActivationData] = Field(None, description="激活数据")


class StatusResponse(BaseModel):
    """状态响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[StatusData] = Field(None, description="状态数据")


class DeviceListResponse(BaseModel):
    """设备列表响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[DeviceListData] = Field(None, description="设备数据")


class DeviceDeleteResponse(BaseModel):
    """设备解绑响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="设备已解绑", description="消息")


class ReferralResponse(BaseModel):
    """推荐码响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[ReferralData] = Field(None, description="推荐码数据")


class QuotaSpecsResponse(BaseModel):
    """次数规格列表响应"""
    success: bool = Field(default=True, description="是否成功")
    data: List[QuotaSpecData] = Field(..., description="规格列表")


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(default=False, description="是否成功")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")