# -*- coding: utf-8 -*-
"""
Prompt 版本历史 API 测试

测试 Prompt 保存、历史查询、版本回滚等功能
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from src.database.models import User, UserPrompt, UserPromptHistory


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def prompt_test_user(db_session):
    """创建测试用户（有使用次数）"""
    from src.auth.utils.password_handler import hash_password
    import secrets

    password_hash = hash_password("TestPassword123!")
    invite_code = "PROMPT-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

    user = User(
        email="prompt_test@example.com",
        password_hash=password_hash,
        nickname="PromptTestUser",
        invite_code=invite_code,
        usage_count=100,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def prompt_user_token(prompt_test_user):
    """用户访问令牌"""
    from src.auth.utils.jwt_handler import create_access_token
    return create_access_token(
        user_id=prompt_test_user.id,
        email=prompt_test_user.email,
        usage_count=prompt_test_user.usage_count
    )


@pytest.fixture
def prompt_user_headers(prompt_user_token):
    """用户认证头"""
    return {"Authorization": f"Bearer {prompt_user_token}"}


# ═══════════════════════════════════════════════════════════
# Prompt 配置测试
# ═══════════════════════════════════════════════════════════

class TestPromptConfig:
    """Prompt 配置测试"""

    def test_get_all_prompts(self, client, prompt_user_headers):
        """测试获取所有 Prompt 配置"""
        response = client.get(
            "/api/user-config/prompt",
            headers=prompt_user_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "prompts" in data
        assert len(data["prompts"]) == 6  # 6 个工具类型 (mission, mission_analysis, bounty, bounty_analysis, alpha, revenue)

    def test_get_prompt_invalid_tool_type(self, client, prompt_user_headers):
        """测试无效的工具类型"""
        response = client.get(
            "/api/user-config/prompt/invalid_type",
            headers=prompt_user_headers
        )
        assert response.status_code == 400

    def test_save_prompt_invalid_tool_type(self, client, prompt_user_headers):
        """测试保存无效工具类型的 Prompt"""
        response = client.put(
            "/api/user-config/prompt/invalid_type",
            headers=prompt_user_headers,
            json={"content": "测试内容"}
        )
        assert response.status_code == 400

    def test_save_prompt_unauthorized(self, client):
        """测试未登录保存 Prompt"""
        response = client.put(
            "/api/user-config/prompt/mission",
            json={"content": "测试内容"}
        )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# Prompt 历史查询测试
# ═══════════════════════════════════════════════════════════

class TestPromptHistory:
    """Prompt 历史查询测试"""

    def test_get_prompt_history(self, client, prompt_user_headers):
        """测试获取 Prompt 历史版本"""
        response = client.get(
            "/api/user-config/prompt/mission/history",
            headers=prompt_user_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "history" in data
        assert "tool_type" in data

    def test_get_history_invalid_tool_type(self, client, prompt_user_headers):
        """测试无效工具类型的历史查询"""
        response = client.get(
            "/api/user-config/prompt/invalid_type/history",
            headers=prompt_user_headers
        )
        assert response.status_code == 400

    def test_get_history_unauthorized(self, client):
        """测试未登录获取历史"""
        response = client.get(
            "/api/user-config/prompt/mission/history"
        )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# Prompt 回滚测试
# ═══════════════════════════════════════════════════════════

class TestPromptRollback:
    """Prompt 回滚测试"""

    def test_rollback_to_nonexistent_version(self, client, prompt_user_headers):
        """测试回滚到不存在的版本"""
        response = client.post(
            "/api/user-config/prompt/mission/rollback",
            headers=prompt_user_headers,
            json={"version": 999}
        )
        assert response.status_code == 404

    def test_rollback_invalid_tool_type(self, client, prompt_user_headers):
        """测试无效工具类型的回滚"""
        response = client.post(
            "/api/user-config/prompt/invalid_type/rollback",
            headers=prompt_user_headers,
            json={"version": 1}
        )
        assert response.status_code == 400

    def test_rollback_unauthorized(self, client):
        """测试未登录回滚"""
        response = client.post(
            "/api/user-config/prompt/mission/rollback",
            json={"version": 1}
        )
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════
# Prompt 重置测试
# ═══════════════════════════════════════════════════════════

class TestPromptReset:
    """Prompt 重置测试"""

    def test_reset_prompt_invalid_tool_type(self, client, prompt_user_headers):
        """测试重置无效工具类型的 Prompt"""
        response = client.delete(
            "/api/user-config/prompt/invalid_type",
            headers=prompt_user_headers
        )
        assert response.status_code == 400

    def test_reset_prompt_unauthorized(self, client):
        """测试未登录重置 Prompt"""
        response = client.delete(
            "/api/user-config/prompt/mission"
        )
        assert response.status_code == 401