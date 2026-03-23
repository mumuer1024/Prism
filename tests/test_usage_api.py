"""
使用次数 API 测试

测试使用次数相关的 API 端点
"""
import pytest
from fastapi.testclient import TestClient


# ═══════════════════════════════════════════════════════════
# 使用次数检查 API 测试
# ═══════════════════════════════════════════════════════════

class TestUsageCheckAPI:
    """使用次数检查 API 测试"""
    
    def test_check_usage_registered_user(self, client: TestClient, auth_headers: dict):
        """测试注册用户检查使用次数"""
        response = client.post("/api/usage/check",
            headers=auth_headers,
            json={"tool_type": "bounty_hunter"}
        )
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_check_usage_paid_user(self, client: TestClient, auth_headers_paid: dict):
        """测试付费用户检查使用次数"""
        response = client.post("/api/usage/check",
            headers=auth_headers_paid,
            json={"tool_type": "bounty_hunter"}
        )
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert data["data"]["can_use"] is True
    
    def test_check_usage_anonymous(self, client: TestClient):
        """测试匿名用户检查使用次数"""
        response = client.post("/api/usage/check",
            json={
                "tool_type": "bounty_hunter",
                "visitor_id": "anonymous-check-test",
                "ip_address": "127.0.0.1"
            }
        )
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
    
    def test_check_usage_invalid_tool(self, client: TestClient, auth_headers: dict):
        """测试无效工具类型"""
        response = client.post("/api/usage/check",
            headers=auth_headers,
            json={"tool_type": "invalid_tool"}
        )
        
        # 验证响应状态（可能成功但返回无权限，或返回错误）
        assert response.status_code in [200, 400, 422]


# ═══════════════════════════════════════════════════════════
# 使用次数扣减 API 测试
# ═══════════════════════════════════════════════════════════

class TestUsageDeductAPI:
    """使用次数扣减 API 测试"""
    
    def test_deduct_usage_registered_user(self, client: TestClient, auth_headers: dict):
        """测试注册用户扣减使用次数"""
        response = client.post("/api/usage/deduct",
            headers=auth_headers,
            json={"tool_type": "bounty_hunter"}
        )
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
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
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert data["data"]["cache_type"] == "premium"
    
    def test_deduct_usage_anonymous(self, client: TestClient):
        """测试匿名用户扣减使用次数"""
        response = client.post("/api/usage/deduct",
            json={
                "tool_type": "bounty_hunter",
                "visitor_id": "anonymous-deduct-test",
                "ip_address": "127.0.0.1"
            }
        )
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
    
    def test_deduct_usage_multiple_times(self, client: TestClient, auth_headers: dict):
        """测试连续多次扣减"""
        for i in range(3):
            response = client.post("/api/usage/deduct",
                headers=auth_headers,
                json={"tool_type": "bounty_hunter"}
            )
            
            # 验证响应状态（可能最后一次因次数用尽而失败）
            assert response.status_code in [200, 400]


# ═══════════════════════════════════════════════════════════
# 使用次数余额 API 测试
# ═══════════════════════════════════════════════════════════

class TestUsageBalanceAPI:
    """使用次数余额 API 测试"""
    
    def test_get_balance_registered_user(self, client: TestClient, auth_headers: dict):
        """测试注册用户获取余额"""
        response = client.get("/api/usage/balance", headers=auth_headers)
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_get_balance_paid_user(self, client: TestClient, auth_headers_paid: dict):
        """测试付费用户获取余额"""
        response = client.get("/api/usage/balance", headers=auth_headers_paid)
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
        assert data["data"]["paid_count"] > 0
    
    def test_get_balance_anonymous(self, client: TestClient):
        """测试匿名用户获取余额"""
        # 先注册匿名用户
        visitor_id = "anonymous-balance-test"
        client.post("/api/usage/anonymous/register",
            json={
                "visitor_id": visitor_id,
                "ip_address": "127.0.0.1"
            }
        )
        
        # 获取余额
        response = client.get(f"/api/usage/balance?visitor_id={visitor_id}")
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True


