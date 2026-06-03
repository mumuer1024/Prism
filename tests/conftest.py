# -*- coding: utf-8 -*-
"""
pytest 配置和 fixtures - v2.1 激活码架构

提供测试所需的数据库会话、测试客户端、测试数据等 fixtures
"""
import pytest
import asyncio
import os
import sys
import secrets
from datetime import datetime, timedelta
from typing import Generator

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.database.models import (
    Base,
    ActivationCode,
    Device,
    ReferralCode,
    AnonymousUsage,
    AdminUser,
    AuditLog,
    UserPrompt,
    UserSource,
    MarketplaceTemplate,
)
from src.database.connection import get_db
from src.database import crud
from src.activation.service import ActivationService
from src.usage.service import UsageService
from src.config import settings


# ═══════════════════════════════════════════════════════════
# 测试数据库配置
# ═══════════════════════════════════════════════════════════

TEST_DATABASE_URL = "sqlite:///:memory:"


# ═══════════════════════════════════════════════════════════
# 事件循环 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def event_loop():
    """创建会话级别的事件循环"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ═══════════════════════════════════════════════════════════
# 数据库 fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def db_engine():
    """创建测试数据库引擎"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════
# FastAPI 客户端 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def client(db_session: Session):
    """创建测试客户端"""
    from fastapi.testclient import TestClient
    from server import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════
# 服务层 fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def activation_service(db_session: Session) -> ActivationService:
    """激活码服务实例"""
    return ActivationService(db_session)


@pytest.fixture
def usage_service(db_session: Session) -> UsageService:
    """使用次数服务实例"""
    return UsageService(db_session)


# ═══════════════════════════════════════════════════════════
# 激活码 fixture
# ═══════════════════════════════════════════════════════════

def generate_activation_code() -> str:
    """生成测试激活码格式"""
    return "PRISM-" + '-'.join(
        ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(4))
        for _ in range(3)
    )


def generate_device_id() -> str:
    """生成测试设备ID"""
    return "DEV-" + secrets.token_hex(16)


@pytest.fixture
def test_activation_code(db_session: Session) -> dict:
    """创建测试激活码"""
    code = generate_activation_code()

    activation = ActivationCode(
        code=code,
        quota=10,  # 购买次数
        remaining=10,  # 剩余次数
        is_activated=True,
        activated_at=datetime.utcnow(),
    )
    db_session.add(activation)
    db_session.commit()
    db_session.refresh(activation)

    return {
        "activation": activation,
        "code": code,
        "code_id": activation.id,
    }


@pytest.fixture
def test_device(db_session: Session, test_activation_code: dict) -> dict:
    """创建测试设备绑定"""
    device_id = generate_device_id()
    code_id = test_activation_code["code_id"]

    device = Device(
        device_id=device_id,
        code_id=code_id,
        device_name="Test Device",
        last_seen=datetime.utcnow(),
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)

    return {
        "device": device,
        "device_id": device_id,
        "code_id": code_id,
    }


@pytest.fixture
def test_referral_code(db_session: Session, test_activation_code: dict) -> dict:
    """创建测试推荐码"""
    ref_code = "REF-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(6))
    code_id = test_activation_code["code_id"]

    referral = ReferralCode(
        referral_code=ref_code,
        code_id=code_id,
        referral_count=0,
        total_rewarded=0,
    )
    db_session.add(referral)
    db_session.commit()
    db_session.refresh(referral)

    return {
        "referral": referral,
        "ref_code": ref_code,
        "code_id": code_id,
    }


# ═══════════════════════════════════════════════════════════
# 匿名用户 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def test_visitor_id() -> str:
    """生成测试访客ID"""
    return "VIS-" + secrets.token_hex(16)


@pytest.fixture
def test_anonymous_usage(db_session: Session, test_visitor_id: str) -> AnonymousUsage:
    """创建匿名用户使用记录"""
    anon = AnonymousUsage(
        visitor_id=test_visitor_id,
        daily_count=0,
        daily_date=datetime.utcnow().strftime("%Y-%m-%d"),
    )
    db_session.add(anon)
    db_session.commit()
    db_session.refresh(anon)
    return anon


# ═══════════════════════════════════════════════════════════
# 管理员 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def test_admin(db_session: Session) -> AdminUser:
    """创建测试管理员"""
    import hashlib
    
    password_hash = hashlib.sha256("admin123".encode()).hexdigest()
    
    admin = AdminUser(
        username="test_admin",
        password_hash=password_hash,
        created_at=datetime.utcnow(),
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


# ═══════════════════════════════════════════════════════════
# 预设模板 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def test_template(db_session: Session) -> MarketplaceTemplate:
    """创建测试预设模板"""
    template = MarketplaceTemplate(
        title="测试模板",
        description="用于测试的模板",
        tool_type="mission",
        prompt_content="测试内容 {{DATA}}",
        tags='["测试"]',
        is_official=True,
        is_published=True,
        import_count=0,
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


# ═══════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════

def assert_response_success(response, status_code: int = 200):
    """断言响应成功"""
    assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"


def assert_response_error(response, status_code: int = 400):
    """断言响应错误"""
    assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}: {response.text}"


def get_response_data(response) -> dict:
    """获取响应数据"""
    return response.json()


# ═══════════════════════════════════════════════════════════
# 兼容旧测试的别名（标记 deprecated）
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def test_user_data() -> dict:
    """已废弃：旧用户系统数据"""
    pytest.skip("旧用户系统已废弃")


@pytest.fixture
def registered_user() -> dict:
    """已废弃：旧用户系统"""
    pytest.skip("旧用户系统已废弃")


@pytest.fixture
def auth_headers() -> dict:
    """已废弃：JWT认证"""
    pytest.skip("JWT认证已废弃")