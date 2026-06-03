# -*- coding: utf-8 -*-
"""
管理员认证依赖

提供管理员登录验证的依赖注入函数
"""

import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import AdminUser
from src.config import settings

# 管理员 Session Token 存储（简单实现，生产环境应使用 Redis）
# 格式: {token: {admin_id, expires_at, ip}}
_admin_sessions: dict = {}

# Session 有效期（小时）
SESSION_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """密码哈希（使用 bcrypt）"""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """验证密码（使用 bcrypt）"""
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )


def create_admin_session(admin_id: int, ip: str) -> str:
    """创建管理员会话Token"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)
    _admin_sessions[token] = {
        "admin_id": admin_id,
        "expires_at": expires_at,
        "ip": ip,
    }
    return token


def get_admin_session(token: str) -> Optional[dict]:
    """获取管理员会话"""
    session = _admin_sessions.get(token)
    if not session:
        return None
    
    # 检查是否过期
    if session["expires_at"] < datetime.utcnow():
        del _admin_sessions[token]
        return None
    
    return session


def revoke_admin_session(token: str) -> bool:
    """撤销管理员会话"""
    if token in _admin_sessions:
        del _admin_sessions[token]
        return True
    return False


def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def get_admin_from_session(
    request: Request,
    db: Session = Depends(get_db),
) -> AdminUser:
    """
    从会话Token获取管理员
    
    Args:
        request: HTTP请求对象
        db: 数据库会话
    
    Returns:
        AdminUser: 管理员对象
    
    Raises:
        HTTPException: 未登录或会话无效
    """
    # 从 Header 或 Cookie 获取 Token
    token = request.headers.get("X-Admin-Token")
    if not token:
        token = request.cookies.get("admin_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录管理员账号",
        )
    
    # 验证会话
    session = get_admin_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员会话已过期，请重新登录",
        )
    
    # 验证IP（可选，增强安全性）
    current_ip = get_client_ip(request)
    # 注意：开发环境下IP可能变化，生产环境可启用严格验证
    
    # 查询管理员
    admin = db.query(AdminUser).filter(
        AdminUser.id == session["admin_id"]
    ).first()
    
    if not admin:
        revoke_admin_session(token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员账号已禁用",
        )
    
    return admin


async def get_admin_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[AdminUser]:
    """
    获取管理员（可选，未登录返回None）
    """
    token = request.headers.get("X-Admin-Token")
    if not token:
        token = request.cookies.get("admin_token")
    
    if not token:
        return None
    
    session = get_admin_session(token)
    if not session:
        return None
    
    admin = db.query(AdminUser).filter(
        AdminUser.id == session["admin_id"]
    ).first()
    
    return admin