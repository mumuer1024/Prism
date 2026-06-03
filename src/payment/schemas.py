# -*- coding: utf-8 -*-
"""
支付模块 Pydantic 模型

定义支付相关的请求和响应模型。
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# 套餐相关
# ============================================================================

class PackageResponse(BaseModel):
    """套餐响应"""
    id: int
    name: str
    description: Optional[str] = None
    usage_count: int
    total_count: int
    price: int
    price_yuan: float
    bonus_count: int = 0
    is_recommended: bool = False

    class Config:
        from_attributes = True


class PackageListResponse(BaseModel):
    """套餐列表响应"""
    packages: List[PackageResponse]


# ============================================================================
# 订单相关
# ============================================================================

class OrderCreateRequest(BaseModel):
    """创建订单请求"""
    package_id: int = Field(..., description="套餐 ID")
    payment_method: str = Field(..., description="支付方式: wechat / alipay / mock")


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    order_no: str
    amount: int
    amount_yuan: float
    usage_count: int
    bonus_count: int = 0
    payment_method: str
    status: str
    trade_no: Optional[str] = None
    qr_code_url: Optional[str] = None
    paid_at: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """订单列表响应"""
    orders: List[OrderResponse]
    total: int


class OrderStatusResponse(BaseModel):
    """订单状态响应"""
    order_no: str
    status: str
    is_paid: bool
    paid_at: Optional[str] = None
    usage_count: int = 0
    message: str = ""


# ============================================================================
# 支付相关
# ============================================================================

class PaymentCreateResponse(BaseModel):
    """创建支付响应"""
    success: bool
    order_no: str
    qr_code_url: Optional[str] = None
    deep_link: Optional[str] = None
    message: str = ""


class MockPayRequest(BaseModel):
    """模拟支付请求（开发测试用）"""
    order_no: str = Field(..., description="订单号")


class MockPayResponse(BaseModel):
    """模拟支付响应"""
    success: bool
    order_no: str
    message: str


# ============================================================================
# 回调相关
# ============================================================================

class CallbackResponse(BaseModel):
    """回调响应"""
    success: bool
    message: str = ""


# ============================================================================
# 通用响应
# ============================================================================

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True