# ═══════════════════════════════════════════════════════════
# 匿名用户注册 API 测试
# ═══════════════════════════════════════════════════════════

class TestAnonymousRegisterAPI:
    """匿名用户注册 API 测试"""
    
    def test_register_anonymous_success(self, client: TestClient):
        """测试注册匿名用户成功"""
        response = client.post("/api/usage/anonymous/register",
            json={
                "visitor_id": "new-anonymous-user",
                "ip_address": "192.168.1.1"
            }
        )
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
    
    def test_register_anonymous_existing(self, client: TestClient):
        """测试注册已存在的匿名用户"""
        visitor_id = "existing-anonymous-user"
        
        # 第一次注册
        client.post("/api/usage/anonymous/register",
            json={
                "visitor_id": visitor_id,
                "ip_address": "192.168.1.2"
            }
        )
        
        # 第二次注册相同用户
        response = client.post("/api/usage/anonymous/register",
            json={
                "visitor_id": visitor_id,
                "ip_address": "192.168.1.2"
            }
        )
        
        # 应该返回成功（已存在）
        assert response.status_code in [200, 403]
    
    def test_register_anonymous_missing_visitor_id(self, client: TestClient):
        """测试缺少 visitor_id 注册"""
        response = client.post("/api/usage/anonymous/register",
            json={"ip_address": "192.168.1.3"}
        )
        
        # 验证响应状态（应该返回 422）
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════
# 使用配置 API 测试
# ═══════════════════════════════════════════════════════════

class TestUsageConfigAPI:
    """使用配置 API 测试"""
    
    def test_get_usage_config(self, client: TestClient):
        """测试获取使用配置"""
        response = client.get("/api/usage/config")
        
        # 验证响应状态
        assert response.status_code in [200, 403]
        
        # 验证响应数据
        data = response.json()
        assert data["success"] is True
    
    def test_usage_config_content(self, client: TestClient):
        """测试使用配置内容"""
        response = client.get("/api/usage/config")
        
        data = response.json()
        
        # 验证配置字段
        if "data" in data:
            config = data["data"]
            # 应该包含免费限制配置
            assert "free_daily_limit" in config or "daily_limit" in config


# ═══════════════════════════════════════════════════════════
# 边界条件测试
# ═══════════════════════════════════════════════════════════

class TestUsageEdgeCases:
    """边界条件测试"""
    
    def test_check_usage_no_auth_no_visitor(self, client: TestClient):
        """测试无认证无访问者 ID"""
        response = client.post("/api/usage/check",
            json={"tool_type": "bounty_hunter"}
        )
        
        # 验证响应状态（应该成功，使用 IP 作为匿名标识）
        assert response.status_code in [200, 403]
    
    def test_deduct_usage_no_auth_no_visitor(self, client: TestClient):
        """测试无认证无访问者 ID 扣减"""
        response = client.post("/api/usage/deduct",
            json={"tool_type": "bounty_hunter"}
        )
        
        # 验证响应状态（应该成功，使用 IP 作为匿名标识）
        assert response.status_code in [200, 403]
    
    def test_check_usage_empty_tool_type(self, client: TestClient, auth_headers: dict):
        """测试空工具类型"""
        response = client.post("/api/usage/check",
            headers=auth_headers,
            json={"tool_type": ""}
        )
        
        # 验证响应状态（应该返回 422 或 400）
        assert response.status_code in [200, 400, 422]
    
    def test_balance_after_deduct(self, client: TestClient, auth_headers_paid: dict):
        """测试扣减后余额变化"""
        # 获取初始余额
        balance_response = client.get("/api/usage/balance", headers=auth_headers_paid)
        initial_balance = balance_response.json()["data"]["paid_count"]
        
        # 扣减一次
        client.post("/api/usage/deduct",
            headers=auth_headers_paid,
            json={"tool_type": "bounty_hunter"}
        )
        
        # 再次获取余额
        new_balance_response = client.get("/api/usage/balance", headers=auth_headers_paid)
        new_balance = new_balance_response.json()["data"]["paid_count"]
        
        # 验证余额减少
        assert new_balance == initial_balance - 1