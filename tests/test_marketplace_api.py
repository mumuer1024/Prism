# -*- coding: utf-8 -*-
"""
预设广场 API 测试

测试模板列表、详情、导入等功能
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from src.database.models import User, MarketplaceTemplate, UserPrompt


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def test_templates(db_session):
    """创建测试模板"""
    templates = []

    template_data = [
        {
            "title": "科技日报模板",
            "description": "适用于科技行业的日报生成",
            "tool_type": "mission",
            "prompt_content": "你是一个科技分析师，请分析以下内容...",
            "tags": '["科技", "日报"]',
            "is_official": True,
            "is_published": True,
        },
        {
            "title": "Web3 分析模板",
            "description": "适用于 Web3/区块链领域分析",
            "tool_type": "alpha",
            "prompt_content": "你是一个 Web3 分析师...",
            "tags": '["Web3", "区块链"]',
            "is_official": True,
            "is_published": True,
        },
        {
            "title": "未发布模板",
            "description": "这是一个未发布的模板",
            "tool_type": "mission",
            "prompt_content": "未发布内容...",
            "tags": '[]',
            "is_official": False,
            "is_published": False,
        },
    ]

    for data in template_data:
        template = MarketplaceTemplate(**data)
        db_session.add(template)
        templates.append(template)

    db_session.commit()
    for t in templates:
        db_session.refresh(t)

    return templates


@pytest.fixture
def paid_user_with_token(db_session):
    """创建付费用户并返回token"""
    from src.auth.utils.password_handler import hash_password
    from src.auth.utils.jwt_handler import create_access_token
    import secrets

    password_hash = hash_password("TestPassword123!")
    invite_code = "PAID-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

    user = User(
        email="paid@test.com",
        password_hash=password_hash,
        nickname="PaidUser",
        invite_code=invite_code,
        usage_count=100,  # 有使用次数
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        usage_count=user.usage_count
    )

    return {
        "user": user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }


# ═══════════════════════════════════════════════════════════
# 模板列表测试
# ═══════════════════════════════════════════════════════════

class TestTemplateList:
    """模板列表测试"""

    def test_list_templates(self, client, test_templates):
        """测试获取模板列表"""
        response = client.get("/api/marketplace/templates")
        assert response.status_code == 200

        data = response.json()
        assert "templates" in data
        assert "total" in data

        # 只返回已发布的模板
        for t in data["templates"]:
            assert t["is_published"] is True

    def test_list_templates_by_tool_type(self, client, test_templates):
        """测试按工具类型筛选"""
        response = client.get("/api/marketplace/templates?tool_type=mission")
        assert response.status_code == 200

        data = response.json()
        for t in data["templates"]:
            assert t["tool_type"] == "mission"

    def test_list_templates_pagination(self, client, test_templates):
        """测试分页"""
        response = client.get("/api/marketplace/templates?skip=0&limit=1")
        assert response.status_code == 200

        data = response.json()
        assert len(data["templates"]) <= 1

    def test_list_templates_no_content(self, client, test_templates):
        """测试列表不返回 prompt_content"""
        response = client.get("/api/marketplace/templates")
        assert response.status_code == 200

        data = response.json()
        for t in data["templates"]:
            # 列表接口不应返回 prompt_content
            assert t.get("prompt_content") is None


# ═══════════════════════════════════════════════════════════
# 模板详情测试
# ═══════════════════════════════════════════════════════════

class TestTemplateDetail:
    """模板详情测试"""

    def test_get_template_detail(self, client, test_templates):
        """测试获取模板详情"""
        template_id = test_templates[0].id
        response = client.get(f"/api/marketplace/templates/{template_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == template_id
        assert data["title"] == test_templates[0].title
        # 详情接口应返回 prompt_content
        assert data["prompt_content"] is not None

    def test_get_template_detail_not_found(self, client):
        """测试获取不存在的模板"""
        response = client.get("/api/marketplace/templates/99999")
        assert response.status_code == 404

    def test_get_unpublished_template_denied(self, client, test_templates):
        """测试获取未发布模板被拒绝"""
        # 找到未发布的模板
        unpublished = None
        for t in test_templates:
            if not t.is_published:
                unpublished = t
                break

        if unpublished:
            response = client.get(f"/api/marketplace/templates/{unpublished.id}")
            assert response.status_code == 404


# ═══════════════════════════════════════════════════════════
# 模板导入测试
# ═══════════════════════════════════════════════════════════

class TestTemplateImport:
    """模板导入测试"""

    def test_import_template_success(self, client, test_templates, paid_user_with_token, db_session):
        """测试成功导入模板"""
        template_id = test_templates[0].id
        response = client.post(
            f"/api/marketplace/templates/{template_id}/import",
            headers=paid_user_with_token["headers"]
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["tool_type"] == test_templates[0].tool_type
        assert data["template_title"] == test_templates[0].title

    def test_import_template_not_found(self, client, paid_user_with_token):
        """测试导入不存在的模板"""
        response = client.post(
            "/api/marketplace/templates/99999/import",
            headers=paid_user_with_token["headers"]
        )
        assert response.status_code == 404

    def test_import_template_unauthorized(self, client, test_templates):
        """测试未登录导入模板"""
        template_id = test_templates[0].id
        response = client.post(f"/api/marketplace/templates/{template_id}/import")
        assert response.status_code == 401

    def test_import_template_no_usage(self, client, test_templates, db_session):
        """测试无使用次数导入模板"""
        from src.auth.utils.password_handler import hash_password
        from src.auth.utils.jwt_handler import create_access_token
        import secrets

        # 创建无使用次数的用户
        password_hash = hash_password("TestPassword123!")
        invite_code = "FREE-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

        user = User(
            email="free@test.com",
            password_hash=password_hash,
            nickname="FreeUser",
            invite_code=invite_code,
            usage_count=0,  # 无使用次数
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            usage_count=user.usage_count
        )

        template_id = test_templates[0].id
        response = client.post(
            f"/api/marketplace/templates/{template_id}/import",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_import_unpublished_template_denied(self, client, test_templates, paid_user_with_token):
        """测试导入未发布模板被拒绝"""
        # 找到未发布的模板
        unpublished = None
        for t in test_templates:
            if not t.is_published:
                unpublished = t
                break

        if unpublished:
            response = client.post(
                f"/api/marketplace/templates/{unpublished.id}/import",
                headers=paid_user_with_token["headers"]
            )
            assert response.status_code == 404


# ═══════════════════════════════════════════════════════════
# 导入计数测试
# ═══════════════════════════════════════════════════════════

class TestImportCount:
    """导入计数测试"""

    def test_import_count_increment(self, client, test_templates, paid_user_with_token, db_session):
        """测试导入计数增加"""
        template_id = test_templates[0].id

        # 获取初始计数
        initial_count = test_templates[0].import_count

        # 导入模板
        client.post(
            f"/api/marketplace/templates/{template_id}/import",
            headers=paid_user_with_token["headers"]
        )

        # 刷新并检查计数
        db_session.refresh(test_templates[0])
        assert test_templates[0].import_count == initial_count + 1