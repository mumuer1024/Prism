# -*- coding: utf-8 -*-
"""
支付模块

提供在线支付功能的前置接口，支持：
- 微信支付（预留）
- 支付宝（预留）
- 模拟支付（开发测试）
"""

from src.payment.base import (
    PaymentChannel,
    PaymentResult,
    QueryResult,
    CallbackResult,
)
from src.payment.mock import MockPaymentChannel
from src.payment.wechat import WechatPaymentChannel
from src.payment.alipay import AlipayChannel
from src.payment.service import PaymentService, get_payment_service
from src.payment.router import router as payment_router

__all__ = [
    # 基类
    "PaymentChannel",
    "PaymentResult",
    "QueryResult",
    "CallbackResult",
    # 渠道
    "MockPaymentChannel",
    "WechatPaymentChannel",
    "AlipayChannel",
    # 服务
    "PaymentService",
    "get_payment_service",
    # 路由
    "payment_router",
]