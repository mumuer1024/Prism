# -*- coding: utf-8 -*-
"""
激活码模块 - 依赖注入

提供激活码认证相关的依赖注入函数
替代原有的 JWT 用户认证系统
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import ActivationCode, AdminUser
from src.database import crud


async def get_activation_by_device_id(
    device_id: str,
    db: Session = Depends(get_db),
) -> Optional[ActivationCode]:
    """
    通过设备 ID 获取激活码（可选，未激活返回 None）

    Args:
        device_id: 设备 ID
        db: 数据库会话

    Returns:
        Optional[ActivationCode]: 激活码对象，未激活返回 None
    """
    if not device_id:
        return None

    return crud.get_activation_code_by_device_id(db, device_id)


async def require_activation(
    device_id: str,
    db: Session = Depends(get_db),
) -> ActivationCode:
    """
    要求已激活（必须提供有效的 device_id）

    Args:
        device_id: 设备 ID
        db: 数据库会话

    Returns:
        ActivationCode: 激活码对象

    Raises:
        HTTPException: 设备未绑定激活码
    """
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先激活激活码",
        )

    activation_code = crud.get_activation_code_by_device_id(db, device_id)

    if not activation_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="设备未绑定激活码",
        )

    if activation_code.remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="次数已用完，请购买新激活码",
        )

    return activation_code


async def require_quota(
    device_id: str,
    amount: int = 1,
    db: Session = Depends(get_db),
) -> ActivationCode:
    """
    要求有足够次数

    Args:
        device_id: 设备 ID
        amount: 需要的次数
        db: 数据库会话

    Returns:
        ActivationCode: 激活码对象

    Raises:
        HTTPException: 次数不足
    """
    activation_code = await require_activation(device_id, db)

    if activation_code.remaining < amount:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"次数不足，当前剩余 {activation_code.remaining} 次",
        )

    return activation_code


async def get_admin_user(
    username: str,
    password: str,
    db: Session = Depends(get_db),
) -> AdminUser:
    """
    验证管理员登录

    Args:
        username: 用户名
        password: 密码
        db: 数据库会话

    Returns:
        AdminUser: 管理员对象

    Raises:
        HTTPException: 认证失败
    """
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请提供用户名和密码",
        )

    admin = crud.verify_admin_password(db, username, password)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    return admin


async def require_admin(
    admin_id: int,
    db: Session = Depends(get_db),
) -> AdminUser:
    """
    要求管理员权限

    Args:
        admin_id: 管理员 ID
        db: 数据库会话

    Returns:
        AdminUser: 管理员对象

    Raises:
        HTTPException: 无管理员权限
    """
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    return admin


class ActivationInfo:
    """
    激活信息容器

    用于同时传递激活码和匿名用户信息
    """

    def __init__(
        self,
        activation_code: Optional[ActivationCode] = None,
        visitor_id: Optional[str] = None,
        is_activated: bool = False,
    ):
        self.activation_code = activation_code
        self.visitor_id = visitor_id
        self.is_activated = is_activated

    def has_quota(self) -> bool:
        """检查是否有次数"""
        if self.activation_code:
            return self.activation_code.remaining > 0
        return False

    def get_remaining(self) -> int:
        """获取剩余次数"""
        if self.activation_code:
            return self.activation_code.remaining
        return 0

    def get_code_id(self) -> Optional[int]:
        """获取激活码 ID"""
        if self.activation_code:
            return self.activation_code.id
        return None


async def get_activation_info(
    device_id: Optional[str] = None,
    visitor_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> ActivationInfo:
    """
    获取激活信息（统一处理已激活用户和匿名用户）

    Args:
        device_id: 设备 ID（已激活用户）
        visitor_id: 访客 ID（匿名用户）
        db: 数据库会话

    Returns:
        ActivationInfo: 激活信息容器
    """
    # 优先检查 device_id（已激活用户）
    if device_id:
        activation_code = crud.get_activation_code_by_device_id(db, device_id)
        if activation_code:
            return ActivationInfo(
                activation_code=activation_code,
                visitor_id=None,
                is_activated=True,
            )

    # 匿名用户
    return ActivationInfo(
        activation_code=None,
        visitor_id=visitor_id,
        is_activated=False,
    )