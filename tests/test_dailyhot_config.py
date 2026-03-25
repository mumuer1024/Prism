# -*- coding: utf-8 -*-
"""
DailyHotApi 配置层单元测试

测试分类配置的读取、更新、初始化功能
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from src.config_loader import (
    get_user_dailyhot_categories,
    get_user_dailyhot_categories_detail,
    update_user_dailyhot_categories,
    init_user_dailyhot_categories,
    DEFAULT_DAILYHOT_CATEGORIES,
)
from src.database.models import DailyHotCategoryConfig


class TestGetUserDailyhotCategories:
    """测试获取用户分类配置"""

    def test_get_categories_new_user(self, db_session: Session):
        """测试新用户返回默认分类"""
        # 新用户没有配置记录
        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            # 模拟空查询结果
            with patch.object(db_session, 'query') as mock_query:
                mock_query.return_value.filter.return_value.all.return_value = []

                categories = get_user_dailyhot_categories(user_id=999)

        assert categories == DEFAULT_DAILYHOT_CATEGORIES

    def test_get_categories_existing_user(self, db_session: Session):
        """测试已有配置的用户返回自定义分类"""
        # 创建测试用户配置
        config1 = DailyHotCategoryConfig(
            user_id=1,
            category="tech",
            is_enabled=True,
        )
        config2 = DailyHotCategoryConfig(
            user_id=1,
            category="news",
            is_enabled=True,
        )
        config3 = DailyHotCategoryConfig(
            user_id=1,
            category="dev",
            is_enabled=False,
        )
        db_session.add_all([config1, config2, config3])
        db_session.commit()

        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            categories = get_user_dailyhot_categories(user_id=1)

        # 应该返回启用的分类
        assert "tech" in categories
        assert "news" in categories
        assert "dev" not in categories

    def test_get_categories_error_fallback(self, db_session: Session):
        """测试查询错误时返回默认值"""
        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.side_effect = Exception("Database error")

            categories = get_user_dailyhot_categories(user_id=1)

        assert categories == DEFAULT_DAILYHOT_CATEGORIES


class TestGetUserDailyhotCategoriesDetail:
    """测试获取分类配置详情"""

    def test_get_detail_new_user(self, db_session: Session):
        """测试新用户返回默认详情"""
        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            with patch.object(db_session, 'query') as mock_query:
                mock_query.return_value.filter.return_value.all.return_value = []

                detail = get_user_dailyhot_categories_detail(user_id=999)

        assert len(detail) == 4
        # 验证默认配置：tech 和 dev 默认启用
        tech_item = next((d for d in detail if d["category"] == "tech"), None)
        dev_item = next((d for d in detail if d["category"] == "dev"), None)
        news_item = next((d for d in detail if d["category"] == "news"), None)
        assert tech_item["is_enabled"] is True
        assert dev_item["is_enabled"] is True
        assert news_item["is_enabled"] is False

    def test_get_detail_existing_user(self, db_session: Session):
        """测试已有配置用户返回正确详情"""
        config1 = DailyHotCategoryConfig(
            user_id=1,
            category="tech",
            is_enabled=True,
        )
        config2 = DailyHotCategoryConfig(
            user_id=1,
            category="news",
            is_enabled=False,
        )
        db_session.add_all([config1, config2])
        db_session.commit()

        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            detail = get_user_dailyhot_categories_detail(user_id=1)

        assert len(detail) == 4
        tech_item = next((d for d in detail if d["category"] == "tech"), None)
        news_item = next((d for d in detail if d["category"] == "news"), None)
        assert tech_item["is_enabled"] is True
        assert news_item["is_enabled"] is False


class TestUpdateUserDailyhotCategories:
    """测试更新分类配置"""

    def test_update_categories_success(self, db_session: Session):
        """测试成功更新分类"""
        # 先创建一些配置
        config1 = DailyHotCategoryConfig(
            user_id=1,
            category="tech",
            is_enabled=True,
        )
        db_session.add(config1)
        db_session.commit()

        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            result = update_user_dailyhot_categories(
                user_id=1,
                categories=["tech", "dev", "news"]
            )

        assert result is True

    def test_update_categories_invalid_category(self, db_session: Session):
        """测试无效分类返回 False"""
        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            result = update_user_dailyhot_categories(
                user_id=1,
                categories=["tech", "invalid_category"]
            )

        assert result is False

    def test_update_categories_empty_list(self, db_session: Session):
        """测试空列表返回 False"""
        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            result = update_user_dailyhot_categories(
                user_id=1,
                categories=[]
            )

        assert result is False

    def test_update_categories_creates_new_records(self, db_session: Session):
        """测试更新时创建新记录"""
        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            result = update_user_dailyhot_categories(
                user_id=1,
                categories=["tech", "dev"]
            )

        assert result is True

        # 验证数据库记录
        configs = db_session.query(DailyHotCategoryConfig).filter(
            DailyHotCategoryConfig.user_id == 1
        ).all()
        assert len(configs) == 4  # 所有 4 个分类都应该有记录


class TestInitUserDailyhotCategories:
    """测试初始化分类配置"""

    def test_init_new_user(self, db_session: Session):
        """测试初始化新用户配置"""
        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            result = init_user_dailyhot_categories(user_id=1)

        assert result is True

        # 验证默认配置已创建
        configs = db_session.query(DailyHotCategoryConfig).filter(
            DailyHotCategoryConfig.user_id == 1
        ).all()
        assert len(configs) == 4

        # 验证 tech 和 dev 默认启用
        tech_config = next((c for c in configs if c.category == "tech"), None)
        dev_config = next((c for c in configs if c.category == "dev"), None)
        assert tech_config.is_enabled is True
        assert dev_config.is_enabled is True

    def test_init_existing_user_skip(self, db_session: Session):
        """测试已有配置用户跳过初始化"""
        # 先创建一个配置
        existing_config = DailyHotCategoryConfig(
            user_id=1,
            category="tech",
            is_enabled=False,  # 自定义配置
        )
        db_session.add(existing_config)
        db_session.commit()

        with patch('src.config_loader.get_db_context') as mock_db:
            mock_db.return_value.__enter__ = MagicMock(return_value=db_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            result = init_user_dailyhot_categories(user_id=1)

        assert result is True

        # 验证原有配置未被覆盖
        config = db_session.query(DailyHotCategoryConfig).filter(
            DailyHotCategoryConfig.user_id == 1,
            DailyHotCategoryConfig.category == "tech"
        ).first()
        assert config.is_enabled is False  # 保持原有值


class TestDefaultCategories:
    """测试默认分类常量"""

    def test_default_categories_value(self):
        """验证默认分类值"""
        assert DEFAULT_DAILYHOT_CATEGORIES == ["tech", "dev"]

    def test_default_categories_length(self):
        """验证默认分类数量"""
        assert len(DEFAULT_DAILYHOT_CATEGORIES) == 2

    def test_default_categories_are_valid(self):
        """验证默认分类都是有效分类"""
        valid_categories = ["tech", "dev", "news", "entertainment"]
        for cat in DEFAULT_DAILYHOT_CATEGORIES:
            assert cat in valid_categories


class TestCategoryConfigModel:
    """测试 DailyHotCategoryConfig 模型"""

    def test_model_creation(self, db_session: Session):
        """测试模型创建"""
        config = DailyHotCategoryConfig(
            user_id=1,
            category="tech",
            is_enabled=True,
        )
        db_session.add(config)
        db_session.commit()

        # 验证可以查询
        saved = db_session.query(DailyHotCategoryConfig).filter(
            DailyHotCategoryConfig.user_id == 1
        ).first()
        assert saved is not None
        assert saved.category == "tech"
        assert saved.is_enabled is True

    def test_unique_constraint(self, db_session: Session):
        """测试唯一约束（同一用户同一分类只能有一条记录）"""
        config1 = DailyHotCategoryConfig(
            user_id=1,
            category="tech",
            is_enabled=True,
        )
        db_session.add(config1)
        db_session.commit()

        # 尝试添加重复记录，应该抛出 IntegrityError
        config2 = DailyHotCategoryConfig(
            user_id=1,
            category="tech",
            is_enabled=False,
        )
        db_session.add(config2)

        # 应该抛出 IntegrityError
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            db_session.commit()