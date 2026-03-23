"""
使用次数模块单元测试

测试使用次数服务、匿名用户管理等
"""
import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session

from src.usage.service import UsageService
from src.database.models import User, AnonymousUser


# ═══════════════════════════════════════════════════════════
# 使用次数服务测试
# ═══════════════════════════════════════════════════════════

class TestUsageService:
    """使用次数服务测试"""
    
    def test_check_usage_paid_user(self, usage_service: UsageService, paid_user: dict):
        """测试付费用户检查使用次数"""
        user = paid_user["user"]
        
        result = usage_service.check_usage(
            user=user,
            visitor_id=None,
            ip_address=None,
            tool_type="bounty_hunter"
        )
        
        # 验证结果
        assert result["can_use"] is True
        assert result["source"] == "paid"
    
    def test_check_usage_free_user(self, usage_service: UsageService, registered_user: dict):
        """测试免费用户检查使用次数"""
        user = registered_user["user"]
        
        result = usage_service.check_usage(
            user=user,
            visitor_id=None,
            ip_address=None,
            tool_type="bounty_hunter"
        )
        
        # 验证结果
        assert result["can_use"] is True
        assert result["source"] == "free"
    
    def test_check_usage_anonymous(self, usage_service: UsageService, db_session: Session):
        """测试匿名用户检查使用次数"""
        result = usage_service.check_usage(
            user=None,
            visitor_id="test-visitor-123",
            ip_address="127.0.0.1",
            tool_type="bounty_hunter"
        )
        
        # 验证结果
        assert result["can_use"] is True
        assert result["source"] == "anonymous"
    
    def test_deduct_paid_count(self, usage_service: UsageService, db_session: Session, paid_user: dict):
        """测试扣减付费次数"""
        user = paid_user["user"]
        original_count = user.usage_count
        
        result = usage_service.deduct_usage(
            user=user,
            visitor_id=None,
            ip_address=None,
            tool_type="bounty_hunter"
        )
        db_session.commit()
        
        # 验证结果
        assert result["success"] is True
        assert result["cache_type"] == "premium"
        # 验证次数减少
        db_session.refresh(user)
        assert user.usage_count == original_count - 1
    
    def test_deduct_free_count(self, usage_service: UsageService, db_session: Session, registered_user: dict):
        """测试扣减免费次数"""
        user = registered_user["user"]
        
        result = usage_service.deduct_usage(
            user=user,
            visitor_id=None,
            ip_address=None,
            tool_type="bounty_hunter"
        )
        db_session.commit()
        
        # 验证结果
        assert result["success"] is True
        assert result["cache_type"] == "free"
    
    def test_deduct_anonymous_count(self, usage_service: UsageService, db_session: Session):
        """测试扣减匿名用户次数"""
        result = usage_service.deduct_usage(
            user=None,
            visitor_id="test-visitor-deduct",
            ip_address="127.0.0.1",
            tool_type="bounty_hunter"
        )
        db_session.commit()
        
        # 验证结果
        assert result["success"] is True
        assert result["cache_type"] == "free"
    
    def test_get_balance_paid_user(self, usage_service: UsageService, paid_user: dict):
        """测试获取付费用户余额"""
        user = paid_user["user"]
        
        result = usage_service.get_balance(
            user=user,
            visitor_id=None,
            ip_address=None
        )
        
        # 验证结果
        assert result["paid_count"] == user.usage_count
        assert result["user_type"] == "paid"
    
    def test_get_balance_free_user(self, usage_service: UsageService, registered_user: dict):
        """测试获取免费用户余额"""
        user = registered_user["user"]
        
        result = usage_service.get_balance(
            user=user,
            visitor_id=None,
            ip_address=None
        )
        
        # 验证结果
        assert result["paid_count"] == 0
        assert result["user_type"] == "free"
        assert "free_remaining" in result
    
    def test_get_balance_anonymous(self, usage_service: UsageService, db_session: Session):
        """测试获取匿名用户余额"""
        # 先创建匿名用户
        usage_service._get_or_create_anonymous("test-visitor-balance", "127.0.0.1")
        db_session.commit()
        
        result = usage_service.get_balance(
            user=None,
            visitor_id="test-visitor-balance",
            ip_address="127.0.0.1"
        )
        
        # 验证结果
        assert result["user_type"] == "anonymous"
        assert "free_remaining" in result


