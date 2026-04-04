# -*- coding: utf-8 -*-
"""
支付服务

处理订单创建、查询、支付等业务逻辑。
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Type

from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.database.models import PaymentOrder, PaymentPackage, User, TopupRecord
from src.payment.base import PaymentChannel, PaymentResult
from src.payment.mock import MockPaymentChannel
from src.payment.wechat import WechatPaymentChannel
from src.payment.alipay import AlipayChannel

logger = logging.getLogger(__name__)


class PaymentService:
    """
    支付服务

    管理支付渠道、订单生命周期等。
    """

    # 订单过期时间（分钟）
    ORDER_EXPIRE_MINUTES = 30

    # 支付渠道注册表
    _channels: Dict[str, PaymentChannel] = {}

    def __init__(self):
        """初始化支付服务"""
        # 注册默认渠道
        self._register_default_channels()

    def _register_default_channels(self):
        """注册默认支付渠道"""
        # 模拟支付（始终可用）
        self.register_channel(MockPaymentChannel())

        # 微信支付（需要配置）
        # TODO: 从配置读取
        self.register_channel(WechatPaymentChannel())

        # 支付宝（需要配置）
        # TODO: 从配置读取
        self.register_channel(AlipayChannel())

    def register_channel(self, channel: PaymentChannel):
        """
        注册支付渠道

        Args:
            channel: 支付渠道实例
        """
        self._channels[channel.channel_name] = channel
        logger.info(f"注册支付渠道: {channel.channel_display_name} ({channel.channel_name})")

    def get_channel(self, channel_name: str) -> Optional[PaymentChannel]:
        """
        获取支付渠道

        Args:
            channel_name: 渠道名称

        Returns:
            PaymentChannel: 支付渠道实例，不存在则返回 None
        """
        return self._channels.get(channel_name)

    def get_available_channels(self) -> List[PaymentChannel]:
        """
        获取可用的支付渠道列表

        Returns:
            List[PaymentChannel]: 可用的支付渠道列表
        """
        return [ch for ch in self._channels.values() if ch.is_available]

    # ========================================================================
    # 套餐管理
    # ========================================================================

    def get_packages(self, db: Session) -> List[PaymentPackage]:
        """
        获取可用套餐列表

        Args:
            db: 数据库会话

        Returns:
            List[PaymentPackage]: 套餐列表
        """
        packages = db.query(PaymentPackage).filter(
            PaymentPackage.is_active == True
        ).order_by(PaymentPackage.sort_order).all()

        return packages

    def get_package(self, db: Session, package_id: int) -> Optional[PaymentPackage]:
        """
        获取套餐详情

        Args:
            db: 数据库会话
            package_id: 套餐 ID

        Returns:
            PaymentPackage: 套餐信息
        """
        return db.query(PaymentPackage).filter(
            PaymentPackage.id == package_id,
            PaymentPackage.is_active == True
        ).first()

    # ========================================================================
    # 订单管理
    # ========================================================================

    def create_order(
        self,
        db: Session,
        user_id: int,
        package_id: int,
        payment_method: str,
    ) -> Optional[PaymentOrder]:
        """
        创建支付订单

        Args:
            db: 数据库会话
            user_id: 用户 ID
            package_id: 套餐 ID
            payment_method: 支付方式

        Returns:
            PaymentOrder: 订单信息，失败返回 None
        """
        # 检查支付渠道
        channel = self.get_channel(payment_method)
        if not channel:
            logger.error(f"不支持的支付方式: {payment_method}")
            return None

        if not channel.is_available:
            logger.error(f"支付渠道不可用: {payment_method}")
            return None

        # 获取套餐
        package = self.get_package(db, package_id)
        if not package:
            logger.error(f"套餐不存在: {package_id}")
            return None

        # 生成订单号
        order_no = channel.generate_order_no("PRISM")

        # 计算过期时间
        expires_at = datetime.utcnow() + timedelta(minutes=self.ORDER_EXPIRE_MINUTES)

        # 创建订单
        order = PaymentOrder(
            user_id=user_id,
            order_no=order_no,
            amount=package.price,
            usage_count=package.usage_count,
            bonus_count=package.bonus_count,
            payment_method=payment_method,
            status="pending",
            expires_at=expires_at,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        logger.info(f"创建订单: {order_no}, 用户: {user_id}, 金额: {package.price}分")

        return order

    def get_order(self, db: Session, order_no: str) -> Optional[PaymentOrder]:
        """
        获取订单详情

        Args:
            db: 数据库会话
            order_no: 订单号

        Returns:
            PaymentOrder: 订单信息
        """
        return db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()

    def get_user_orders(
        self,
        db: Session,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[PaymentOrder]:
        """
        获取用户订单列表

        Args:
            db: 数据库会话
            user_id: 用户 ID
            status: 订单状态筛选
            limit: 返回数量限制

        Returns:
            List[PaymentOrder]: 订单列表
        """
        query = db.query(PaymentOrder).filter(
            PaymentOrder.user_id == user_id
        )

        if status:
            query = query.filter(PaymentOrder.status == status)

        orders = query.order_by(PaymentOrder.created_at.desc()).limit(limit).all()

        return orders

    # ========================================================================
    # 支付流程
    # ========================================================================

    async def initiate_payment(
        self,
        db: Session,
        order_no: str,
    ) -> Optional[PaymentResult]:
        """
        发起支付

        Args:
            db: 数据库会话
            order_no: 订单号

        Returns:
            PaymentResult: 支付结果
        """
        order = self.get_order(db, order_no)
        if not order:
            return PaymentResult(
                success=False,
                order_no=order_no,
                error_code="ORDER_NOT_FOUND",
                error_message="订单不存在",
            )

        # 检查订单状态
        if not order.is_pending():
            return PaymentResult(
                success=False,
                order_no=order_no,
                error_code="ORDER_STATUS_INVALID",
                error_message=f"订单状态异常: {order.status}",
            )

        # 检查是否过期
        if order.is_expired():
            order.status = "cancelled"
            db.commit()
            return PaymentResult(
                success=False,
                order_no=order_no,
                error_code="ORDER_EXPIRED",
                error_message="订单已过期",
            )

        # 获取支付渠道
        channel = self.get_channel(order.payment_method)
        if not channel or not channel.is_available:
            return PaymentResult(
                success=False,
                order_no=order_no,
                error_code="CHANNEL_UNAVAILABLE",
                error_message="支付渠道不可用",
            )

        # 调用支付渠道创建支付
        result = await channel.create_payment(
            order_no=order.order_no,
            amount=order.amount,
            description=f"Prism 次数充值 - {order.usage_count}次",
        )

        # 更新订单信息
        if result.success:
            order.trade_no = result.trade_no
            order.qr_code_url = result.qr_code_url
            db.commit()

        return result

    async def handle_payment_callback(
        self,
        db: Session,
        payment_method: str,
        callback_data: dict,
    ) -> bool:
        """
        处理支付回调

        Args:
            db: 数据库会话
            payment_method: 支付方式
            callback_data: 回调数据

        Returns:
            bool: 是否处理成功
        """
        channel = self.get_channel(payment_method)
        if not channel:
            logger.error(f"未知的支付渠道: {payment_method}")
            return False

        # 处理回调
        result = await channel.handle_callback(callback_data)

        if not result.success:
            logger.warning(f"支付回调处理失败: {result.error_message}")
            return False

        # 查询订单
        order = self.get_order(db, result.order_no)
        if not order:
            logger.error(f"回调订单不存在: {result.order_no}")
            return False

        # 检查订单状态
        if order.status != "pending":
            logger.warning(f"订单状态不是待支付: {order.order_no}, status={order.status}")
            return True  # 幂等处理

        # 更新订单状态
        order.status = "paid"
        order.trade_no = result.trade_no
        order.paid_at = result.paid_at or datetime.utcnow()
        order.callback_raw = result.raw_data
        order.callback_at = datetime.utcnow()

        # 充值次数
        user = db.query(User).filter(User.id == order.user_id).first()
        if user:
            total_count = order.usage_count + order.bonus_count
            user.usage_count += total_count

            # 创建充值记录
            topup_record = TopupRecord(
                user_id=user.id,
                source=payment_method,
                count=order.usage_count,
                bonus_count=order.bonus_count,
            )
            db.add(topup_record)

        db.commit()

        logger.info(f"支付成功: {order.order_no}, 用户: {order.user_id}, 次数: {order.usage_count}")

        return True

    async def mock_pay(self, db: Session, order_no: str) -> bool:
        """
        模拟支付（开发测试用）

        Args:
            db: 数据库会话
            order_no: 订单号

        Returns:
            bool: 是否成功
        """
        channel = self.get_channel("mock")
        if not channel:
            return False

        # 模拟支付
        mock_channel: MockPaymentChannel = channel
        success = await mock_channel.mock_pay(order_no)

        if not success:
            return False

        # 触发回调处理
        return await self.handle_payment_callback(
            db,
            "mock",
            {"order_no": order_no, "success": True}
        )

    async def close_order(self, db: Session, order_no: str) -> bool:
        """
        关闭订单

        Args:
            db: 数据库会话
            order_no: 订单号

        Returns:
            bool: 是否成功
        """
        order = self.get_order(db, order_no)
        if not order:
            return False

        if order.status != "pending":
            return False

        # 调用渠道关闭
        channel = self.get_channel(order.payment_method)
        if channel:
            await channel.close_payment(order_no)

        # 更新状态
        order.status = "cancelled"
        db.commit()

        return True


# 全局支付服务实例
_payment_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """获取支付服务实例"""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service