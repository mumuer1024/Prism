# src/user/__init__.py
"""
用户模块
提供用户信息、兑换码充值、邀请统计等功能
"""

from src.user.router import router as user_router
from src.user.service import UserService

__all__ = ["user_router", "UserService"]