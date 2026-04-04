# -*- coding: utf-8 -*-
"""
微信支付渠道

预留接口，后续接入微信支付时实现。
"""

from datetime import datetime
from typing import Dict, Any

from src.payment.base import (
    PaymentChannel,
    PaymentResult,
    QueryResult,
    CallbackResult,
)


class WechatPaymentChannel(PaymentChannel):
    """
    微信支付渠道

    预留接口，后续接入微信支付时实现。
    当前返回不可用状态。
    """

    def __init__(self, app_id: str = "", mch_id: str = "", api_key: str = ""):
        """
        初始化微信支付渠道

        Args:
            app_id: 微信公众号/小程序 AppID
            mch_id: 商户号
            api_key: API 密钥
        """
        self.app_id = app_id
        self.mch_id = mch_id
        self.api_key = api_key

    @property
    def channel_name(self) -> str:
        return "wechat"

    @property
    def channel_display_name(self) -> str:
        return "微信支付"

    @property
    def is_available(self) -> bool:
        # 需要配置完成才可用
        return bool(self.app_id and self.mch_id and self.api_key)

    async def create_payment(
        self,
        order_no: str,
        amount: int,
        description: str,
        **kwargs,
    ) -> PaymentResult:
        """
        创建微信支付订单

        TODO: 接入微信支付 Native Pay API
        """
        if not self.is_available:
            return PaymentResult(
                success=False,
                order_no=order_no,
                error_code="CHANNEL_NOT_CONFIGURED",
                error_message="微信支付未配置，请联系管理员",
            )

        # TODO: 调用微信支付 API
        # 当前返回模拟数据
        return PaymentResult(
            success=False,
            order_no=order_no,
            error_code="NOT_IMPLEMENTED",
            error_message="微信支付功能即将上线，敬请期待",
        )

    async def query_payment(self, order_no: str) -> QueryResult:
        """
        查询微信支付订单状态

        TODO: 接入微信支付订单查询 API
        """
        if not self.is_available:
            return QueryResult(
                success=False,
                order_no=order_no,
                error_code="CHANNEL_NOT_CONFIGURED",
                error_message="微信支付未配置",
            )

        # TODO: 调用微信支付查询 API
        return QueryResult(
            success=False,
            order_no=order_no,
            error_code="NOT_IMPLEMENTED",
            error_message="微信支付功能即将上线",
        )

    async def handle_callback(self, data: Dict[str, Any]) -> CallbackResult:
        """
        处理微信支付回调

        TODO: 实现微信支付回调验签和处理
        """
        # TODO: 验证签名
        # TODO: 解析回调数据
        return CallbackResult(
            success=False,
            order_no="",
            error_message="微信支付功能即将上线",
        )

    async def close_payment(self, order_no: str) -> bool:
        """
        关闭微信支付订单

        TODO: 接入微信支付订单关闭 API
        """
        if not self.is_available:
            return False

        # TODO: 调用微信支付关闭订单 API
        return False

    async def refund_payment(
        self,
        order_no: str,
        refund_no: str,
        amount: int,
        reason: str = "",
    ) -> bool:
        """
        微信退款

        TODO: 接入微信退款 API
        """
        if not self.is_available:
            return False

        # TODO: 调用微信退款 API
        return False