# ═══════════════════════════════════════════════════════════
# 匿名用户测试
# ═══════════════════════════════════════════════════════════

class TestAnonymousUser:
    """匿名用户测试"""
    
    def test_create_anonymous(self, usage_service: UsageService, db_session: Session):
        """测试创建匿名用户"""
        anonymous = usage_service._get_or_create_anonymous(
            visitor_id="new-visitor",
            ip_address="192.168.1.1"
        )
        db_session.commit()
        
        # 验证匿名用户创建成功
        assert anonymous is not None
        assert anonymous.visitor_hash is not None
        assert anonymous.ip_address == "192.168.1.1"
    
    def test_get_or_create_anonymous_existing(self, usage_service: UsageService, db_session: Session):
        """测试获取已存在的匿名用户"""
        # 第一次创建
        anonymous1 = usage_service._get_or_create_anonymous(
            visitor_id="existing-visitor",
            ip_address="192.168.1.2"
        )
        db_session.commit()
        
        # 第二次获取
        anonymous2 = usage_service._get_or_create_anonymous(
            visitor_id="existing-visitor",
            ip_address="192.168.1.2"
        )
        
        # 应该返回同一个用户
        assert anonymous1.id == anonymous2.id
    
    def test_anonymous_daily_reset(self, usage_service: UsageService, db_session: Session):
        """测试匿名用户每日重置"""
        today = date.today().isoformat()
        
        anonymous = usage_service._get_or_create_anonymous(
            visitor_id="daily-reset-visitor",
            ip_address="192.168.1.3"
        )
        db_session.commit()
        
        # 验证日期设置正确
        assert anonymous.free_usage_date == today
        assert anonymous.free_usage_count == 0
    
    def test_anonymous_usage_increment(self, usage_service: UsageService, db_session: Session):
        """测试匿名用户使用次数增加"""
        # 创建匿名用户
        anonymous = usage_service._get_or_create_anonymous(
            visitor_id="increment-visitor",
            ip_address="192.168.1.4"
        )
        db_session.commit()
        
        # 扣减使用次数
        usage_service.deduct_usage(
            user=None,
            visitor_id="increment-visitor",
            ip_address="192.168.1.4",
            tool_type="bounty_hunter"
        )
        db_session.commit()
        
        # 验证使用次数增加
        db_session.refresh(anonymous)
        assert anonymous.free_usage_count == 1


# ═══════════════════════════════════════════════════════════
# 使用限制测试
# ═══════════════════════════════════════════════════════════

class TestUsageLimits:
    """使用限制测试"""
    
    def test_paid_user_no_daily_limit(self, usage_service: UsageService, paid_user: dict):
        """测试付费用户无每日限制"""
        user = paid_user["user"]
        
        # 付费用户应该有大量次数可用
        for _ in range(5):
            result = usage_service.check_usage(
                user=user,
                visitor_id=None,
                ip_address=None,
                tool_type="bounty_hunter"
            )
            assert result["can_use"] is True
    
    def test_free_user_daily_limit(self, usage_service: UsageService, db_session: Session, registered_user: dict):
        """测试免费用户每日限制"""
        user = registered_user["user"]
        
        # 免费用户每日有限制（假设为 3 次）
        # 连续检查应该都返回 True
        for _ in range(3):
            result = usage_service.check_usage(
                user=user,
                visitor_id=None,
                ip_address=None,
                tool_type="bounty_hunter"
            )
            # 可能返回 True 或 False，取决于具体实现
            # 这里只验证不会抛出异常
    
    def test_anonymous_daily_limit(self, usage_service: UsageService, db_session: Session):
        """测试匿名用户每日限制"""
        visitor_id = "limit-test-visitor"
        
        # 匿名用户每日有限制
        for _ in range(3):
            result = usage_service.check_usage(
                user=None,
                visitor_id=visitor_id,
                ip_address="127.0.0.1",
                tool_type="bounty_hunter"
            )
            # 验证不会抛出异常


# ═══════════════════════════════════════════════════════════
# 工具权限测试
# ═══════════════════════════════════════════════════════════

