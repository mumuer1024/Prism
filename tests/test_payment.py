# -*- coding: utf-8 -*-
"""
支付模块测试

测试支付渠道、订单管理、API 端点等。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

import anyio

from src.payment.base import (
    PaymentChannel,
    PaymentResult,
    QueryResult,
    CallbackResult,
)
from src.payment.mock import MockPaymentChannel
from src.payment.wechat import WechatPaymentChannel
from src.payment.alipay import AlipayChannel
from src.payment.service import PaymentService


# ============================================================================
# 支付渠道基类测试
# ============================================================================

class TestPaymentResult:
    """PaymentResult 数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        result = PaymentResult(success=True, order_no="TEST001")

        assert result.success is True
        assert result.order_no == "TEST001"
        assert result.trade_no is None
        assert result.qr_code_url is None
        assert result.error_code is None
        assert result.error_message is None

    def test_to_dict(self):
        """测试转换为字典"""
        result = PaymentResult(
            success=True,
            order_no="TEST001",
            trade_no="TRADE001",
            qr_code_url="https://example.com/qr",
        )
        d = result.to_dict()

        assert d["success"] is True
        assert d["order_no"] == "TEST001"
        assert d["trade_no"] == "TRADE001"
        assert d["qr_code_url"] == "https://example.com/qr"


class TestQueryResult:
    """QueryResult 数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        result = QueryResult(success=True, order_no="TEST001")

        assert result.status == "unknown"
        assert result.paid_at is None

    def test_to_dict(self):
        """测试转换为字典"""
        result = QueryResult(
            success=True,
            order_no="TEST001",
            status="paid",
            amount=1000,
        )
        d = result.to_dict()

        assert d["status"] == "paid"
        assert d["amount"] == 1000


class TestCallbackResult:
    """CallbackResult 数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        result = CallbackResult(success=True, order_no="TEST001")

        assert result.trade_no is None
        assert result.paid_at is None
        assert result.raw_data is None


# ============================================================================
# 模拟支付渠道测试
# ============================================================================

class TestMockPaymentChannel:
    """模拟支付渠道测试"""

    @pytest.fixture
    def channel(self):
        return MockPaymentChannel()

    def test_channel_name(self, channel):
        """测试渠道名称"""
        assert channel.channel_name == "mock"
        assert "模拟" in channel.channel_display_name

    def test_is_available(self, channel):
        """测试渠道可用性"""
        assert channel.is_available is True

    @pytest.mark.anyio
    async def test_create_payment(self, channel):
        """测试创建支付"""
        result = await channel.create_payment(
            order_no="TEST001",
            amount=1000,
            description="测试订单",
        )

        assert result.success is True
        assert result.order_no == "TEST001"
        assert result.qr_code_url is not None
        assert "TEST001" in result.qr_code_url

    @pytest.mark.anyio
    async def test_query_payment(self, channel):
        """测试查询支付"""
        # 先创建订单
        await channel.create_payment("TEST001", 1000, "测试")

        # 查询
        result = await channel.query_payment("TEST001")

        assert result.success is True
        assert result.order_no == "TEST001"
        assert result.status == "pending"

    @pytest.mark.anyio
    async def test_query_nonexistent_order(self, channel):
        """测试查询不存在的订单"""
        result = await channel.query_payment("NOTEXIST")

        assert result.success is False
        assert result.error_code == "ORDER_NOT_FOUND"

    @pytest.mark.anyio
    async def test_handle_callback_success(self, channel):
        """测试成功回调"""
        # 先创建订单
        await channel.create_payment("TEST001", 1000, "测试")

        # 模拟回调
        result = await channel.handle_callback({
            "order_no": "TEST001",
            "success": True,
        })

        assert result.success is True
        assert result.order_no == "TEST001"

        # 验证状态已更新
        query = await channel.query_payment("TEST001")
        assert query.status == "paid"

    @pytest.mark.anyio
    async def test_handle_callback_failure(self, channel):
        """测试失败回调"""
        await channel.create_payment("TEST002", 1000, "测试")

        result = await channel.handle_callback({
            "order_no": "TEST002",
            "success": False,
        })

        assert result.success is False

        query = await channel.query_payment("TEST002")
        assert query.status == "failed"

    @pytest.mark.anyio
    async def test_close_payment(self, channel):
        """测试关闭订单"""
        await channel.create_payment("TEST003", 1000, "测试")

        success = await channel.close_payment("TEST003")
        assert success is True

        query = await channel.query_payment("TEST003")
        assert query.status == "closed"

    @pytest.mark.anyio
    async def test_mock_pay(self, channel):
        """测试模拟支付"""
        await channel.create_payment("TEST004", 1000, "测试")

        success = await channel.mock_pay("TEST004")
        assert success is True

        query = await channel.query_payment("TEST004")
        assert query.status == "paid"

    def test_generate_order_no(self, channel):
        """测试生成订单号"""
        order_no = channel.generate_order_no("PRISM")

        assert order_no.startswith("PRISM-")
        assert len(order_no) > 10


# ============================================================================
# 微信支付渠道测试
# ============================================================================

