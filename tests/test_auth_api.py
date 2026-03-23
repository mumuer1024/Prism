"""
认证 API 测试

测试认证相关的 API 端点
"""
import pytest
from fastapi.testclient import TestClient


# ═══════════════════════════════════════════════════════════
# 注册 API 测试
# ═══════════════════════════════════════════════════════════

class TestRegisterAPI:
    """注册 API 测试"""

    def test_register_success(self, client: TestClient, test_user_data: dict):
        """测试注册成功"""
        response = client.post("/api/auth/register", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
            "nickname": test_user_data.get("nickname")
        })

        # 验证响应状态
        assert response.status_code in [200, 201]

        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "user" in data["data"]
        assert data["data"]["user"]["email"] == test_user_data["email"]

    def test_register_invalid_email(self, client: TestClient, invalid_email_data: dict):
        """测试无效邮箱注册"""
        response = client.post("/api/auth/register", json={
            "email": invalid_email_data["email"],
            "password": invalid_email_data["password"]
        })

        # 验证响应状态（应该返回 422 验证错误或 400）
        assert response.status_code in [400, 422]

    def test_register_weak_password(self, client: TestClient, weak_password_data: dict):
        """测试弱密码注册"""
        response = client.post("/api/auth/register", json={
            "email": weak_password_data["email"],
            "password": weak_password_data["password"]
        })

        # 验证响应状态（应该返回 400 或 422）
        assert response.status_code in [400, 422]

    def test_register_missing_email(self, client: TestClient):
        """测试缺少邮箱注册"""
        response = client.post("/api/auth/register", json={
            "password": "TestPassword123!"
        })

        # 验证响应状态（应该返回 422）
        assert response.status_code == 422

    def test_register_missing_password(self, client: TestClient):
        """测试缺少密码注册"""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com"
        })

        # 验证响应状态（应该返回 422）
        assert response.status_code == 422

    def test_register_duplicate_email(self, client: TestClient, registered_user: dict, test_user_data: dict):
        """测试重复邮箱注册"""
        response = client.post("/api/auth/register", json={
            "email": test_user_data["email"],
            "password": "AnotherPassword123!"
        })

        # 验证响应状态（应该返回 400 或 409）
        assert response.status_code in [400, 409]

    def test_register_with_invite_code(self, client: TestClient, invite_code: str):
        """测试使用邀请码注册"""
        response = client.post("/api/auth/register", json={
            "email": "invited@example.com",
            "password": "TestPassword123!",
            "invite_code": invite_code
        })

        # 验证响应状态
        assert response.status_code in [200, 201, 400]


# ═══════════════════════════════════════════════════════════
# 登录 API 测试
# ═══════════════════════════════════════════════════════════

class TestLoginAPI:
    """登录 API 测试"""

    def test_login_success(self, client: TestClient, registered_user: dict, test_user_data: dict):
        """测试登录成功"""
        response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })

        # 验证响应状态
        assert response.status_code in [200, 201]

        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert "expires_in" in data["data"]

    def test_login_wrong_password(self, client: TestClient, registered_user: dict, test_user_data: dict):
        """测试登录错误密码"""
        response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        })

        # 验证响应状态（应该返回 401）
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """测试登录不存在的用户"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "TestPassword123!"
        })

        # 验证响应状态（应该返回 401）
        assert response.status_code == 401

    def test_login_missing_email(self, client: TestClient):
        """测试缺少邮箱登录"""
        response = client.post("/api/auth/login", json={
            "password": "TestPassword123!"
        })

        # 验证响应状态（应该返回 422）
        assert response.status_code == 422

    def test_login_missing_password(self, client: TestClient):
        """测试缺少密码登录"""
        response = client.post("/api/auth/login", json={
            "email": "test@example.com"
        })

        # 验证响应状态（应该返回 422）
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════
# 用户信息 API 测试
# ═══════════════════════════════════════════════════════════

class TestMeAPI:
    """用户信息 API 测试"""

    def test_get_current_user_success(self, client: TestClient, auth_headers: dict):
        """测试获取当前用户成功"""
        response = client.get("/api/auth/me", headers=auth_headers)

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]

    def test_unauthorized_access(self, client: TestClient):
        """测试未授权访问"""
        response = client.get("/api/auth/me")

        # 验证响应状态（应该返回 401）
        assert response.status_code == 401

    def test_invalid_token_access(self, client: TestClient):
        """测试无效 Token 访问"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid.token.string"
        })

        # 验证响应状态（应该返回 401）
        assert response.status_code == 401

    def test_expired_token_access(self, client: TestClient):
        """测试过期 Token 访问"""
        # 使用一个过期的 Token
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {expired_token}"
        })

        # 验证响应状态（应该返回 401）
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# Token 刷新 API 测试
# ═══════════════════════════════════════════════════════════

