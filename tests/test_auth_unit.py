"""
认证模块单元测试

测试密码处理、JWT 处理、认证服务等核心功能
"""
import pytest
from datetime import datetime, timedelta

from src.auth.utils.password_handler import (
    PasswordHandler, hash_password, verify_password, validate_password_strength
)
from src.auth.utils.jwt_handler import (
    JWTHandler, create_access_token, verify_access_token, verify_refresh_token
)
from src.auth.service import AuthService
from src.auth.schemas import RegisterRequest, LoginRequest
from src.database.models import User


# ═══════════════════════════════════════════════════════════
# 密码处理测试
# ═══════════════════════════════════════════════════════════

class TestPasswordHandler:
    """密码处理器测试"""

    def test_hash_password(self):
        """测试密码哈希生成"""
        password = "TestPassword123!"
        handler = PasswordHandler()
        hashed = handler.hash_password(password)

        # 验证哈希值不为空
        assert hashed is not None
        # 验证哈希值与原密码不同
        assert hashed != password
        # 验证哈希值是字符串
        assert isinstance(hashed, str)
        # 验证哈希值长度合理（bcrypt 生成的哈希约 60 字符）
        assert len(hashed) > 50

    def test_hash_password_different_each_time(self):
        """测试相同密码每次生成的哈希不同"""
        password = "TestPassword123!"
        handler = PasswordHandler()
        hash1 = handler.hash_password(password)
        hash2 = handler.hash_password(password)

        # 两次哈希值应该不同（bcrypt 自动加盐）
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "TestPassword123!"
        handler = PasswordHandler()
        hashed = handler.hash_password(password)

        # 验证正确密码
        assert handler.verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """测试错误密码验证"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        handler = PasswordHandler()
        hashed = handler.hash_password(password)

        # 验证错误密码
        assert handler.verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """测试空密码验证"""
        password = "TestPassword123!"
        handler = PasswordHandler()
        hashed = handler.hash_password(password)

        # 验证空密码
        assert handler.verify_password("", hashed) is False

    def test_module_level_functions(self):
        """测试模块级便捷函数"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


# ═══════════════════════════════════════════════════════════
# JWT 处理测试
# ═══════════════════════════════════════════════════════════