class TestWechatPaymentChannel:
    """微信支付渠道测试"""

    def test_channel_name(self):
        """测试渠道名称"""
        channel = WechatPaymentChannel()
        assert channel.channel_name == "wechat"

    def test_not_available_without_config(self):
        """测试未配置时不可用"""
        channel = WechatPaymentChannel()
        assert channel.is_available is False

    def test_available_with_config(self):
        """测试配置后可用"""
        channel = WechatPaymentChannel(
            app_id="test_app_id",
            mch_id="test_mch_id",
            api_key="test_api_key",
        )
        assert channel.is_available is True

    @pytest.mark.anyio
    async def test_create_payment_not_configured(self):
        """测试未配置时创建支付"""
        channel = WechatPaymentChannel()
        result = await channel.create_payment("TEST001", 1000, "测试")

        assert result.success is False
        assert result.error_code == "CHANNEL_NOT_CONFIGURED"


# ============================================================================
# 支付宝渠道测试
# ============================================================================

class TestAlipayChannel:
    """支付宝渠道测试"""

    def test_channel_name(self):
        """测试渠道名称"""
        channel = AlipayChannel()
        assert channel.channel_name == "alipay"

    def test_not_available_without_config(self):
        """测试未配置时不可用"""
        channel = AlipayChannel()
        assert channel.is_available is False


# ============================================================================
# 支付服务测试
# ============================================================================

class TestPaymentService:
    """支付服务测试"""

    @pytest.fixture
    def service(self):
        return PaymentService()

    def test_service_initialization(self, service):
        """测试服务初始化"""
        assert service is not None

    def test_get_channel(self, service):
        """测试获取渠道"""
        mock_channel = service.get_channel("mock")
        assert mock_channel is not None
        assert mock_channel.channel_name == "mock"

    def test_get_nonexistent_channel(self, service):
        """测试获取不存在的渠道"""
        channel = service.get_channel("nonexistent")
        assert channel is None

    def test_get_available_channels(self, service):
        """测试获取可用渠道"""
        channels = service.get_available_channels()

        # 模拟支付应该始终可用
        assert any(ch.channel_name == "mock" for ch in channels)

    def test_register_channel(self, service):
        """测试注册渠道"""
        custom_channel = MockPaymentChannel()
        custom_channel._channel_name = "custom"

        # 修改 channel_name 属性
        type(custom_channel).channel_name = property(lambda self: "custom")

        service.register_channel(custom_channel)

        channel = service.get_channel("custom")
        assert channel is not None


# ============================================================================
# 订单号生成测试
# ============================================================================

class TestOrderNoGeneration:
    """订单号生成测试"""

    def test_order_no_format(self):
        """测试订单号格式"""
        channel = MockPaymentChannel()
        order_no = channel.generate_order_no("PRISM")

        # 格式: PRISM-YYYYMMDD-XXXXXX
        parts = order_no.split("-")
        assert len(parts) == 3
        assert parts[0] == "PRISM"
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # XXXXXX

    def test_order_no_uniqueness(self):
        """测试订单号唯一性"""
        channel = MockPaymentChannel()
        order_nos = [channel.generate_order_no() for _ in range(100)]

        # 检查唯一性
        assert len(set(order_nos)) == 100


# ============================================================================
# 数据模型测试
# ============================================================================

class TestPaymentOrderModel:
    """PaymentOrder 模型测试"""

    def test_is_pending(self):
        """测试待支付状态"""
        from src.database.models import PaymentOrder

        order = PaymentOrder(
            order_no="TEST001",
            user_id=1,
            amount=1000,
            usage_count=10,
            payment_method="mock",
            status="pending",
        )

        assert order.is_pending() is True
        assert order.is_paid() is False

    def test_is_paid(self):
        """测试已支付状态"""
        from src.database.models import PaymentOrder

        order = PaymentOrder(
            order_no="TEST001",
            user_id=1,
            amount=1000,
            usage_count=10,
            payment_method="mock",
            status="paid",
        )

        assert order.is_pending() is False
        assert order.is_paid() is True

    def test_is_expired(self):
        """测试过期状态"""
        from src.database.models import PaymentOrder

        # 已过期
        order1 = PaymentOrder(
            order_no="TEST001",
            user_id=1,
            amount=1000,
            usage_count=10,
            payment_method="mock",
            status="pending",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert order1.is_expired() is True

        # 未过期
        order2 = PaymentOrder(
            order_no="TEST002",
            user_id=1,
            amount=1000,
            usage_count=10,
            payment_method="mock",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert order2.is_expired() is False

    def test_to_dict(self):
        """测试转换为字典"""
        from src.database.models import PaymentOrder

        order = PaymentOrder(
            id=1,
            order_no="TEST001",
            user_id=1,
            amount=1000,
            usage_count=10,
            bonus_count=2,
            payment_method="mock",
            status="pending",
        )

        d = order.to_dict()

        assert d["order_no"] == "TEST001"
        assert d["amount"] == 1000
        assert d["amount_yuan"] == 10.0
        assert d["usage_count"] == 10
        assert d["bonus_count"] == 2


class TestPaymentPackageModel:
    """PaymentPackage 模型测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        from src.database.models import PaymentPackage

        package = PaymentPackage(
            id=1,
            name="基础套餐",
            description="10次使用",
            usage_count=10,
            price=1000,
            bonus_count=2,
            is_recommended=True,
        )

        d = package.to_dict()

        assert d["name"] == "基础套餐"
        assert d["usage_count"] == 10
        assert d["total_count"] == 12  # 10 + 2
        assert d["price"] == 1000
        assert d["price_yuan"] == 10.0
        assert d["is_recommended"] is True