# -*- coding: utf-8 -*-
"""
预设广场 API 测试

测试模板列表、详情、导入等功能
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from src.database.models import User, MarketplaceTemplate


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    from src.auth.utils.password_handler import hash_password
    import secrets

    password_hash = hash_password("TestPassword123!")
    invite_code = "TEST-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

    user = User(
        email="test@example.com",
        password_hash=password_hash,
        nickname="TestUser",
        invite_code=invite_code,
        usage_count=100,  # 有使用次数
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def user_token(test_user):
    """用户访问令牌"""
    from src.auth.utils.jwt_handler import create_access_token
    return create_access_token(
        user_id=test_user.id,
        email=test_user.email,
        usage_count=test_user.usage_count
    )


@pytest.fixture
def user_headers(user_token):
    """用户认证头"""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def test_templates(db_session):
    """创建测试模板"""
    templates = []
    
    template_data = [
        {
            "title": "测试情报日报模板",
            "description": "用于测试的情报日报模板",
            "tool_type": "mission",
            "prompt_content": "# 测试日报\n日期: {date_str}\n内容: 测试内容",
            "tags": '["测试", "日报"]',
            "is_official": True,
            "is_published": True,
        },
        {
            "title": "测试Alpha雷达模板",
            "description": "用于测试的Alpha雷达模板",
            "tool_type": "alpha",
            "prompt_content": "Search for: {query}",
            "tags": '["测试", "Alpha"]',
            "is_official": True,
            "is_published": True,
        },
        {
            "title": "未发布模板",
            "description": "这个模板不应该被列出",
            "tool_type": "mission",
            "prompt_content": "未发布内容",
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
        assert data["total"] >= 2  # 至少有2个已发布模板

    def test_list_templates_with_tool_type_filter(self, client, test_templates):
        """测试按工具类型筛选模板"""
        response = client.get("/api/marketplace/templates?tool_type=mission")
        assert response.status_code == 200

        data = response.json()
        assert "templates" in data
        
        # 所有返回的模板都应该是 mission 类型
        for template in data["templates"]:
            assert template["tool_type"] == "mission"

    def test_list_templates_pagination(self, client, test_templates):
        """测试模板列表分页"""
        response = client.get("/api/marketplace/templates?skip=0&limit=1")
        assert response.status_code == 200

        data = response.json()
        assert len(data["templates"]) <= 1

    def test_list_templates_invalid_tool_type(self, client):
        """测试无效的工具类型"""
        response = client.get("/api/marketplace/templates?tool_type=invalid_type")
        assert response.status_code == 400

    def test_list_templates_exclude_unpublished(self, client, test_templates):
        """测试未发布模板不显示"""
        response = client.get("/api/marketplace/templates")
        assert response.status_code == 200

        data = response.json()
        titles = [t["title"] for t in data["templates"]]
        
        # 未发布模板不应该出现在列表中
        assert "未发布模板" not in titles


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
        assert "prompt_content" in data  # 详情应包含完整内容

    def test_get_template_detail_not_found(self, client):
        """测试获取不存在的模板"""
        response = client.get("/api/marketplace/templates/99999")
        assert response.status_code == 404

    def test_get_template_detail_unpublished(self, client, test_templates):
        """测试获取未发布模板详情"""
        # 未发布模板的ID
        unpublished_id = None
        for t in test_templates:
            if not t.is_published:
                unpublished_id = t.id
                break

        if unpublished_id:
            response = client.get(f"/api/marketplace/templates/{unpublished_id}")
            assert response.status_code == 404


# ═══════════════════════════════════════════════════════════
# 模板导入测试
# ═══════════════════════════════════════════════════════════

class TestTemplateImport:
    """模板导入测试"""

    def test_import_template_not_found(self, client, user_headers):
        """测试导入不存在的模板"""
        response = client.post(
            "/api/marketplace/templates/99999/import",
            headers=user_headers
        )
        assert response.status_code == 404

    def test_import_template_unauthorized(self, client, test_templates):
        """测试未登录导入模板"""
        template = test_templates[0]
        
        response = client.post(
            f"/api/marketplace/templates/{template.id}/import"
        )
        assert response.status_code == 401

    def test_import_template_no_usage_count(self, client, db_session, test_templates):
        """测试使用次数为0的用户导入模板"""
        from src.auth.utils.password_handler import hash_password
        import secrets
        from src.auth.utils.jwt_handler import create_access_token

        # 创建没有使用次数的用户
        password_hash = hash_password("NoUsage123!")
        invite_code = "NOUSE-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        
        user = User(
            email="nousage@example.com",
            password_hash=password_hash,
            nickname="NoUsageUser",
            invite_code=invite_code,
            usage_count=0,  # 没有使用次数
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
        headers = {"Authorization": f"Bearer {token}"}

        template = test_templates[0]
        response = client.post(
            f"/api/marketplace/templates/{template.id}/import",
            headers=headers
        )
        assert response.status_code == 403  # 权限不足