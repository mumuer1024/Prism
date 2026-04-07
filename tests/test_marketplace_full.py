# -*- coding: utf-8 -*-
"""
预设广场完整流程测试 - v2.1 激活码架构

测试模板浏览、筛选、导入完整流程
使用 device_id 认证替代 JWT
"""

import pytest
from fastapi.testclient import TestClient

from src.database.models import MarketplaceTemplate, ActivationCode, Device


# ═══════════════════════════════════════════════════════════
# 模板浏览完整流程测试
# ═══════════════════════════════════════════════════════════

class TestTemplateBrowseFlow:
    """模板浏览完整流程"""

    def test_browse_all_templates(self, client: TestClient, db_session):
        """测试浏览所有模板"""
        # 创建多个模板
        for i in range(3):
            template = MarketplaceTemplate(
                title=f"模板{i}",
                description=f"描述{i}",
                tool_type="mission",
                prompt_content=f"内容{i}",
                is_published=True,
                is_official=True if i == 0 else False,
            )
            db_session.add(template)
        db_session.commit()

        response = client.get("/api/marketplace/templates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    def test_browse_by_tool_type(self, client: TestClient, db_session):
        """测试按类型筛选模板"""
        # 创建不同类型的模板
        templates = [
            MarketplaceTemplate(title="Mission模板", description="M描述", tool_type="mission", prompt_content="M", is_published=True),
            MarketplaceTemplate(title="Bounty模板", description="B描述", tool_type="bounty_v2ex", prompt_content="B", is_published=True),
            MarketplaceTemplate(title="Alpha模板", description="A描述", tool_type="alpha", prompt_content="A", is_published=True),
        ]
        for t in templates:
            db_session.add(t)
        db_session.commit()

        # 筛选 mission
        response = client.get("/api/marketplace/templates?tool_type=mission")
        assert response.status_code == 200
        data = response.json()
        assert len(data["templates"]) >= 1
        assert all(t["tool_type"] == "mission" for t in data["templates"])

    def test_view_template_detail(self, client: TestClient, db_session):
        """测试查看模板详情"""
        template = MarketplaceTemplate(
            title="详情测试模板",
            description="详情描述",
            tool_type="mission",
            prompt_content="详情内容 {{DATA}}",
            is_published=True,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        response = client.get(f"/api/marketplace/templates/{template.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "详情测试模板"
        assert data["prompt_content"] == "详情内容 {{DATA}}"


# ═══════════════════════════════════════════════════════════
# 模板导入完整流程测试
# ═══════════════════════════════════════════════════════════

class TestTemplateImportFlow:
    """模板导入完整流程"""

    def test_full_import_flow(self, client: TestClient, test_device: dict, db_session):
        """测试完整导入流程"""
        device_id = test_device["device_id"]

        # 1. 创建模板
        template = MarketplaceTemplate(
            title="导入测试模板",
            description="导入描述",
            tool_type="mission",
            prompt_content="导入内容 {{DATA}}",
            is_published=True,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        # 2. 导入模板
        response = client.post(
            f"/api/marketplace/templates/{template.id}/import",
            json={"device_id": device_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tool_type"] == "mission"

    def test_import_multiple_templates(self, client: TestClient, test_device: dict, db_session):
        """测试导入多个模板"""
        device_id = test_device["device_id"]

        # 创建多个模板
        tool_types = ["mission", "bounty_v2ex", "alpha"]
        templates = []
        for tt in tool_types:
            template = MarketplaceTemplate(
                title=f"{tt}模板",
                description=f"{tt}描述",
                tool_type=tt,
                prompt_content=f"{tt}内容",
                is_published=True,
            )
            db_session.add(template)
            templates.append(template)
        db_session.commit()

        # 导入每个模板
        for template in templates:
            db_session.refresh(template)
            response = client.post(
                f"/api/marketplace/templates/{template.id}/import",
                json={"device_id": device_id}
            )
            assert response.status_code == 200


# ═══════════════════════════════════════════════════════════
# 边界情况测试
# ═══════════════════════════════════════════════════════════

class TestMarketplaceEdgeCases:
    """边界情况测试"""

    def test_import_unpublished_template(self, client: TestClient, test_device: dict, db_session):
        """测试导入未发布模板"""
        device_id = test_device["device_id"]

        template = MarketplaceTemplate(
            title="未发布模板",
            description="未发布",
            tool_type="mission",
            prompt_content="内容",
            is_published=False,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        response = client.post(
            f"/api/marketplace/templates/{template.id}/import",
            json={"device_id": device_id}
        )

        assert response.status_code == 404

    def test_import_with_no_quota(self, client: TestClient, db_session):
        """测试次数不足导入失败"""
        # 创建次数为0的激活码
        activation = ActivationCode(
            code="PRISM-FULL-NOQ",
            quota=10,
            remaining=0,
            is_activated=True,
        )
        db_session.add(activation)
        db_session.commit()
        db_session.refresh(activation)

        device = Device(
            device_id="DEV-FULL-NOQ",
            code_id=activation.id,
        )
        db_session.add(device)
        db_session.commit()

        template = MarketplaceTemplate(
            title="次数不足模板",
            description="描述",
            tool_type="mission",
            prompt_content="内容",
            is_published=True,
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)

        response = client.post(
            f"/api/marketplace/templates/{template.id}/import",
            json={"device_id": "DEV-FULL-NOQ"}
        )

        assert response.status_code == 403

    def test_pagination_edge_cases(self, client: TestClient, db_session):
        """测试分页边界"""
        # 创建模板
        for i in range(10):
            template = MarketplaceTemplate(
                title=f"分页{i}",
                description=f"描述{i}",
                tool_type="mission",
                prompt_content=f"内容{i}",
                is_published=True,
            )
            db_session.add(template)
        db_session.commit()

        # 测试 skip 超出范围
        response = client.get("/api/marketplace/templates?skip=100&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["templates"]) == 0

        # 测试 limit 超大
        response = client.get("/api/marketplace/templates?limit=100")
        assert response.status_code == 200