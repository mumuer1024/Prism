# -*- coding: utf-8 -*-
"""
预设广场 API 测试 - v2.1 激活码架构

测试模板列表、详情、导入等接口
使用 device_id 认证替代 JWT
"""

import pytest
from fastapi.testclient import TestClient

from src.database.models import MarketplaceTemplate, ActivationCode, Device


# ═══════════════════════════════════════════════════════════
# 模板列表测试
# ═══════════════════════════════════════════════════════════

class TestTemplateList:
    """模板列表接口测试"""

    def test_list_templates_success(self, client: TestClient, test_template: MarketplaceTemplate):
        """测试获取模板列表"""
        response = client.get("/api/marketplace/templates")

        assert response.status_code == 200
        data = response.json()

        assert "templates" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["templates"]) >= 1

    def test_list_templates_with_tool_type_filter(self, client: TestClient, db_session):
        """测试按工具类型筛选"""
        # 创建不同类型的模板
        template_mission = MarketplaceTemplate(
            title="Mission模板",
            description="Mission模板描述",
            tool_type="mission",
            prompt_content="Mission {{DATA}}",
            is_published=True,
            is_official=True,
        )
        template_bounty = MarketplaceTemplate(
            title="Bounty模板",
            description="Bounty模板描述",
            tool_type="bounty_v2ex",
            prompt_content="Bounty {{DATA}}",
            is_published=True,
            is_official=True,
        )
        db_session.add_all([template_mission, template_bounty])
        db_session.commit()

        # 筛选 mission
        response = client.get("/api/marketplace/templates?tool_type=mission")

        assert response.status_code == 200
        data = response.json()
        assert all(t["tool_type"] == "mission" for t in data["templates"])

    def test_list_templates_invalid_tool_type(self, client: TestClient):
        """测试无效工具类型"""
        response = client.get("/api/marketplace/templates?tool_type=invalid_type")

        assert response.status_code == 400
        assert "无效的 tool_type" in response.json()["detail"]

    def test_list_templates_pagination(self, client: TestClient, db_session):
        """测试分页参数"""
        # 创建多个模板
        for i in range(5):
            template = MarketplaceTemplate(
                title=f"模板{i}",
                description=f"描述{i}",
                tool_type="mission",
                prompt_content=f"内容{i}",
                is_published=True,
            )
            db_session.add(template)
        db_session.commit()

        # 测试 skip 和 limit
        response = client.get("/api/marketplace/templates?skip=2&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["templates"]) == 2


# ═══════════════════════════════════════════════════════════
# 模板详情测试
# ═══════════════════════════════════════════════════════════

class TestTemplateDetail:
    """模板详情接口测试"""

    def test_get_template_detail_success(self, client: TestClient, test_template: MarketplaceTemplate):
        """测试获取模板详情"""
        response = client.get(f"/api/marketplace/templates/{test_template.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_template.id
        assert data["title"] == test_template.title
        assert data["prompt_content"] == test_template.prompt_content

    def test_get_template_detail_not_found(self, client: TestClient):
        """测试模板不存在"""
        response = client.get("/api/marketplace/templates/99999")

        assert response.status_code == 404
        assert "模板不存在" in response.json()["detail"]

    def test_get_template_detail_unpublished(self, client: TestClient, db_session):
        """测试未发布模板不可见"""
        template = MarketplaceTemplate(
            title="未发布模板",
            description="未发布描述",
            tool_type="mission",
            prompt_content="内容",
            is_published=False,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        response = client.get(f"/api/marketplace/templates/{template.id}")

        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════
# 模板导入测试
# ═══════════════════════════════════════════════════════════

class TestTemplateImport:
    """模板导入接口测试"""

    def test_import_template_success(self, client: TestClient, test_device: dict, test_template: MarketplaceTemplate, db_session):
        """测试成功导入模板"""
        device_id = test_device["device_id"]

        response = client.post(
            f"/api/marketplace/templates/{test_template.id}/import",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["tool_type"] == test_template.tool_type
        assert data["template_title"] == test_template.title

    def test_import_template_no_device_id(self, client: TestClient, test_template: MarketplaceTemplate):
        """测试缺少 device_id（FastAPI 返回 422 验证错误）"""
        response = client.post(
            f"/api/marketplace/templates/{test_template.id}/import",
            json={}
        )

        # FastAPI 验证错误返回 422
        assert response.status_code == 422

    def test_import_template_invalid_device(self, client: TestClient, test_template: MarketplaceTemplate):
        """测试无效设备"""
        response = client.post(
            f"/api/marketplace/templates/{test_template.id}/import",
            json={"device_id": "INVALID-DEVICE"}
        )

        assert response.status_code == 401
        assert "设备未激活" in response.json()["detail"]

    def test_import_template_not_found(self, client: TestClient, test_device: dict):
        """测试导入不存在的模板"""
        device_id = test_device["device_id"]

        response = client.post(
            "/api/marketplace/templates/99999/import",
            json={"device_id": device_id}
        )

        assert response.status_code == 404

    def test_import_template_no_quota(self, client: TestClient, db_session):
        """测试次数不足无法导入"""
        # 创建激活码（次数为0）
        activation = ActivationCode(
            code="PRISM-IMPORT-NOQ",
            quota=10,
            remaining=0,  # 使用 remaining 字段
            is_activated=True,
        )
        db_session.add(activation)
        db_session.commit()
        db_session.refresh(activation)

        # 绑定设备
        device = Device(
            device_id="DEV-IMPORT-NOQ",
            code_id=activation.id,
        )
        db_session.add(device)
        db_session.commit()

        # 创建模板
        template = MarketplaceTemplate(
            title="测试模板",
            description="测试描述",
            tool_type="mission",
            prompt_content="内容",
            is_published=True,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        response = client.post(
            f"/api/marketplace/templates/{template.id}/import",
            json={"device_id": "DEV-IMPORT-NOQ"}
        )

        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════
# 公开接口测试（无需认证）
# ═══════════════════════════════════════════════════════════

class TestPublicEndpoints:
    """公开接口测试"""

    def test_list_templates_no_auth(self, client: TestClient, test_template: MarketplaceTemplate):
        """测试模板列表无需认证"""
        response = client.get("/api/marketplace/templates")

        assert response.status_code == 200

    def test_get_template_detail_no_auth(self, client: TestClient, test_template: MarketplaceTemplate):
        """测试模板详情无需认证"""
        response = client.get(f"/api/marketplace/templates/{test_template.id}")

        assert response.status_code == 200