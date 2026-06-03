# -*- coding: utf-8 -*-
"""
支付渠道抽象基类

定义支付渠道的统一接口，支持微信、支付宝等支付方式的扩展。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class PaymentResult:
    """
    支付创建结果

    创建支付订单后返回的结果，包含支付二维码等信息。
    """
    success: bool
    order_no: str
    trade_no: Optional[str] = None
    qr_code_url: Optional[str] = None
    deep_link: Optional[str] = None  # App 深度链接
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "order_no": self.order_no,
            "trade_no": self.trade_no,
            "qr_code_url": self.qr_code_url,
            "deep_link": self.deep_link,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "extra": self.extra,
        }


@dataclass
class QueryResult:
    """
    支付查询结果

    查询支付订单状态后返回的结果。
    """
    success: bool
    order_no: str
    trade_no: Optional[str] = None
    status: str = "unknown"  # pending / paid / closed / refund
    paid_at: Optional[datetime] = None
    amount: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "order_no": self.order_no,
            "trade_no": self.trade_no,
            "status": self.status,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "amount": self.amount,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


@dataclass
class CallbackResult:
    """
    支付回调结果

    处理支付平台回调后返回的结果。
    """
    success: bool
    order_no: str
    trade_no: Optional[str] = None
    paid_at: Optional[datetime] = None
    amount: Optional[int] = None
    raw_data: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "order_no": self.order_no,
            "trade_no": self.trade_no,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "amount": self.amount,
            "raw_data": self.raw_data,
            "error_message": self.error_message,
        }


class PaymentChannel(ABC):
    """
    支付渠道抽象基类

    定义支付渠道的统一接口，所有支付方式（微信、支付宝等）都需要实现此接口。
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """
        渠道名称

        Returns:
            str: 渠道标识（如 wechat, alipay, mock）
        """
        pass

    @property
    @abstractmethod
    def channel_display_name(self) -> str:
        """
        渠道显示名称

        Returns:
            str: 用户可见的渠道名称（如"微信支付"、"支付宝"）
        """
        pass

    @property
    def is_available(self) -> bool:
        """
        渠道是否可用

        Returns:
            bool: 是否配置完成、可用
        """
        return True

    @abstractmethod
    async def create_payment(
        self,
        order_no: str,
        amount: int,
        description: str,
        **kwargs,
    ) -> PaymentResult:
        """
        创建支付订单

        Args:
            order_no: 商户订单号
            amount: 金额（分）
            description: 商品描述
            **kwargs: 额外参数

        Returns:
            PaymentResult: 支付创建结果
        """
        pass

    @abstractmethod
    async def query_payment(self, order_no: str) -> QueryResult:
        """
        查询支付状态

        Args:
            order_no: 商户订单号

        Returns:
            QueryResult: 支付查询结果
        """
        pass

    @abstractmethod
    async def handle_callback(self, data: Dict[str, Any]) -> CallbackResult:
        """
        处理支付回调

        Args:
            data: 回调数据

        Returns:
            CallbackResult: 回调处理结果
        """
        pass

    @abstractmethod
    async def close_payment(self, order_no: str) -> bool:
        """
        关闭支付订单

        Args:
            order_no: 商户订单号

        Returns:
            bool: 是否成功
        """
        pass

    async def refund_payment(
        self,
        order_no: str,
        refund_no: str,
        amount: int,
        reason: str = "",
    ) -> bool:
        """
        退款（可选实现）

        Args:
            order_no: 原订单号
            refund_no: 退款单号
            amount: 退款金额（分）
            reason: 退款原因

        Returns:
            bool: 是否成功
        """
        raise NotImplementedError("此支付渠道不支持退款")

    def generate_order_no(self, prefix: str = "PRISM") -> str:
        """
        生成订单号

        Args:
            prefix: 订单号前缀

        Returns:
            str: 订单号（格式：PREFIX-YYYYMMDD-XXXXXX）
        """
        import random
        import string
        from datetime import datetime

        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}-{date_str}-{random_str}"