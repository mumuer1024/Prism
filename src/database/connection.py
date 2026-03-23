# -*- coding: utf-8 -*-
"""
数据库连接模块

提供 SQLAlchemy 数据库连接和会话管理
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
            db.query(User).all()
    
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
    
    创建所有表结构
    """
    # 确保数据目录存在
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 导入所有模型以确保它们被注册
    from src.database.models import (
        User,
        VerificationCode,
        RefreshToken,
        RedemptionCode,
        TopupRecord,
        InviteRecord,
        Admin,
        SchemaVersion,
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("数据库初始化完成")
    
    # 检查并运行迁移脚本
    _run_migrations()


def _run_migrations():
    """
    运行数据库迁移脚本
    
    检查 schema_version 表，执行未应用的迁移
    """
    db = SessionLocal()
    try:
        # 检查是否需要初始化版本表
        from src.database.models import SchemaVersion
        
        # 获取当前版本
        latest_version = db.query(SchemaVersion).order_by(
            SchemaVersion.version.desc()
        ).first()
        
        current_version = latest_version.version if latest_version else 0
        
        if current_version < 1:
            # 版本 1: 初始表结构（已在 create_all 中创建）
            version_record = SchemaVersion(
                version=1,
                description="初始表结构：用户、验证码、Token、兑换码等"
            )
            db.add(version_record)
            db.commit()
            logger.info("数据库迁移: 版本 1 已应用")
        
        # 未来迁移示例：
        # if current_version < 2:
        #     _apply_migration_v2()
        
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