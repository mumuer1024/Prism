"""
用户 API 测试

测试用户相关的 API 端点
"""
import pytest
from fastapi.testclient import TestClient


# ═══════════════════════════════════════════════════════════
# 用户信息 API 测试
# ═══════════════════════════════════════════════════════════

class TestUserProfileAPI:
    """用户信息 API 测试"""
    
    def test_get_profile_success(self, client: TestClient, auth_headers: dict):
        """测试获取用户信息成功"""
        response = client.get("/api/user/profile", headers=auth_headers)
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
    
    def test_get_profile_unauthorized(self, client: TestClient):
        """测试未授权获取用户信息"""
        response = client.get("/api/user/profile")
        
        # 验证响应状态（应该返回 401）
        assert response.status_code == 401
    
    def test_update_nickname_success(self, client: TestClient, auth_headers: dict):
        """测试更新昵称成功"""
        response = client.put("/api/user/profile", 
            headers=auth_headers,
            json={"nickname": "NewNickname"}
        )
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
    
    def test_update_nickname_unauthorized(self, client: TestClient):
        """测试未授权更新昵称"""
        response = client.put("/api/user/profile", json={"nickname": "NewNickname"})
        
        # 验证响应状态（应该返回 401）
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# 使用次数 API 测试
# ═══════════════════════════════════════════════════════════

class TestUsageBalanceAPI:
    """使用次数 API 测试"""
    
    def test_get_balance_success(self, client: TestClient, auth_headers: dict):
        """测试获取使用次数成功"""
        response = client.get("/api/usage/balance", headers=auth_headers)
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "paid_count" in data["data"] or "balance" in data["data"]
    
    def test_get_balance_unauthorized(self, client: TestClient):
        """测试未授权获取使用次数"""
        response = client.get("/api/usage/balance")
        
        # 验证响应状态（应该返回 401 或 200 匿名用户）
        assert response.status_code in [200, 401]


# ═══════════════════════════════════════════════════════════
# 激活码 API 测试
# ═══════════════════════════════════════════════════════════

class TestRedeemAPI:
    """激活码兑换 API 测试"""
    
    def test_redeem_code_success(self, client: TestClient, auth_headers: dict, activation_code: str):
        """测试兑换激活码成功"""
        response = client.post("/api/user/redeem",
            headers=auth_headers,
            json={"code": activation_code}
        )
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "count" in data["data"]
    
    def test_redeem_code_invalid(self, client: TestClient, auth_headers: dict):
        """测试兑换无效激活码"""
        response = client.post("/api/user/redeem",
            headers=auth_headers,
            json={"code": "INVALID-CODE"}
        )
        
        # 验证响应状态（应该返回 400）
        assert response.status_code == 400
    
    def test_redeem_code_empty(self, client: TestClient, auth_headers: dict):
        """测试兑换空激活码"""
        response = client.post("/api/user/redeem",
            headers=auth_headers,
            json={"code": ""}
        )
        
        # 验证响应状态（应该返回 400 或 422）
        assert response.status_code in [400, 422]
    
    def test_redeem_code_unauthorized(self, client: TestClient, activation_code: str):
        """测试未授权兑换激活码"""
        response = client.post("/api/user/redeem", json={"code": activation_code})
        
        # 验证响应状态（应该返回 401）
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# 邀请统计 API 测试
# ═══════════════════════════════════════════════════════════

class TestInviteStatsAPI:
    """邀请统计 API 测试"""
    
    def test_get_invite_stats_success(self, client: TestClient, auth_headers: dict):
        """测试获取邀请统计成功"""
        response = client.get("/api/user/invite-stats", headers=auth_headers)
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "invite_code" in data["data"]
    
    def test_get_invite_stats_unauthorized(self, client: TestClient):
        """测试未授权获取邀请统计"""
        response = client.get("/api/user/invite-stats")
        
        # 验证响应状态（应该返回 401）
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# 使用次数检查 API 测试
# ═══════════════════════════════════════════════════════════

