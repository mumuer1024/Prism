# -*- coding: utf-8 -*-
"""
支付宝支付渠道

预留接口，后续接入支付宝时实现。
"""

from datetime import datetime
from typing import Dict, Any

from src.payment.base import (
    PaymentChannel,
    PaymentResult,
    QueryResult,
    CallbackResult,
)


class AlipayChannel(PaymentChannel):
    """
    支付宝支付渠道

    预留接口，后续接入支付宝时实现。
    当前返回不可用状态。
    """

    def __init__(
        self,
        app_id: str = "",
        private_key: str = "",
        alipay_public_key: str = "",
    ):
        """
        初始化支付宝渠道

        Args:
            app_id: 支付宝应用 ID
            private_key: 应用私钥
            alipay_public_key: 支付宝公钥
        """
        self.app_id = app_id
        self.private_key = private_key
        self.alipay_public_key = alipay_public_key

    @property
    def channel_name(self) -> str:
        return "alipay"

    @property
    def channel_display_name(self) -> str:
        return "支付宝"

    @property
    def is_available(self) -> bool:
        # 需要配置完成才可用
        return bool(self.app_id and self.private_key and self.alipay_public_key)

    async def create_payment(
        self,
        order_no: str,
        amount: int,
        description: str,
        **kwargs,
    ) -> PaymentResult:
        """
        创建支付宝订单

        TODO: 接入支付宝当面付或电脑网站支付 API
        """
        if not self.is_available:
            return PaymentResult(
                success=False,
                order_no=order_no,
                error_code="CHANNEL_NOT_CONFIGURED",
                error_message="支付宝未配置，请联系管理员",
            )

        # TODO: 调用支付宝 API
        # 当前返回模拟数据
        return PaymentResult(
            success=False,
            order_no=order_no,
            error_code="NOT_IMPLEMENTED",
            error_message="支付宝功能即将上线，敬请期待",
        )

    async def query_payment(self, order_no: str) -> QueryResult:
        """
        查询支付宝订单状态

        TODO: 接入支付宝订单查询 API
        """
        if not self.is_available:
            return QueryResult(
                success=False,
                order_no=order_no,
                error_code="CHANNEL_NOT_CONFIGURED",
                error_message="支付宝未配置",
            )

        # TODO: 调用支付宝查询 API
        return QueryResult(
            success=False,
            order_no=order_no,
            error_code="NOT_IMPLEMENTED",
            error_message="支付宝功能即将上线",
        )

    async def handle_callback(self, data: Dict[str, Any]) -> CallbackResult:
        """
        处理支付宝回调

        TODO: 实现支付宝回调验签和处理
        """
        # TODO: 验证签名
        # TODO: 解析回调数据
        return CallbackResult(
            success=False,
            order_no="",
            error_message="支付宝功能即将上线",
        )

    async def close_payment(self, order_no: str) -> bool:
        """
        关闭支付宝订单

        TODO: 接入支付宝订单关闭 API
        """
        if not self.is_available:
            return False

        # TODO: 调用支付宝关闭订单 API
        return False

    async def refund_payment(
        self,
        order_no: str,
        refund_no: str,
        amount: int,
        reason: str = "",
    ) -> bool:
        """
        支付宝退款

        TODO: 接入支付宝退款 API
        """
        if not self.is_available:
            return False

        # TODO: 调用支付宝退款 API
        return False