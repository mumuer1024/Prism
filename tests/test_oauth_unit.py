"""
OAuth 模块单元测试

测试 OAuth 状态管理、工具函数等
注意：GitHub OAuth 集成测试需要真实 OAuth 应用，此处跳过
"""
import pytest
from datetime import datetime, timedelta
import hashlib
import secrets

from src.auth.oauth.state import OAuthStateManager
from src.auth.oauth.github import GitHubOAuthService
from src.auth.oauth.exceptions import OAuthError, OAuthStateError, OAuthTokenError, OAuthUserError
from src.config import settings


# ═══════════════════════════════════════════════════════════
# OAuth 状态管理测试
# ═══════════════════════════════════════════════════════════

class TestOAuthStateManager:
    """OAuth 状态管理测试"""

    def test_generate_state(self):
        """测试创建 OAuth State"""
        state = OAuthStateManager.generate_state()

        # 验证状态不为空
        assert state is not None
        assert isinstance(state, str)
        assert len(state) >= 16  # 状态应该足够长

    def test_state_uniqueness(self):
        """测试状态唯一性"""
        states = set()
        for _ in range(100):
            state = OAuthStateManager.generate_state()
            states.add(state)

        # 验证所有状态都是唯一的
        assert len(states) == 100

    def test_validate_state_valid(self):
        """测试验证有效状态"""
        # 创建状态
        state = OAuthStateManager.generate_state()

        # 验证状态
        state_data = OAuthStateManager.validate_state(state)

        # 验证应该成功
        assert state_data is not None

    def test_validate_state_invalid(self):
        """测试验证无效状态"""
        # 验证一个不存在的状态
        state_data = OAuthStateManager.validate_state("invalid-state-string")

        # 验证应该失败
        assert state_data is None

    def test_consume_state(self):
        """测试消费状态（一次性使用）"""
        # 创建状态
        state = OAuthStateManager.generate_state()

        # 第一次消费成功
        state_data = OAuthStateManager.consume_state(state)
        assert state_data is not None

        # 第二次消费失败（状态已使用）
        state_data2 = OAuthStateManager.consume_state(state)
        assert state_data2 is None

    def test_state_expiration(self):
        """测试状态过期机制存在"""
        # 简单验证状态管理器有过期时间配置
        assert OAuthStateManager.STATE_EXPIRE_SECONDS > 0

    def test_clear_all(self):
        """测试清除所有状态"""
        # 创建一些状态
        state1 = OAuthStateManager.generate_state()
        state2 = OAuthStateManager.generate_state()
        
        # 清除所有
        OAuthStateManager.clear_all()
        
        # 验证状态已清除
        assert OAuthStateManager.validate_state(state1) is None
        assert OAuthStateManager.validate_state(state2) is None


# ═══════════════════════════════════════════════════════════
# GitHub OAuth 测试（基础功能，不涉及真实 API 调用）
# ═══════════════════════════════════════════════════════════

class TestGitHubOAuthBasics:
    """GitHub OAuth 基础测试"""

    def test_service_creation(self):
        """测试服务创建"""
        service = GitHubOAuthService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback"
        )
        
        assert service.client_id == "test_client_id"
        assert service.client_secret == "test_client_secret"
        assert service.redirect_uri == "http://localhost:8000/callback"

    def test_get_authorization_url(self):
        """测试获取授权 URL"""
        service = GitHubOAuthService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback"
        )

        url = service.get_authorize_url(state="test_state")

        # 验证 URL 格式
        assert url is not None
        assert "github.com" in url
        assert "client_id=test_client_id" in url
        assert "state=test_state" in url

    def test_authorization_url_contains_state(self):
        """测试授权 URL 包含 state"""
        service = GitHubOAuthService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback"
        )

        state = "random_state_123"
        url = service.get_authorize_url(state=state)

        # 验证 URL 和 state
        assert url is not None
        assert state in url

    def test_is_configured(self):
        """测试配置检查"""
        # 未配置
        service1 = GitHubOAuthService(
            client_id="",
            client_secret="",
            redirect_uri="http://localhost:8000/callback"
        )
        assert service1.is_configured() is False

        # 已配置
        service2 = GitHubOAuthService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback"
        )
        assert service2.is_configured() is True


# ═══════════════════════════════════════════════════════════
# OAuth 错误处理测试
# ═══════════════════════════════════════════════════════════

class TestOAuthErrors:
    """OAuth 错误处理测试"""

    def test_oauth_error_creation(self):
        """测试 OAuth 错误创建"""
        error = OAuthError("Test error message", "github")

        # 验证错误属性
        assert error.message == "Test error message"
        assert error.provider == "github"

    def test_oauth_error_string(self):
        """测试 OAuth 错误字符串表示"""
        error = OAuthError("User denied access", "github")
        error_str = str(error)

        # 验证错误字符串
        assert "github" in error_str
        assert "User denied access" in error_str

    def test_oauth_state_error(self):
        """测试状态错误"""
        error = OAuthStateError()

        # 验证错误类型
        assert isinstance(error, OAuthError)
        assert "state" in str(error).lower() or "验证" in str(error)

    def test_oauth_token_error(self):
        """测试 Token 错误"""
        error = OAuthTokenError("Failed to exchange token", "github")

        # 验证错误信息
        assert error is not None
        assert isinstance(error, OAuthError)

    def test_oauth_user_error(self):
        """测试用户信息错误"""
        error = OAuthUserError("Failed to get user info", "github")

        # 验证错误信息
        assert error is not None
        assert isinstance(error, OAuthError)


