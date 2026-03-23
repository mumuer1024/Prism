"""
pytest 配置和 fixtures

提供测试所需的数据库会话、测试客户端、测试数据等 fixtures
"""
import pytest
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Generator

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.database.models import Base, User, RedemptionCode, InviteRecord
from src.database.connection import get_db
from src.auth.service import AuthService
from src.auth.utils import PasswordHandler, JWTHandler
from src.auth.utils.password_handler import hash_password
from src.auth.utils.jwt_handler import create_access_token
from src.user.service import UserService
from src.usage.service import UsageService
from src.config import settings


# ═══════════════════════════════════════════════════════════
# 测试数据库配置
# ═══════════════════════════════════════════════════════════

# 使用内存 SQLite 数据库进行测试
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

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    yield engine

    # 清理：删除所有表
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

    # 覆盖数据库依赖
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # 清理依赖覆盖
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════
# 测试数据 fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def test_user_data() -> dict:
    """测试用户数据"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "nickname": "TestUser"
    }


@pytest.fixture
def test_user_data_2() -> dict:
    """第二个测试用户数据（用于邀请测试）"""
    return {
        "email": "test2@example.com",
        "password": "TestPassword456!",
        "nickname": "TestUser2"
    }


@pytest.fixture
def test_admin_data() -> dict:
    """测试管理员数据"""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "nickname": "Admin"
    }


@pytest.fixture
def weak_password_data() -> dict:
    """弱密码测试数据"""
    return {
        "email": "weak@example.com",
        "password": "123",  # 弱密码
        "nickname": "WeakUser"
    }


@pytest.fixture
def invalid_email_data() -> dict:
    """无效邮箱测试数据"""
    return {
        "email": "invalid-email",
        "password": "TestPassword123!",
        "nickname": "InvalidUser"
    }


# ═══════════════════════════════════════════════════════════
# 服务层 fixtures
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def auth_service(db_session: Session) -> AuthService:
    """认证服务实例"""
    return AuthService(db_session)


@pytest.fixture
def user_service(db_session: Session) -> UserService:
    """用户服务实例"""
    return UserService(db_session)


@pytest.fixture
def usage_service(db_session: Session) -> UsageService:
    """使用次数服务实例"""
    return UsageService(db_session)


# ═══════════════════════════════════════════════════════════
# 已注册用户 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def registered_user(db_session: Session, test_user_data: dict) -> dict:
    """已注册的用户（返回用户信息和 token）"""
    import secrets
    
    # 直接创建用户（同步方式）
    password_hash = hash_password(test_user_data["password"])
    invite_code = "TEST-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
    
    user = User(
        email=test_user_data["email"],
        password_hash=password_hash,
        nickname=test_user_data.get("nickname"),
        invite_code=invite_code,
        usage_count=0,
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 生成 token
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        usage_count=user.usage_count
    )

    return {
        "user": user,
        "access_token": access_token,
        "token_type": "bearer"
    }


@pytest.fixture
def registered_user_2(db_session: Session, test_user_data_2: dict) -> dict:
    """第二个已注册的用户"""
    import secrets
    
    password_hash = hash_password(test_user_data_2["password"])
    invite_code = "TEST-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
    
    user = User(
        email=test_user_data_2["email"],
        password_hash=password_hash,
        nickname=test_user_data_2.get("nickname"),
        invite_code=invite_code,
        usage_count=0,
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        usage_count=user.usage_count
    )

    return {
        "user": user,
        "access_token": access_token,
        "token_type": "bearer"
    }


# ═══════════════════════════════════════════════════════════
# 付费用户 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def paid_user(db_session: Session, test_user_data: dict) -> dict:
    """付费用户（有使用次数）"""
    import secrets
    
    password_hash = hash_password(test_user_data["password"])
    invite_code = "TEST-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
    
    user = User(
        email=test_user_data["email"],
        password_hash=password_hash,
        nickname=test_user_data.get("nickname"),
        invite_code=invite_code,
        usage_count=100,  # 直接设置使用次数
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        usage_count=user.usage_count
    )

    return {
        "user": user,
        "access_token": access_token,
        "token_type": "bearer"
    }


# ═══════════════════════════════════════════════════════════
# 兑换码 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def redemption_code(db_session: Session) -> str:
    """创建测试兑换码"""
    import secrets
    
    # 生成兑换码
    code = "PRISM-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

    redemption = RedemptionCode(
        code=code,
        count=10,  # 10 次使用次数
        used=False,
        batch_id="TEST-BATCH",
        created_at=datetime.utcnow()
    )
    db_session.add(redemption)
    db_session.commit()

    return code


# 保留旧名称的别名，兼容旧测试
@pytest.fixture
def activation_code(redemption_code: str) -> str:
    """创建测试激活码（兼容旧测试）"""
    return redemption_code


# ═══════════════════════════════════════════════════════════
# 邀请码 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def invite_code(db_session: Session) -> str:
    """创建一个已注册用户的邀请码"""
    import secrets

    # 创建一个用户来获取邀请码
    password_hash = hash_password("TestPassword123!")
    code = "INV-" + ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

    user = User(
        email="inviter_fixture@example.com",
        password_hash=password_hash,
        invite_code=code,
        usage_count=0,
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()

    return code


# ═══════════════════════════════════════════════════════════
# 认证头 fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def auth_headers(registered_user: dict) -> dict:
    """认证请求头"""
    return {
        "Authorization": f"{registered_user['token_type']} {registered_user['access_token']}"
    }


@pytest.fixture
def auth_headers_paid(paid_user: dict) -> dict:
    """付费用户认证请求头"""
    return {
        "Authorization": f"{paid_user['token_type']} {paid_user['access_token']}"
    }


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