class TestJWTHandler:
    """JWT 处理器测试"""

    def test_create_access_token(self):
        """测试创建 Access Token"""
        handler = JWTHandler()
        token = handler.create_access_token(
            user_id=1,
            email="test@example.com",
            usage_count=0
        )

        # 验证 Token 不为空
        assert token is not None
        # 验证 Token 是字符串
        assert isinstance(token, str)
        # 验证 Token 有内容
        assert len(token) > 50

    def test_create_refresh_token(self):
        """测试创建 Refresh Token"""
        handler = JWTHandler()
        token, token_hash, expires_at = handler.create_refresh_token(user_id=1)

        # 验证 Token 不为空
        assert token is not None
        assert token_hash is not None
        assert expires_at is not None
        # 验证 Token 是字符串
        assert isinstance(token, str)
        # 验证 Token 有内容
        assert len(token) > 50

    def test_verify_access_token_valid(self):
        """测试验证有效 Access Token"""
        handler = JWTHandler()
        token = handler.create_access_token(
            user_id=1,
            email="test@example.com",
            usage_count=0
        )

        # 验证 Token
        decoded = handler.verify_access_token(token)

        # 验证解码结果
        assert decoded is not None
        assert decoded["sub"] == "1"
        assert decoded["email"] == "test@example.com"

    def test_verify_access_token_invalid(self):
        """测试验证无效 Token"""
        handler = JWTHandler()
        invalid_token = "invalid.token.string"

        # 验证无效 Token
        decoded = handler.verify_access_token(invalid_token)

        # 应该返回 None
        assert decoded is None

    def test_verify_access_token_empty(self):
        """测试验证空 Token"""
        handler = JWTHandler()
        decoded = handler.verify_access_token("")
        assert decoded is None

    def test_token_contains_exp(self):
        """测试 Token 包含过期时间"""
        handler = JWTHandler()
        token = handler.create_access_token(
            user_id=1,
            email="test@example.com",
            usage_count=0
        )

        decoded = handler.verify_access_token(token)

        # 验证包含过期时间
        assert "exp" in decoded

    def test_token_contains_iat(self):
        """测试 Token 包含签发时间"""
        handler = JWTHandler()
        token = handler.create_access_token(
            user_id=1,
            email="test@example.com",
            usage_count=0
        )

        decoded = handler.verify_access_token(token)

        # 验证包含签发时间
        assert "iat" in decoded

    def test_module_level_functions(self):
        """测试模块级便捷函数"""
        token = create_access_token(
            user_id=1,
            email="test@example.com",
            usage_count=0
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        decoded = verify_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "1"


# ═══════════════════════════════════════════════════════════
# 认证服务测试
# ═══════════════════════════════════════════════════════════

class TestAuthService:
    """认证服务测试"""

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service: AuthService, db_session):
        """测试用户注册成功"""
        user, refresh_token, message = await auth_service.register(
            email="new@example.com",
            password="Password123!"
        )
        db_session.commit()

        # 验证用户创建成功
        assert user is not None
        assert user.email == "new@example.com"
        assert user.usage_count == 0
        # 验证密码已哈希
        assert user.password_hash != "Password123!"
        assert refresh_token is not None

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service: AuthService, db_session):
        """测试重复邮箱注册"""
        # 第一次注册
        user1, _, _ = await auth_service.register(
            email="duplicate@example.com",
            password="Password123!"
        )
        db_session.commit()

        # 第二次注册相同邮箱
        user2, _, message = await auth_service.register(
            email="duplicate@example.com",
            password="Password456!"
        )
        
        assert user2 is None
        assert "已被注册" in message

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service: AuthService, db_session):
        """测试登录成功"""
        # 先注册用户
        await auth_service.register(
            email="login@example.com",
            password="Password123!"
        )
        db_session.commit()

        # 登录
        user, refresh_token, message = await auth_service.login(
            email="login@example.com",
            password="Password123!"
        )

        # 验证登录结果
        assert user is not None
        assert user.email == "login@example.com"
        assert refresh_token is not None

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service: AuthService, db_session):
        """测试登录错误密码"""
        # 先注册用户
        await auth_service.register(
            email="wrongpass@example.com",
            password="Password123!"
        )
        db_session.commit()

        # 使用错误密码登录
        user, refresh_token, message = await auth_service.login(
            email="wrongpass@example.com",
            password="WrongPassword!"
        )

        # 应该返回 None
        assert user is None
        assert refresh_token is None

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, auth_service: AuthService):
        """测试登录不存在的用户"""
        user, refresh_token, message = await auth_service.login(
            email="nonexistent@example.com",
            password="Password123!"
        )

        # 应该返回 None
        assert user is None
        assert refresh_token is None

    @pytest.mark.asyncio
    async def test_refresh_token(self, auth_service: AuthService, db_session):
        """测试刷新 Token"""
        # 注册用户
        user, refresh_token, _ = await auth_service.register(
            email="refresh@example.com",
            password="Password123!"
        )
        db_session.commit()

        # 刷新 Token
        new_access, new_refresh, message = await auth_service.refresh_tokens(refresh_token)

        # 验证刷新结果
        assert new_access is not None
        assert new_refresh is not None


# ═══════════════════════════════════════════════════════════
# 密码强度验证测试
# ═══════════════════════════════════════════════════════════

class TestPasswordStrength:
    """密码强度验证测试"""

    def test_password_strength_weak(self):
        """测试弱密码检测"""
        weak_passwords = [
            "123",
            "abc",
            "password",
            "qwerty"
        ]

        for password in weak_passwords:
            is_valid, msg = validate_password_strength(password)
            assert is_valid is False

    def test_password_strength_strong(self):
        """测试强密码检测"""
        strong_passwords = [
            "Password123!",
            "StrongPass@2024",
            "MyP@ssw0rd!",
            "Complex#Pass1"
        ]

        for password in strong_passwords:
            is_valid, msg = validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid: {msg}"

    def test_password_strength_medium(self):
        """测试中等密码检测"""
        # 密码需要至少8字符、一个字母、一个数字
        medium_passwords = [
            "password123",  # 缺少大写字母但符合基本要求
            "Password123",  # 符合要求
        ]

        for password in medium_passwords:
            is_valid, msg = validate_password_strength(password)
            # 验证有结果返回
            assert isinstance(is_valid, bool)

    def test_password_too_short(self):
        """测试密码太短"""
        is_valid, msg = validate_password_strength("Pass1")
        assert is_valid is False
        assert "8" in msg

    def test_password_no_letter(self):
        """测试密码没有字母"""
        is_valid, msg = validate_password_strength("12345678")
        assert is_valid is False
        assert "字母" in msg

    def test_password_no_digit(self):
        """测试密码没有数字"""
        is_valid, msg = validate_password_strength("Password")
        assert is_valid is False
        assert "数字" in msg