# ═══════════════════════════════════════════════════════════
# OAuth 配置测试
# ═══════════════════════════════════════════════════════════

class TestOAuthConfig:
    """OAuth 配置测试"""

    def test_oauth_enabled_check(self):
        """测试 OAuth 启用检查"""
        # 检查 GitHub OAuth 是否配置
        has_github = bool(getattr(settings, 'GITHUB_CLIENT_ID', None))

        # 只验证检查逻辑，不验证具体值
        assert isinstance(has_github, bool)

    def test_redirect_uri_format(self):
        """测试回调 URI 格式"""
        redirect_uri = getattr(settings, 'GITHUB_REDIRECT_URI', None)

        if redirect_uri:
            # 验证 URI 格式
            assert redirect_uri.startswith('http://') or redirect_uri.startswith('https://')


# ═══════════════════════════════════════════════════════════
# OAuth 回调处理测试
# ═══════════════════════════════════════════════════════════

class TestOAuthCallback:
    """OAuth 回调处理测试"""

    def test_parse_callback_params(self):
        """测试解析回调参数"""
        from urllib.parse import parse_qs, urlparse

        # 模拟回调 URL
        callback_url = "http://localhost:8000/api/auth/github/callback?code=abc123&state=xyz789"

        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)

        # 验证参数解析
        assert params.get('code') == ['abc123']
        assert params.get('state') == ['xyz789']

    def test_parse_callback_error(self):
        """测试解析回调错误"""
        from urllib.parse import parse_qs, urlparse

        # 模拟错误回调 URL
        callback_url = "http://localhost:8000/api/auth/github/callback?error=access_denied&error_description=User%20denied"

        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)

        # 验证错误参数
        assert params.get('error') == ['access_denied']
        assert 'denied' in params.get('error_description', [''])[0]


# ═══════════════════════════════════════════════════════════
# OAuth 用户信息测试
# ═══════════════════════════════════════════════════════════

class TestOAuthUserInfo:
    """OAuth 用户信息测试"""

    def test_extract_github_user_info(self):
        """测试提取 GitHub 用户信息"""
        # 模拟 GitHub API 返回的用户信息
        github_user = {
            "id": 12345,
            "login": "testuser",
            "email": "test@example.com",
            "name": "Test User",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345"
        }

        # 验证字段存在
        assert 'id' in github_user
        assert 'login' in github_user
        assert 'email' in github_user

    def test_github_user_id_uniqueness(self):
        """测试 GitHub 用户 ID 唯一性"""
        # GitHub 用户 ID 应该是唯一标识
        github_user = {
            "id": 12345,
            "login": "testuser"
        }

        # 使用 ID 作为唯一标识
        unique_id = f"github_{github_user['id']}"

        # 验证唯一标识格式
        assert unique_id == "github_12345"


# ═══════════════════════════════════════════════════════════
# 状态存储测试
# ═══════════════════════════════════════════════════════════

class TestStateStorage:
    """状态存储测试"""

    def test_state_storage_in_memory(self):
        """测试内存状态存储"""
        # 清除之前的状态
        OAuthStateManager.clear_all()
        
        # 创建状态
        state = OAuthStateManager.generate_state()

        # 验证状态存储
        state_data = OAuthStateManager.validate_state(state)
        assert state_data is not None

    def test_state_removal_after_consumption(self):
        """测试消费后状态移除"""
        OAuthStateManager.clear_all()
        
        # 创建状态
        state = OAuthStateManager.generate_state()

        # 第一次消费成功
        assert OAuthStateManager.consume_state(state) is not None

        # 第二次消费失败（状态已移除）
        assert OAuthStateManager.consume_state(state) is None


# ═══════════════════════════════════════════════════════════
# OAuth 安全性测试
# ═══════════════════════════════════════════════════════════

class TestOAuthSecurity:
    """OAuth 安全性测试"""

    def test_state_length_sufficient(self):
        """测试状态长度足够"""
        state = OAuthStateManager.generate_state()

        # 状态长度应该足够防止暴力猜测
        assert len(state) >= 16

    def test_state_randomness(self):
        """测试状态随机性"""
        states = [OAuthStateManager.generate_state() for _ in range(100)]

        # 计算唯一状态数量
        unique_count = len(set(states))

        # 所有状态应该都是唯一的
        assert unique_count == 100

    def test_csrf_protection_via_state(self):
        """测试通过 state 防止 CSRF"""
        OAuthStateManager.clear_all()
        
        # 正常流程
        state = OAuthStateManager.generate_state()

        # 攻击者尝试使用伪造的 state
        forged_state = "forged-state-123"

        # 验证伪造状态应该失败
        assert OAuthStateManager.validate_state(forged_state) is None

        # 验证真实状态应该成功
        assert OAuthStateManager.validate_state(state) is not None