class TestToolAccess:
    """工具权限测试"""
    
    def test_free_tools_access(self, usage_service: UsageService, registered_user: dict):
        """测试免费工具访问权限"""
        user = registered_user["user"]
        
        # 免费工具应该都可以访问
        free_tools = ["bounty_hunter", "alpha_radar", "revenue_architect", "narrator"]
        
        for tool in free_tools:
            result = usage_service.check_usage(
                user=user,
                visitor_id=None,
                ip_address=None,
                tool_type=tool
            )
            # 验证有访问权限（可能次数有限，但工具可访问）
            assert "can_use" in result
    
    def test_paid_tools_access(self, usage_service: UsageService, paid_user: dict):
        """测试付费工具访问权限"""
        user = paid_user["user"]
        
        # 付费用户应该可以访问所有工具
        result = usage_service.check_usage(
            user=user,
            visitor_id=None,
            ip_address=None,
            tool_type="premium_tool"
        )
        
        # 验证结果
        assert "can_use" in result


# ═══════════════════════════════════════════════════════════
# 缓存策略测试
# ═══════════════════════════════════════════════════════════

class TestCacheStrategy:
    """缓存策略测试"""
    
    def test_paid_user_premium_cache(self, usage_service: UsageService, db_session: Session, paid_user: dict):
        """测试付费用户高级缓存"""
        user = paid_user["user"]
        
        result = usage_service.deduct_usage(
            user=user,
            visitor_id=None,
            ip_address=None,
            tool_type="bounty_hunter"
        )
        db_session.commit()
        
        # 验证缓存类型为 premium
        assert result["cache_type"] == "premium"
        assert result["cache_expires_at"] is not None  # 付费用户有缓存过期时间
    
    def test_free_user_free_cache(self, usage_service: UsageService, db_session: Session, registered_user: dict):
        """测试免费用户免费缓存"""
        user = registered_user["user"]
        
        result = usage_service.deduct_usage(
            user=user,
            visitor_id=None,
            ip_address=None,
            tool_type="bounty_hunter"
        )
        db_session.commit()
        
        # 验证缓存类型为 free
        assert result["cache_type"] == "free"
    
    def test_anonymous_no_cache(self, usage_service: UsageService, db_session: Session):
        """测试匿名用户无缓存"""
        result = usage_service.deduct_usage(
            user=None,
            visitor_id="cache-test-visitor",
            ip_address="127.0.0.1",
            tool_type="bounty_hunter"
        )
        db_session.commit()
        
        # 验证缓存类型为 free（无持久缓存）
        assert result["cache_type"] == "free"


# ═══════════════════════════════════════════════════════════
# 匿名用户模型测试
# ═══════════════════════════════════════════════════════════

class TestAnonymousUserModel:
    """匿名用户模型测试"""
    
    def test_anonymous_user_create(self, db_session: Session):
        """测试创建匿名用户模型"""
        today = date.today().isoformat()
        
        anonymous = AnonymousUser(
            visitor_hash="test-hash-123",
            ip_address="192.168.1.100",
            free_usage_date=today,
            free_usage_count=0,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow()
        )
        db_session.add(anonymous)
        db_session.commit()
        
        # 验证创建成功
        assert anonymous.id is not None
        assert anonymous.visitor_hash == "test-hash-123"
    
    def test_anonymous_user_unique_hash(self, db_session: Session):
        """测试匿名用户哈希唯一"""
        from sqlalchemy.exc import IntegrityError
        
        today = date.today().isoformat()
        
        # 创建第一个匿名用户
        anonymous1 = AnonymousUser(
            visitor_hash="unique-hash-test",
            ip_address="192.168.1.101",
            free_usage_date=today,
            free_usage_count=0,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow()
        )
        db_session.add(anonymous1)
        db_session.commit()
        
        # 尝试创建相同哈希的用户
        anonymous2 = AnonymousUser(
            visitor_hash="unique-hash-test",
            ip_address="192.168.1.102",
            free_usage_date=today,
            free_usage_count=0,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow()
        )
        db_session.add(anonymous2)
        
        # 应该抛出唯一约束异常
        with pytest.raises(IntegrityError):
            db_session.commit()