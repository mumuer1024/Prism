# -*- coding: utf-8 -*-
"""
数据库连接模块

提供 SQLAlchemy 数据库连接和会话管理（v2.1 激活码架构）
"""

import os
import logging
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

from src.config import settings

logger = logging.getLogger(__name__)

# 创建 Base 类
Base = declarative_base()

# 数据库 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'prism.db')}"
)

# 创建引擎
if DATABASE_URL.startswith("sqlite"):
    # SQLite 配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG,
    )
else:
    # PostgreSQL / MySQL 配置
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.DEBUG,
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 依赖注入：获取数据库会话

    使用方式：
        @router.post("/example")
        def example(db: Session = Depends(get_db)):
            ...

    Yields:
        Session: SQLAlchemy 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    上下文管理器：获取数据库会话

    使用方式：
        with get_db_context() as db:
            db.query(ActivationCode).all()

    Yields:
        Session: SQLAlchemy 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def init_database():
    """
    初始化数据库

    创建所有表结构（激活码架构）
    """
    # 确保数据目录存在
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # 导入所有模型以确保它们被注册
    from src.database.models import (
        ActivationCode,
        Device,
        ReferralCode,
        AnonymousUsage,
        AdminUser,
        AuditLog,
        UserPrompt,
        UserPromptHistory,
        UserSource,
        UserConfig,
        DailyHotCategoryConfig,
        MarketplaceTemplate,
        SchemaVersion,
    )

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库初始化完成（激活码架构）")

    # 检查并运行迁移脚本
    _run_migrations()


def _run_migrations():
    """
    运行数据库迁移脚本

    版本从 1 开始，记录激活码架构
    """
    db = SessionLocal()
    try:
        from src.database.models import SchemaVersion

        # 获取当前版本
        latest_version = db.query(SchemaVersion).order_by(
            SchemaVersion.version.desc()
        ).first()

        current_version = latest_version.version if latest_version else 0

        if current_version < 1:
            # 版本 1: 激活码架构初始表结构
            # 表已在 create_all 中创建，只需记录版本
            version_record = SchemaVersion(
                version=1,
                description="激活码架构：activation_codes, devices, referral_codes, anonymous_usage, admin_users, audit_logs, user_prompts, user_sources, user_configs, dailyhot_category_config, marketplace_templates"
            )
            db.add(version_record)
            db.commit()
            logger.info("数据库迁移: 版本 1 已应用 - 激活码架构初始化")

        if current_version < 2:
            # 版本 2: 插入官方预设模板
            from src.database.models import MarketplaceTemplate
            from src.defaults.official_templates import OFFICIAL_TEMPLATES
            import json

            # 清空现有官方模板
            db.query(MarketplaceTemplate).filter(
                MarketplaceTemplate.is_official == True
            ).delete()

            # 插入新模板
            for template_data in OFFICIAL_TEMPLATES:
                template = MarketplaceTemplate(
                    title=template_data["title"],
                    description=template_data["description"],
                    tool_type=template_data["tool_type"],
                    prompt_content=template_data["prompt_content"],
                    tags=json.dumps(template_data["tags"], ensure_ascii=False),
                    is_official=template_data["is_official"],
                    is_published=template_data["is_published"],
                    import_count=template_data.get("import_count", 0),
                )
                db.add(template)

            db.commit()

            version_record = SchemaVersion(
                version=2,
                description="插入 11 个官方预设模板"
            )
            db.add(version_record)
            db.commit()
            logger.info("数据库迁移: 版本 2 已应用 - 插入官方模板")

        if current_version < 3:
            # 版本 3: 创建默认管理员账号
            from src.database.models import AdminUser
            import bcrypt

            # 检查是否已存在管理员
            existing_admin = db.query(AdminUser).filter(
                AdminUser.username == "admin"
            ).first()

            if not existing_admin:
                # 创建默认管理员（密码: admin123，建议首次登录后修改）
                default_password = "admin123"
                password_hash = bcrypt.hashpw(
                    default_password.encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')

                admin = AdminUser(
                    username="admin",
                    password_hash=password_hash,
                    is_admin=True,
                )
                db.add(admin)
                db.commit()
                logger.info("数据库迁移: 版本 3 已应用 - 创建默认管理员（admin/admin123）")

            version_record = SchemaVersion(
                version=3,
                description="创建默认管理员账号（admin/admin123）"
            )
            db.add(version_record)
            db.commit()

    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        db.rollback()
    finally:
        db.close()


def close_database():
    """
    关闭数据库连接

    在应用关闭时调用
    """
    engine.dispose()
    logger.info("数据库连接已关闭")


# SQLite 优化：启用外键约束
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()