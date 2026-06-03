# -*- coding: utf-8 -*-
"""
模拟支付渠道

用于开发和测试的模拟支付实现，不进行真实的支付操作。
"""

import json
import random
from datetime import datetime
from typing import Dict, Any

from src.payment.base import (
    PaymentChannel,
    PaymentResult,
    QueryResult,
    CallbackResult,
)


class MockPaymentChannel(PaymentChannel):
    """
    模拟支付渠道

    用于开发测试，模拟支付流程但不进行真实支付。
    """

    # 存储模拟订单状态（开发测试用）
    _mock_orders: Dict[str, Dict[str, Any]] = {}

    @property
    def channel_name(self) -> str:
        return "mock"

    @property
    def channel_display_name(self) -> str:
        return "模拟支付（测试）"

    @property
    def is_available(self) -> bool:
        # 模拟支付始终可用
        return True

    async def create_payment(
        self,
        order_no: str,
        amount: int,
        description: str,
        **kwargs,
    ) -> PaymentResult:
        """
        创建模拟支付订单

        返回模拟的支付二维码链接。
        """
        # 生成模拟交易号
        trade_no = f"MOCK{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

        # 存储模拟订单
        self._mock_orders[order_no] = {
            "trade_no": trade_no,
            "amount": amount,
            "description": description,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "paid_at": None,
        }

        # 返回模拟二维码
        qr_code_url = f"mock://pay/{order_no}?amount={amount}"

        return PaymentResult(
            success=True,
            order_no=order_no,
            trade_no=trade_no,
            qr_code_url=qr_code_url,
            deep_link=f"mockpay://pay?order={order_no}",
        )

    async def query_payment(self, order_no: str) -> QueryResult:
        """
        查询模拟支付状态
        """
        order = self._mock_orders.get(order_no)

        if not order:
            return QueryResult(
                success=False,
                order_no=order_no,
                error_code="ORDER_NOT_FOUND",
                error_message="订单不存在",
            )

        return QueryResult(
            success=True,
            order_no=order_no,
            trade_no=order["trade_no"],
            status=order["status"],
            paid_at=order.get("paid_at"),
            amount=order["amount"],
        )

    async def handle_callback(self, data: Dict[str, Any]) -> CallbackResult:
        """
        处理模拟回调

        接收模拟的回调数据，更新订单状态。
        """
        order_no = data.get("order_no")
        success = data.get("success", False)

        if not order_no:
            return CallbackResult(
                success=False,
                order_no="",
                error_message="缺少订单号",
            )

        order = self._mock_orders.get(order_no)
        if not order:
            return CallbackResult(
                success=False,
                order_no=order_no,
                error_message="订单不存在",
            )

        if success:
            order["status"] = "paid"
            order["paid_at"] = datetime.utcnow()
            return CallbackResult(
                success=True,
                order_no=order_no,
                trade_no=order["trade_no"],
                paid_at=order["paid_at"],
                amount=order["amount"],
                raw_data=json.dumps(data),
            )
        else:
            order["status"] = "failed"
            return CallbackResult(
                success=False,
                order_no=order_no,
                error_message="支付失败",
                raw_data=json.dumps(data),
            )

    async def close_payment(self, order_no: str) -> bool:
        """
        关闭模拟订单
        """
        order = self._mock_orders.get(order_no)
        if not order:
            return False

        if order["status"] == "pending":
            order["status"] = "closed"
            return True

        return False

    async def mock_pay(self, order_no: str) -> bool:
        """
        模拟支付成功

        用于测试，直接将订单标记为已支付。

        Args:
            order_no: 订单号

        Returns:
            bool: 是否成功
        """
        order = self._mock_orders.get(order_no)
        if not order:
            return False

        if order["status"] != "pending":
            return False

        order["status"] = "paid"
        order["paid_at"] = datetime.utcnow()
        return True

    def clear_mock_orders(self):
        """清空模拟订单（测试用）"""
        self._mock_orders.clear()