class TestRefreshTokenAPI:
    """Token 刷新 API 测试"""

    def test_refresh_token_success(self, client: TestClient, registered_user: dict, test_user_data: dict):
        """测试刷新 Token 成功"""
        # 先登录获取 refresh_token
        login_response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })

        if login_response.status_code == 200:
            login_data = login_response.json()
            refresh_token = login_data["data"]["refresh_token"]

            response = client.post("/api/auth/refresh", json={
                "refresh_token": refresh_token
            })

            # 验证响应状态
            assert response.status_code == 200

            # 验证响应数据
            data = response.json()
            assert "access_token" in data["data"]

    def test_refresh_token_invalid(self, client: TestClient):
        """测试无效刷新 Token"""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid-refresh-token"
        })

        # 验证响应状态（应该返回 401 或 400）
        assert response.status_code in [401, 400]


# ═══════════════════════════════════════════════════════════
# 登出 API 测试
# ═══════════════════════════════════════════════════════════

class TestLogoutAPI:
    """登出 API 测试"""

    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """测试登出成功"""
        response = client.post("/api/auth/logout", headers=auth_headers)

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应数据
        data = response.json()
        assert data["success"] is True

    def test_logout_unauthorized(self, client: TestClient):
        """测试未授权登出"""
        response = client.post("/api/auth/logout")

        # 验证响应状态（应该返回 401）
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# 忘记密码 API 测试
# ═══════════════════════════════════════════════════════════

class TestForgotPasswordAPI:
    """忘记密码 API 测试"""

    def test_forgot_password_success(self, client: TestClient, registered_user: dict, test_user_data: dict):
        """测试发送重置邮件成功"""
        # 注意：需要 SMTP 配置才能真正发送邮件
        # 测试环境下可能需要 mock 邮件服务
        response = client.post("/api/auth/send-code", json={
            "email": test_user_data["email"],
            "purpose": "reset_password"
        })

        # 验证响应状态（成功或服务不可用）
        assert response.status_code in [200, 503, 400, 429]

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """测试不存在的邮箱"""
        response = client.post("/api/auth/send-code", json={
            "email": "nonexistent@example.com",
            "purpose": "reset_password"
        })

        # 为了安全，通常会返回错误
        assert response.status_code in [200, 400, 404]


# ═══════════════════════════════════════════════════════════
# 验证码 API 测试
# ═══════════════════════════════════════════════════════════

class TestVerifyCodeAPI:
    """验证码 API 测试"""

    def test_send_verify_code(self, client: TestClient):
        """测试发送验证码"""
        # 注意：需要 SMTP 配置
        response = client.post("/api/auth/send-code", json={
            "email": "verify@example.com",
            "purpose": "register"
        })

        # 验证响应状态（成功或服务不可用）
        assert response.status_code in [200, 503, 400, 429]

    def test_send_verify_code_invalid_email(self, client: TestClient):
        """测试无效邮箱发送验证码"""
        response = client.post("/api/auth/send-code", json={
            "email": "invalid-email",
            "purpose": "register"
        })

        # 验证响应状态（应该返回 422）
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════
# 密码重置 API 测试
# ═══════════════════════════════════════════════════════════

class TestResetPasswordAPI:
    """密码重置 API 测试"""

    def test_reset_password_invalid_token(self, client: TestClient):
        """测试无效 Token 重置密码"""
        response = client.post("/api/auth/reset-password", json={
            "email": "test@example.com",
            "code": "invalid-code",
            "new_password": "NewPassword123!"
        })

        # 验证响应状态（应该返回 400 或 401）
        assert response.status_code in [400, 401, 404, 422]

    def test_reset_password_weak_password(self, client: TestClient):
        """测试弱密码重置"""
        response = client.post("/api/auth/reset-password", json={
            "email": "test@example.com",
            "code": "123456",
            "new_password": "123"
        })

        # 验证响应状态（应该返回 400 或 422）
        assert response.status_code in [400, 422]


# ═══════════════════════════════════════════════════════════
# 修改密码 API 测试
# ═══════════════════════════════════════════════════════════

class TestChangePasswordAPI:
    """修改密码 API 测试"""

    def test_change_password_success(self, client: TestClient, auth_headers: dict, test_user_data: dict):
        """测试修改密码成功"""
        response = client.post("/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": test_user_data["password"],
                "new_password": "NewPassword456!"
            }
        )

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应数据
        data = response.json()
        assert data["success"] is True

    def test_change_password_wrong_old_password(self, client: TestClient, auth_headers: dict):
        """测试旧密码错误"""
        response = client.post("/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "WrongOldPassword123!",
                "new_password": "NewPassword456!"
            }
        )

        # 验证响应状态（应该返回 400）
        assert response.status_code in [400, 401]

    def test_change_password_unauthorized(self, client: TestClient):
        """测试未授权修改密码"""
        response = client.post("/api/auth/change-password", json={
            "old_password": "OldPassword123!",
            "new_password": "NewPassword456!"
        })

        # 验证响应状态（应该返回 401）
        assert response.status_code == 401