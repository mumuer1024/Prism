# -*- coding: utf-8 -*-
"""
DailyHotApi API 端点测试 - v2.1 激活码架构

测试分类配置相关的 REST API 端点
使用 device_id 认证替代 JWT
"""

import pytest
from fastapi.testclient import TestClient

from src.database.models import DailyHotCategoryConfig, ActivationCode, Device


class TestDailyHotCategoriesAPI:
    """测试 DailyHotApi 分类配置 API"""

    def test_get_categories_success(self, client: TestClient, test_device: dict):
        """测试获取分类配置"""
        device_id = test_device["device_id"]

        response = client.post(
            "/api/user-config/dailyhot/categories",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "enabled" in data
        assert "available" in data
        assert isinstance(data["enabled"], list)
        assert isinstance(data["available"], list)

    def test_get_categories_default_values(self, client: TestClient, test_device: dict):
        """测试新用户获取默认分类配置"""
        device_id = test_device["device_id"]

        response = client.post(
            "/api/user-config/dailyhot/categories",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证默认启用 tech 和 dev
        assert "tech" in data["enabled"]
        assert "dev" in data["enabled"]

    def test_get_categories_available_structure(self, client: TestClient, test_device: dict):
        """测试可用分类结构"""
        device_id = test_device["device_id"]

        response = client.post(
            "/api/user-config/dailyhot/categories",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证 available 结构
        for cat in data["available"]:
            assert "key" in cat
            assert "label" in cat
            assert "platforms" in cat
            assert isinstance(cat["platforms"], list)

    def test_update_categories_success(self, client: TestClient, test_device: dict):
        """测试成功更新分类配置"""
        device_id = test_device["device_id"]

        response = client.put(
            "/api/user-config/dailyhot/categories",
            json={
                "device_id": device_id,
                "categories": ["tech", "dev", "news"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "已更新" in data["message"]

    def test_update_categories_and_verify(self, client: TestClient, test_device: dict):
        """测试更新后验证配置"""
        device_id = test_device["device_id"]

        # 更新配置
        client.put(
            "/api/user-config/dailyhot/categories",
            json={
                "device_id": device_id,
                "categories": ["tech", "news"]
            }
        )

        # 获取配置验证
        response = client.post(
            "/api/user-config/dailyhot/categories",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "tech" in data["enabled"]
        assert "news" in data["enabled"]

    def test_get_categories_invalid_device(self, client: TestClient):
        """测试无效设备"""
        response = client.post(
            "/api/user-config/dailyhot/categories",
            json={"device_id": "INVALID-DEVICE"}
        )

        assert response.status_code == 401
        assert "设备未激活" in response.json()["detail"]

    def test_get_categories_no_device_id(self, client: TestClient):
        """测试缺少 device_id"""
        response = client.post(
            "/api/user-config/dailyhot/categories",
            json={}
        )

        # FastAPI 验证错误返回 422
        assert response.status_code == 422

    def test_update_categories_empty_list(self, client: TestClient, test_device: dict):
        """测试更新空分类列表"""
        device_id = test_device["device_id"]

        response = client.put(
            "/api/user-config/dailyhot/categories",
            json={
                "device_id": device_id,
                "categories": []
            }
        )

        # 空列表应该失败（min_length=1）
        assert response.status_code == 422

    def test_get_category_map_public(self, client: TestClient):
        """测试获取分类映射（公开接口）"""
        response = client.get("/api/user-config/dailyhot/category-map")

        assert response.status_code == 200
        data = response.json()

        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0

        for cat in data["categories"]:
            assert "key" in cat
            assert "label" in cat
            assert "platforms" in cat