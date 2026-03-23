"""
用户模块单元测试

测试用户服务、兑换码服务、邀请服务等
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
import secrets

from src.user.service import UserService
from src.auth.service import AuthService
from src.database.models import User, RedemptionCode, InviteRecord
from src.auth.utils.password_handler import hash_password


# ═══════════════════════════════════════════════════════════
# 用户服务测试
# ═══════════════════════════════════════════════════════════

class TestUserService:
    """用户服务测试"""

    @pytest.mark.asyncio
    async def test_get_user_profile(self, user_service: UserService, registered_user: dict):
        """测试获取用户信息"""
        user = registered_user["user"]

        profile = await user_service.get_user_profile(user)

        # 验证返回的用户信息
        assert profile is not None
        assert profile["success"] is True
        assert profile["data"]["user"]["email"] == user.email

    @pytest.mark.asyncio
    async def test_get_user_usage(self, user_service: UserService, registered_user: dict):
        """测试获取用户使用次数"""
        user = registered_user["user"]

        usage = await user_service.get_user_usage(user)

        # 验证返回的使用次数信息
        assert usage is not None
        assert usage["success"] is True
        assert "usage_count" in usage["data"]


# ═══════════════════════════════════════════════════════════
# 兑换码服务测试
# ═══════════════════════════════════════════════════════════

class TestRedemptionService:
    """兑换码服务测试"""

    @pytest.mark.asyncio
    async def test_redeem_code_success(self, user_service: UserService, db_session: Session, registered_user: dict, redemption_code: str):
        """测试兑换码兑换成功"""
        user = registered_user["user"]
        original_count = user.usage_count

        result = await user_service.redeem_code(user, redemption_code)
        db_session.commit()

        # 验证兑换结果
        assert result["success"] is True
        assert result["data"]["count"] > 0

    @pytest.mark.asyncio
    async def test_redeem_code_already_used(self, user_service: UserService, db_session: Session, registered_user: dict):
        """测试使用已使用的兑换码"""
        user = registered_user["user"]

        # 创建已使用的兑换码
        used_code = RedemptionCode(
            code="PRISM-USED123",
            count=10,
            used=True,
            used_by=user.id,
            used_at=datetime.utcnow(),
            batch_id="TEST",
            created_at=datetime.utcnow()
        )
        db_session.add(used_code)
        db_session.commit()

        # 尝试兑换
        result = await user_service.redeem_code(user, "PRISM-USED123")

        # 应该失败
        assert result["success"] is False
        assert "已" in result["message"] or "used" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_redeem_code_invalid(self, user_service: UserService, registered_user: dict):
        """测试无效兑换码"""
        user = registered_user["user"]

        result = await user_service.redeem_code(user, "INVALID-CODE")

        # 应该失败
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_redeem_code_empty(self, user_service: UserService, registered_user: dict):
        """测试空兑换码"""
        user = registered_user["user"]

        result = await user_service.redeem_code(user, "")

        # 应该失败
        assert result["success"] is False


# ═══════════════════════════════════════════════════════════
# 邀请服务测试
# ═══════════════════════════════════════════════════════════

class TestInviteService:
    """邀请服务测试"""

    @pytest.mark.asyncio
    async def test_get_invite_statistics(self, user_service: UserService, registered_user: dict):
        """测试获取邀请统计"""
        user = registered_user["user"]

        stats = await user_service.get_invite_statistics(user)

        # 验证统计数据
        assert stats is not None
        assert stats["success"] is True
        assert "invite_code" in stats["data"]
        assert "total_invited" in stats["data"]

    def test_user_has_invite_code(self, registered_user: dict):
        """测试用户有邀请码"""
        user = registered_user["user"]

        # 验证用户有邀请码
        assert user.invite_code is not None
        assert len(user.invite_code) > 0


# ═══════════════════════════════════════════════════════════
# 用户状态测试
# ═══════════════════════════════════════════════════════════

class TestUserStatus:
    """用户状态测试"""

    def test_user_usage_count_default(self, registered_user: dict):
        """测试用户默认使用次数"""
        user = registered_user["user"]

        assert user.usage_count == 0

    def test_user_is_active_default(self, registered_user: dict):
        """测试用户默认是激活状态"""
        user = registered_user["user"]

        assert user.is_active is True

    def test_user_is_verified_default(self, registered_user: dict):
        """测试用户默认未验证"""
        user = registered_user["user"]

        assert user.is_verified is False


# ═══════════════════════════════════════════════════════════
# 用户模型测试
# ═══════════════════════════════════════════════════════════

class TestUserModel:
    """用户模型测试"""

    def test_user_create(self, db_session: Session):
        """测试创建用户"""
        invite_code = "TEST-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        
        user = User(
            email="model@example.com",
            password_hash=hash_password("Password123!"),
            nickname="ModelUser",
            invite_code=invite_code,
            usage_count=0,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 验证用户创建成功
        assert user.id is not None
        assert user.email == "model@example.com"

    def test_user_email_unique(self, db_session: Session):
        """测试邮箱唯一约束"""
        from sqlalchemy.exc import IntegrityError
        
        invite_code1 = "TEST-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        invite_code2 = "TEST-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

        # 创建第一个用户
        user1 = User(
            email="unique@example.com",
            password_hash=hash_password("Password123!"),
            nickname="User1",
            invite_code=invite_code1,
        )
        db_session.add(user1)
        db_session.commit()

        # 尝试创建相同邮箱的用户
        user2 = User(
            email="unique@example.com",
            password_hash=hash_password("Password456!"),
            nickname="User2",
            invite_code=invite_code2,
        )
        db_session.add(user2)

        # 应该抛出唯一约束异常
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_created_at(self, db_session: Session):
        """测试用户创建时间"""
        invite_code = "TEST-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        
        user = User(
            email="createdat@example.com",
            password_hash=hash_password("Password123!"),
            nickname="CreatedAtUser",
            invite_code=invite_code,
        )
        db_session.add(user)
        db_session.commit()

        # 验证创建时间存在
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

    def test_user_repr(self, registered_user: dict):
        """测试用户字符串表示"""
        user = registered_user["user"]

        repr_str = repr(user)

        # 验证 repr 包含邮箱
        assert user.email in repr_str

    def test_user_to_dict(self, registered_user: dict):
        """测试用户转字典"""
        user = registered_user["user"]

        user_dict = user.to_dict()

        # 验证字典包含必要字段
        assert "id" in user_dict
        assert "email" in user_dict
        assert user_dict["email"] == user.email


# ═══════════════════════════════════════════════════════════
# 兑换码模型测试
# ═══════════════════════════════════════════════════════════

class TestRedemptionCodeModel:
    """兑换码模型测试"""

    def test_redemption_code_create(self, db_session: Session):
        """测试创建兑换码"""
        code = RedemptionCode(
            code="PRISM-TEST123",
            count=100,
            used=False,
            batch_id="TEST-BATCH",
            created_at=datetime.utcnow()
        )
        db_session.add(code)
        db_session.commit()

        # 验证兑换码创建成功
        assert code.id is not None
        assert code.code == "PRISM-TEST123"
        assert code.count == 100
        assert code.used is False

    def test_redemption_code_is_valid(self, db_session: Session):
        """测试兑换码有效性检查"""
        code = RedemptionCode(
            code="PRISM-VALID123",
            count=50,
            used=False,
            batch_id="TEST-BATCH",
            created_at=datetime.utcnow()
        )
        db_session.add(code)
        db_session.commit()

        # 验证兑换码有效
        assert code.is_valid() is True

        # 使用后验证
        code.used = True
        assert code.is_valid() is False

    def test_redemption_code_use(self, db_session: Session, registered_user: dict):
        """测试使用兑换码"""
        code = RedemptionCode(
            code="PRISM-USE123",
            count=50,
            used=False,
            batch_id="TEST-BATCH",
            created_at=datetime.utcnow()
        )
        db_session.add(code)
        db_session.commit()

        # 使用兑换码
        code.used = True
        code.used_by = registered_user["user"].id
        code.used_at = datetime.utcnow()
        db_session.commit()

        # 验证兑换码已使用
        assert code.used is True
        assert code.used_by == registered_user["user"].id


# ═══════════════════════════════════════════════════════════
# 邀请记录模型测试
# ═══════════════════════════════════════════════════════════

class TestInviteRecordModel:
    """邀请记录模型测试"""

    def test_invite_record_create(self, db_session: Session, registered_user: dict, registered_user_2: dict):
        """测试创建邀请记录"""
        record = InviteRecord(
            inviter_id=registered_user["user"].id,
            invitee_id=registered_user_2["user"].id,
            bonus_given=False,
            bonus_count=0,
        )
        db_session.add(record)
        db_session.commit()

        # 验证邀请记录创建成功
        assert record.id is not None
        assert record.inviter_id == registered_user["user"].id
        assert record.invitee_id == registered_user_2["user"].id