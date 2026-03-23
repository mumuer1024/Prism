# -*- coding: utf-8 -*-
"""
FastAPI 依赖注入

提供认证相关的依赖注入函数
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.crud import get_user_by_id
from src.database.models import User
from src.auth.utils.jwt_handler import verify_access_token
from src.config import settings

# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前登录用户（必须登录）
    
    Args:
        credentials: HTTP Bearer 凭证
        db: 数据库会话
    
    Returns:
        User: 当前用户对象
    
    Raises:
        HTTPException: 未提供 Token 或 Token 无效
    """
    # 检查功能开关
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # 验证 Token
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户 ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查询用户
    user = get_user_by_id(db, int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )
    
    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    获取当前用户（可选，未登录返回 None）
    
    Args:
        credentials: HTTP Bearer 凭证
        db: 数据库会话
    
    Returns:
        Optional[User]: 当前用户对象，未登录返回 None
    """
    # 检查功能开关
    if not settings.FEATURE_USER_SYSTEM:
        return None
    
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # 验证 Token
    payload = verify_access_token(token)
    
    if not payload:
        return None
    
    # 获取用户 ID
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    # 查询用户
    user = get_user_by_id(db, int(user_id))
    
    if not user or not user.is_active:
        return None
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 当前活跃用户
    
    Raises:
        HTTPException: 用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前已验证用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 当前已验证用户
    
    Raises:
        HTTPException: 用户未验证邮箱
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先验证邮箱"
        )
    return current_user


async def get_user_with_usage(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取有使用次数的用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 有使用次数的用户
    
    Raises:
        HTTPException: 用户没有使用次数
    """
    if current_user.usage_count <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="使用次数不足，请充值"
        )
    return current_user


class RateLimiter:
    """
    简单的速率限制器
    
    用于限制 API 调用频率
    """
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        # TODO: 实现基于 Redis 的速率限制
    
    async def __call__(self, current_user: User = Depends(get_current_user)):
        # 暂时不做限制
        return current_user