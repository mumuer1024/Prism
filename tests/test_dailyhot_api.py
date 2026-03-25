# -*- coding: utf-8 -*-
"""
DailyHotApi API 端点测试

测试分类配置相关的 REST API 端点
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database.models import DailyHotCategoryConfig, User


class TestDailyHotCategoriesAPI:
    """测试 DailyHotApi 分类配置 API"""

    def test_get_categories_unauthenticated(self, client: TestClient):
        """测试未登录访问返回 401"""
        response = client.get("/api/user-config/dailyhot/categories")
        assert response.status_code == 401

    def test_get_categories_success(self, client: TestClient, auth_headers: dict):
        """测试登录用户获取分类配置"""
        response = client.get(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "enabled" in data
        assert "available" in data
        assert isinstance(data["enabled"], list)
        assert isinstance(data["available"], list)

    def test_get_categories_default_values(self, client: TestClient, auth_headers: dict):
        """测试新用户获取默认分类配置"""
        response = client.get(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证默认启用 tech 和 dev
        assert "tech" in data["enabled"]
        assert "dev" in data["enabled"]

    def test_get_categories_available_structure(self, client: TestClient, auth_headers: dict):
        """测试可用分类结构"""
        response = client.get(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证 available 结构
        assert len(data["available"]) == 4

        for cat in data["available"]:
            assert "key" in cat
            assert "label" in cat
            assert "platforms" in cat
            assert isinstance(cat["platforms"], list)

    def test_update_categories_success(self, client: TestClient, auth_headers: dict):
        """测试成功更新分类配置"""
        response = client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": ["tech", "dev", "news"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "已更新" in data["message"]

    def test_update_categories_verify_persisted(self, client: TestClient, auth_headers: dict):
        """测试更新后配置已持久化"""
        # 更新配置
        client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": ["tech", "news"]}
        )

        # 重新获取验证
        response = client.get(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers
        )

        data = response.json()
        assert "tech" in data["enabled"]
        assert "news" in data["enabled"]
        assert "dev" not in data["enabled"]

    def test_update_categories_invalid(self, client: TestClient, auth_headers: dict):
        """测试无效分类返回 400"""
        response = client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": ["tech", "invalid_category"]}
        )

        assert response.status_code == 400

    def test_update_categories_empty(self, client: TestClient, auth_headers: dict):
        """测试空列表返回验证错误"""
        response = client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": []}
        )

        # Pydantic 验证返回 422 (Unprocessable Entity)
        assert response.status_code == 422

    def test_update_categories_unauthenticated(self, client: TestClient):
        """测试未登录更新返回 401"""
        response = client.put(
            "/api/user-config/dailyhot/categories",
            json={"categories": ["tech"]}
        )

        assert response.status_code == 401


class TestDailyHotCategoryMapAPI:
    """测试分类映射公开 API"""

    def test_category_map_public(self, client: TestClient):
        """测试公开接口无需认证"""
        response = client.get("/api/user-config/dailyhot/category-map")

        assert response.status_code == 200

    def test_category_map_structure(self, client: TestClient):
        """测试分类映射响应结构"""
        response = client.get("/api/user-config/dailyhot/category-map")

        assert response.status_code == 200
        data = response.json()

        assert "categories" in data
        assert len(data["categories"]) == 4

    def test_category_map_content(self, client: TestClient):
        """测试分类映射内容正确"""
        response = client.get("/api/user-config/dailyhot/category-map")

        data = response.json()
        categories = data["categories"]

        # 验证包含所有分类
        keys = [c["key"] for c in categories]
        assert "tech" in keys
        assert "dev" in keys
        assert "news" in keys
        assert "entertainment" in keys

        # 验证每个分类有平台列表
        for cat in categories:
            assert len(cat["platforms"]) > 0
            # 验证平台结构
            for platform in cat["platforms"]:
                assert "key" in platform
                assert "name" in platform

    def test_category_map_tech_platforms(self, client: TestClient):
        """测试科技分类平台列表"""
        response = client.get("/api/user-config/dailyhot/category-map")

        data = response.json()
        tech_cat = next((c for c in data["categories"] if c["key"] == "tech"), None)

        assert tech_cat is not None
        assert tech_cat["label"] == "科技数字"

        platform_keys = [p["key"] for p in tech_cat["platforms"]]
        assert "sspai" in platform_keys
        assert "ithome" in platform_keys

    def test_category_map_dev_platforms(self, client: TestClient):
        """测试开发者分类平台列表"""
        response = client.get("/api/user-config/dailyhot/category-map")

        data = response.json()
        dev_cat = next((c for c in data["categories"] if c["key"] == "dev"), None)

        assert dev_cat is not None
        assert dev_cat["label"] == "开发者"

        platform_keys = [p["key"] for p in dev_cat["platforms"]]
        assert "juejin" in platform_keys
        assert "v2ex" in platform_keys


class TestDailyHotAPIIntegration:
    """API 集成测试"""

    def test_full_workflow(self, client: TestClient, auth_headers: dict):
        """测试完整工作流：获取 → 更新 → 验证"""
        # 1. 获取初始配置
        response = client.get(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers
        )
        assert response.status_code == 200
        initial_data = response.json()

        # 2. 更新配置
        response = client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": ["tech", "dev", "news", "entertainment"]}
        )
        assert response.status_code == 200

        # 3. 验证更新生效
        response = client.get(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers
        )
        assert response.status_code == 200
        updated_data = response.json()

        assert len(updated_data["enabled"]) == 4

    def test_different_users_independent(self, client: TestClient, auth_headers: dict, registered_user_2: dict):
        """测试不同用户配置独立"""
        # 用户 1 更新配置
        client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": ["tech"]}
        )

        # 用户 2 获取配置
        auth_headers_2 = {
            "Authorization": f"{registered_user_2['token_type']} {registered_user_2['access_token']}"
        }
        response = client.get(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers_2
        )

        data = response.json()
        # 用户 2 应该有默认配置，不受用户 1 影响
        assert "tech" in data["enabled"]
        assert "dev" in data["enabled"]


class TestDailyHotAPIEdgeCases:
    """边界情况测试"""

    def test_update_same_categories(self, client: TestClient, auth_headers: dict):
        """测试更新相同配置"""
        # 第一次更新
        client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": ["tech", "dev"]}
        )

        # 第二次更新相同配置
        response = client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": ["tech", "dev"]}
        )

        assert response.status_code == 200

    def test_update_single_category(self, client: TestClient, auth_headers: dict):
        """测试只启用一个分类"""
        response = client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": ["news"]}
        )

        assert response.status_code == 200

        # 验证只有一个分类启用
        response = client.get(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers
        )
        data = response.json()
        assert data["enabled"] == ["news"]

    def test_update_all_categories(self, client: TestClient, auth_headers: dict):
        """测试启用所有分类"""
        response = client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"categories": ["tech", "dev", "news", "entertainment"]}
        )

        assert response.status_code == 200

        response = client.get(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers
        )
        data = response.json()
        assert len(data["enabled"]) == 4

    def test_malformed_request(self, client: TestClient, auth_headers: dict):
        """测试格式错误的请求"""
        response = client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers,
            json={"wrong_field": ["tech"]}
        )

        assert response.status_code == 422  # Validation error

    def test_missing_request_body(self, client: TestClient, auth_headers: dict):
        """测试缺少请求体"""
        response = client.put(
            "/api/user-config/dailyhot/categories",
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error