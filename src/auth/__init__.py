"""
Prism V2.0 认证模块

提供用户注册、登录、OAuth 认证等功能
"""

from .router import router as auth_router

__all__ = ['auth_router']