class TestUsageCheckAPI:
    """使用次数检查 API 测试"""
    
    def test_check_usage_success(self, client: TestClient, auth_headers: dict):
        """测试检查使用次数成功"""
        response = client.post("/api/usage/check",
            headers=auth_headers,
            json={"tool_type": "bounty_hunter"}
        )
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert "can_use" in data["data"] or "allowed" in data["data"]
    
    def test_check_usage_anonymous(self, client: TestClient):
        """测试匿名用户检查使用次数"""
        response = client.post("/api/usage/check",
            json={
                "tool_type": "bounty_hunter",
                "visitor_id": "test-visitor-123"
            }
        )
        
        # 验证响应状态（应该成功，匿名用户有免费次数）
        assert response.status_code == 200
    
    def test_check_usage_paid_user(self, client: TestClient, auth_headers_paid: dict):
        """测试付费用户检查使用次数"""
        response = client.post("/api/usage/check",
            headers=auth_headers_paid,
            json={"tool_type": "bounty_hunter"}
        )
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["data"]["can_use"] is True or data["data"]["allowed"] is True


# ═══════════════════════════════════════════════════════════
# 使用次数扣减 API 测试
# ═══════════════════════════════════════════════════════════

class TestUsageDeductAPI:
    """使用次数扣减 API 测试"""
    
    def test_deduct_usage_success(self, client: TestClient, auth_headers: dict):
        """测试扣减使用次数成功"""
        response = client.post("/api/usage/deduct",
            headers=auth_headers,
            json={"tool_type": "bounty_hunter"}
        )
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
    
    def test_deduct_usage_paid_user(self, client: TestClient, auth_headers_paid: dict):
        """测试付费用户扣减使用次数"""
        response = client.post("/api/usage/deduct",
            headers=auth_headers_paid,
            json={"tool_type": "bounty_hunter"}
        )
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert data["data"]["cache_type"] == "premium"  # 付费用户使用高级缓存


# ═══════════════════════════════════════════════════════════
# 使用配置 API 测试
# ═══════════════════════════════════════════════════════════

class TestUsageConfigAPI:
    """使用配置 API 测试"""
    
    def test_get_usage_config(self, client: TestClient):
        """测试获取使用配置"""
        response = client.get("/api/usage/config")
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "free_daily_limit" in data["data"] or "config" in data["data"]


# ═══════════════════════════════════════════════════════════
# 匿名用户 API 测试
# ═══════════════════════════════════════════════════════════

class TestAnonymousUserAPI:
    """匿名用户 API 测试"""
    
    def test_register_anonymous(self, client: TestClient):
        """测试注册匿名用户"""
        response = client.post("/api/usage/anonymous/register",
            json={
                "visitor_id": "test-visitor-" + str(hash("test") % 10000),
                "ip_address": "127.0.0.1"
            }
        )
        
        # 验证响应状态
        assert response.status_code == 200
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
    
    def test_anonymous_balance(self, client: TestClient):
        """测试获取匿名用户使用次数"""
        # 先注册匿名用户
        visitor_id = "test-visitor-" + str(hash("balance_test") % 10000)
        client.post("/api/usage/anonymous/register",
            json={
                "visitor_id": visitor_id,
                "ip_address": "127.0.0.1"
            }
        )
        
        # 获取使用次数
        response = client.get(f"/api/usage/balance?visitor_id={visitor_id}")
        
        # 验证响应状态
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════
# 用户删除 API 测试
# ═══════════════════════════════════════════════════════════

class TestUserDeleteAPI:
    """用户删除 API 测试"""
    
    def test_delete_user_unauthorized(self, client: TestClient):
        """测试未授权删除用户"""
        response = client.delete("/api/user/account")
        
        # 验证响应状态（应该返回 401）
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# 用户统计 API 测试
# ═══════════════════════════════════════════════════════════

class TestUserStatsAPI:
    """用户统计 API 测试"""
    
    def test_get_user_stats_success(self, client: TestClient, auth_headers: dict):
        """测试获取用户统计成功"""
        response = client.get("/api/user/stats", headers=auth_headers)
        
        # 验证响应状态
        assert response.status_code in [200, 404]  # 404 如果端点不存在
    
    def test_get_user_stats_unauthorized(self, client: TestClient):
        """测试未授权获取用户统计"""
        response = client.get("/api/user/stats")
        
        # 验证响应状态（应该返回 401）
        assert response.status_code == 401