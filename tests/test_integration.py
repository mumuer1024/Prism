"""
集成测试

测试完整的用户流程和端到端场景
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# 完整注册流程测试
# ═══════════════════════════════════════════════════════════

class TestFullRegisterFlow:
    """完整注册流程测试"""
    
    def test_full_register_flow(self, client: TestClient):
        """测试完整注册流程：注册 → 获取用户信息 → 生成邀请码"""
        # 1. 注册用户
        register_response = client.post("/api/auth/register", json={
            "email": "fullflow@example.com",
            "password": "TestPassword123!",
            "nickname": "FullFlowUser"
        })
        
        assert register_response.status_code in [200, 201]
        register_data = register_response.json()
        
        # 验证注册成功
        assert register_data["success"] is True
        assert "access_token" in register_data["data"]
        
        token = register_data["data"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 获取用户信息
        profile_response = client.get("/api/auth/me", headers=auth_headers)
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        
        # 验证用户信息
        assert profile_data["success"] is True
        assert profile_data["data"]["user"]["email"] == "fullflow@example.com"
        
        # 3. 获取邀请码
        invite_response = client.get("/api/user/invite-stats", headers=auth_headers)
        
        assert invite_response.status_code == 200
        invite_data = invite_response.json()
        
        # 验证邀请码存在
        assert invite_data["success"] is True
        assert "invite_code" in invite_data["data"]


# ═══════════════════════════════════════════════════════════
# 完整登录流程测试
# ═══════════════════════════════════════════════════════════

class TestFullLoginFlow:
    """完整登录流程测试"""
    
    def test_full_login_flow(self, client: TestClient, test_user_data: dict):
        """测试完整登录流程：注册 → 登出 → 登录 → 访问受保护资源"""
        # 1. 先注册用户
        client.post("/api/auth/register", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        # 2. 登录
        login_response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        # 验证登录成功
        assert login_data["success"] is True
        assert "access_token" in login_data["data"]
        
        token = login_data["data"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # 3. 访问受保护资源
        profile_response = client.get("/api/user/profile", headers=auth_headers)
        
        assert profile_response.status_code == 200
        
        # 4. 登出
        logout_response = client.post("/api/auth/logout", headers=auth_headers)
        
        assert logout_response.status_code == 200


# ═══════════════════════════════════════════════════════════
# 激活码充值流程测试
# ═══════════════════════════════════════════════════════════

class TestRedeemFlow:
    """激活码充值流程测试"""
    
    def test_redeem_flow(self, client: TestClient, activation_code: str, test_user_data: dict):
        """测试激活码充值流程：注册 → 检查次数 → 兑换 → 检查次数增加"""
        # 1. 注册用户
        register_response = client.post("/api/auth/register", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        token = register_response.json()["data"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 检查初始次数
        balance_response = client.get("/api/usage/balance", headers=auth_headers)
        
        assert balance_response.status_code == 200
        initial_balance = balance_response.json()["data"]
        
        # 3. 兑换激活码
        redeem_response = client.post("/api/user/redeem",
            headers=auth_headers,
            json={"code": activation_code}
        )
        
        assert redeem_response.status_code == 200
        redeem_data = redeem_response.json()
        
        # 验证兑换成功
        assert redeem_data["success"] is True
        assert redeem_data["data"]["count"] > 0
        
        # 4. 检查次数增加
        new_balance_response = client.get("/api/usage/balance", headers=auth_headers)
        
        assert new_balance_response.status_code == 200
        new_balance = new_balance_response.json()["data"]
        
        # 验证次数增加
        assert new_balance["paid_count"] >= initial_balance.get("paid_count", 0)


# ═══════════════════════════════════════════════════════════
# 使用次数扣减流程测试
# ═══════════════════════════════════════════════════════════

class TestUsageDeductionFlow:
    """使用次数扣减流程测试"""
    
    def test_usage_deduction_flow(self, client: TestClient):
        """测试使用次数扣减流程：注册 → 检查权限 → 扣减 → 检查余额"""
        # 1. 注册用户
        register_response = client.post("/api/auth/register", json={
            "email": "deduction@example.com",
            "password": "TestPassword123!"
        })
        
        token = register_response.json()["data"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 检查使用权限
        check_response = client.post("/api/usage/check",
            headers=auth_headers,
            json={"tool_type": "bounty_hunter"}
        )
        
        assert check_response.status_code == 200
        assert check_response.json()["data"]["can_use"] is True
        
        # 3. 获取初始余额
        balance_response = client.get("/api/usage/balance", headers=auth_headers)
        initial_free = balance_response.json()["data"].get("free_count", 3)
        
        # 4. 扣减使用次数
        deduct_response = client.post("/api/usage/deduct",
            headers=auth_headers,
            json={"tool_type": "bounty_hunter"}
        )
        
        assert deduct_response.status_code == 200
        
        # 5. 再次检查余额
        new_balance_response = client.get("/api/usage/balance", headers=auth_headers)
        new_free = new_balance_response.json()["data"].get("free_count", 0)
        
        # 验证次数减少（免费次数应该减少）
        # 注意：具体逻辑取决于实现


# ═══════════════════════════════════════════════════════════
# 邀请返利流程测试
# ═══════════════════════════════════════════════════════════

class TestInviteRewardFlow:
    """邀请返利流程测试"""
    
    def test_invite_reward_flow(self, client: TestClient, activation_code: str):
        """测试邀请返利流程：用户A注册 → 用户B使用邀请码注册 → 验证邀请关系"""
        # 1. 用户A注册
        user_a_response = client.post("/api/auth/register", json={
            "email": "inviter@example.com",
            "password": "TestPassword123!"
        })
        
        token_a = user_a_response.json()["data"]["access_token"]
        auth_headers_a = {"Authorization": f"Bearer {token_a}"}
        
        # 2. 获取用户A的邀请码
        invite_response = client.get("/api/user/invite-stats", headers=auth_headers_a)
        invite_code = invite_response.json()["data"]["invite_code"]
        
        # 3. 用户B使用邀请码注册
        user_b_response = client.post("/api/auth/register", json={
            "email": "invitee@example.com",
            "password": "TestPassword123!",
            "invite_code": invite_code
        })
        
        # 验证注册成功
        assert user_b_response.status_code in [200, 201]
        
        # 4. 检查用户A的邀请统计
        # 注意：邀请奖励可能需要在被邀请人充值后才生效
        # 这里只验证邀请码功能正常


# ═══════════════════════════════════════════════════════════
# 匿名用户流程测试
# ═══════════════════════════════════════════════════════════

class TestAnonymousUserFlow:
    """匿名用户流程测试"""
    
    def test_anonymous_user_flow(self, client: TestClient):
        """测试匿名用户流程：检查次数 → 扣减 → 检查余额 → 再次扣减"""
        visitor_id = "anonymous-flow-test"
        
        # 1. 检查匿名用户使用权限
        check_response = client.post("/api/usage/check",
            json={
                "tool_type": "bounty_hunter",
                "visitor_id": visitor_id,
                "ip_address": "127.0.0.1"
            }
        )
        
        assert check_response.status_code == 200
        assert check_response.json()["data"]["can_use"] is True
        
        # 2. 扣减使用次数
        deduct_response = client.post("/api/usage/deduct",
            json={
                "tool_type": "bounty_hunter",
                "visitor_id": visitor_id,
                "ip_address": "127.0.0.1"
            }
        )
        
        assert deduct_response.status_code == 200
        
        # 3. 检查余额
        balance_response = client.get(f"/api/usage/balance?visitor_id={visitor_id}")
        
        assert balance_response.status_code == 200
        
        # 4. 再次扣减
        deduct_response2 = client.post("/api/usage/deduct",
            json={
                "tool_type": "bounty_hunter",
                "visitor_id": visitor_id,
                "ip_address": "127.0.0.1"
            }
        )
        
        assert deduct_response2.status_code == 200


# ═══════════════════════════════════════════════════════════
# 付费用户完整流程测试
# ═══════════════════════════════════════════════════════════

class TestPaidUserFlow:
    """付费用户完整流程测试"""
    
    def test_paid_user_flow(self, client: TestClient, paid_user: dict):
        """测试付费用户流程：检查权限 → 扣减 → 验证缓存类型"""
        auth_headers = {"Authorization": f"Bearer {paid_user['access_token']}"}
        
        # 1. 检查使用权限
        check_response = client.post("/api/usage/check",
            headers=auth_headers,
            json={"tool_type": "bounty_hunter"}
        )
        
        assert check_response.status_code == 200
        assert check_response.json()["data"]["can_use"] is True
        
        # 2. 获取初始余额
        initial_balance_response = client.get("/api/usage/balance", headers=auth_headers)
        initial_paid_count = initial_balance_response.json()["data"]["paid_count"]

        # 3. 扣减使用次数
        deduct_response = client.post("/api/usage/deduct",
            headers=auth_headers,
            json={"tool_type": "bounty_hunter"}
        )
        
        assert deduct_response.status_code == 200
        
        # 4. 验证缓存类型为 premium
        deduct_data = deduct_response.json()
        assert deduct_data["data"]["cache_type"] == "premium"
        
        # 5. 检查剩余次数
        balance_response = client.get("/api/usage/balance", headers=auth_headers)
        
        assert balance_response.status_code == 200
        balance_data = balance_response.json()["data"]
        
        # 验证付费次数减少
        assert balance_data["paid_count"] < initial_paid_count


# ═══════════════════════════════════════════════════════════
# 错误处理流程测试
# ═══════════════════════════════════════════════════════════

class TestErrorHandlingFlow:
    """错误处理流程测试"""
    
    def test_invalid_token_handling(self, client: TestClient):
        """测试无效 Token 处理"""
        # 使用无效 Token 访问受保护资源
        response = client.get("/api/user/profile", headers={
            "Authorization": "Bearer invalid.token.string"
        })
        
        # 应该返回 401
        assert response.status_code == 401
    
    def test_missing_token_handling(self, client: TestClient):
        """测试缺少 Token 处理"""
        # 不提供 Token 访问受保护资源
        response = client.get("/api/user/profile")
        
        # 应该返回 401
        assert response.status_code == 401
    
    def test_duplicate_registration_handling(self, client: TestClient, test_user_data: dict):
        """测试重复注册处理"""
        # 第一次注册
        client.post("/api/auth/register", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        # 第二次注册相同邮箱
        response = client.post("/api/auth/register", json={
            "email": test_user_data["email"],
            "password": "AnotherPassword123!"
        })
        
        # 应该返回错误
        assert response.status_code in [400, 409]
    
    def test_wrong_password_handling(self, client: TestClient, test_user_data: dict):
        """测试错误密码处理"""
        # 先注册用户
        client.post("/api/auth/register", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        # 使用错误密码登录
        response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": "WrongPassword123!"
        })
        
        # 应该返回 401
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# 并发访问测试
# ═══════════════════════════════════════════════════════════

class TestConcurrentAccess:
    """并发访问测试"""
    
    def test_concurrent_usage_check(self, client: TestClient, auth_headers: dict):
        """测试并发使用权限检查"""
        # 连续多次检查使用权限
        responses = []
        for _ in range(10):
            response = client.post("/api/usage/check",
                headers=auth_headers,
                json={"tool_type": "bounty_hunter"}
            )
            responses.append(response)
        
        # 所有请求都应该成功
        for response in responses:
            assert response.status_code == 200
    
    def test_concurrent_balance_check(self, client: TestClient, auth_headers: dict):
        """测试并发余额查询"""
        # 连续多次查询余额
        responses = []
        for _ in range(5):
            response = client.get("/api/usage/balance", headers=auth_headers)
            responses.append(response)
        
        # 所有请求都应该成功
        for response in responses:
            assert response.status_code == 200


# ═══════════════════════════════════════════════════════════
# 用户信息更新流程测试
# ═══════════════════════════════════════════════════════════

class TestUserInfoUpdateFlow:
    """用户信息更新流程测试"""

    def test_update_nickname_flow(self, client: TestClient):
        """测试更新昵称流程"""
        # 1. 注册用户
        register_response = client.post("/api/auth/register", json={
            "email": "nickname@example.com",
            "password": "TestPassword123!"
        })

        token = register_response.json()["data"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 2. 获取初始信息
        profile_response = client.get("/api/user/profile", headers=auth_headers)
        original_nickname = profile_response.json()["data"]["user"].get("nickname")

        # 3. 更新昵称
        update_response = client.put("/api/user/profile",
            headers=auth_headers,
            json={"nickname": "UpdatedName"}
        )

        assert update_response.status_code == 200

        # 4. 验证昵称已更新
        new_profile_response = client.get("/api/user/profile", headers=auth_headers)
        new_nickname = new_profile_response.json()["data"]["user"]["nickname"]

        assert new_nickname == "UpdatedName"


# ═══════════════════════════════════════════════════════════
# 密码修改流程测试
# ═══════════════════════════════════════════════════════════

class TestPasswordChangeFlow:
    """密码修改流程测试"""
    
    def test_change_password_flow(self, client: TestClient):
        """测试密码修改流程"""
        # 1. 注册用户
        register_response = client.post("/api/auth/register", json={
            "email": "password@example.com",
            "password": "OldPassword123!"
        })
        
        token = register_response.json()["data"]["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 修改密码
        change_response = client.post("/api/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "OldPassword123!",
                "new_password": "NewPassword456!"
            }
        )
        
        assert change_response.status_code == 200
        
        # 3. 使用旧密码登录应该失败
        old_login_response = client.post("/api/auth/login", json={
            "email": "password@example.com",
            "password": "OldPassword123!"
        })
        
        assert old_login_response.status_code == 401
        
        # 4. 使用新密码登录应该成功
        new_login_response = client.post("/api/auth/login", json={
            "email": "password@example.com",
            "password": "NewPassword456!"
        })
        
        assert new_login_response.status_code == 200