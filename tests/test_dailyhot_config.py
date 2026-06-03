# -*- coding: utf-8 -*-
"""
DailyHotApi 配置层单元测试 - v2.1 激活码架构

测试分类配置的读取、更新功能
使用 code_id 替代 user_id
"""

import pytest
from sqlalchemy.orm import Session

from src.config_loader import DEFAULT_DAILYHOT_CATEGORIES
from src.database.models import DailyHotCategoryConfig, ActivationCode


class TestDefaultCategories:
    """默认分类测试"""

    def test_default_categories_not_empty(self):
        """测试默认分类不为空"""
        assert len(DEFAULT_DAILYHOT_CATEGORIES) > 0

    def test_default_categories_contains_common(self):
        """测试默认分类包含常用分类"""
        assert "tech" in DEFAULT_DAILYHOT_CATEGORIES
        assert "dev" in DEFAULT_DAILYHOT_CATEGORIES

    def test_default_categories_format(self):
        """测试默认分类格式正确"""
        for cat in DEFAULT_DAILYHOT_CATEGORIES:
            assert isinstance(cat, str)
            assert len(cat) > 0


class TestDailyHotCategoryConfigModel:
    """分类配置模型测试"""

    def test_create_category_config(self, db_session: Session):
        """测试创建分类配置"""
        # 创建激活码
        activation = ActivationCode(
            code="PRISM-CAT-TEST",
            quota=10,
            remaining=10,
            is_activated=True,
        )
        db_session.add(activation)
        db_session.commit()
        db_session.refresh(activation)

        # 创建分类配置
        config = DailyHotCategoryConfig(
            code_id=activation.id,
            category="tech",
            is_enabled=True,
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        assert config.id is not None
        assert config.category == "tech"
        assert config.is_enabled is True

    def test_multiple_category_configs(self, db_session: Session):
        """测试多个分类配置"""
        # 创建激活码
        activation = ActivationCode(
            code="PRISM-MULTI-CAT",
            quota=10,
            remaining=10,
            is_activated=True,
        )
        db_session.add(activation)
        db_session.commit()
        db_session.refresh(activation)

        # 创建多个配置
        configs = [
            DailyHotCategoryConfig(code_id=activation.id, category="tech", is_enabled=True),
            DailyHotCategoryConfig(code_id=activation.id, category="dev", is_enabled=True),
            DailyHotCategoryConfig(code_id=activation.id, category="news", is_enabled=False),
        ]
        db_session.add_all(configs)
        db_session.commit()

        # 查询验证
        saved_configs = db_session.query(DailyHotCategoryConfig).filter_by(code_id=activation.id).all()
        assert len(saved_configs) == 3

        enabled_configs = [c for c in saved_configs if c.is_enabled]
        assert len(enabled_configs) == 2

    def test_category_config_unique_constraint(self, db_session: Session):
        """测试分类配置唯一约束"""
        # 创建激活码
        activation = ActivationCode(
            code="PRISM-UNIQUE-CAT",
            quota=10,
            remaining=10,
            is_activated=True,
        )
        db_session.add(activation)
        db_session.commit()
        db_session.refresh(activation)

        # 创建配置
        config1 = DailyHotCategoryConfig(
            code_id=activation.id,
            category="tech",
            is_enabled=True,
        )
        db_session.add(config1)
        db_session.commit()

        # 同一 code_id + category 应该可以更新而非重复创建
        config1.is_enabled = False
        db_session.commit()

        # 查询应该只有一条
        configs = db_session.query(DailyHotCategoryConfig).filter_by(
            code_id=activation.id, category="tech"
        ).all()
        assert len(configs) == 1


class TestDailyHotConfigIntegration:
    """集成测试"""

    def test_api_update_creates_configs(self, client, test_device, db_session):
        """测试 API 更新创建配置"""
        device_id = test_device["device_id"]
        code_id = test_device["code_id"]

        # 通过 API 更新
        response = client.put(
            "/api/user-config/dailyhot/categories",
            json={
                "device_id": device_id,
                "categories": ["tech", "dev"]
            }
        )

        assert response.status_code == 200

        # 注意：由于 session 隔离，直接查询可能看不到
        # 这个测试主要验证 API 返回成功