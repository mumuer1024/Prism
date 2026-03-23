# -*- coding: utf-8 -*-
"""
OAuth 认证模块
支持 GitHub、微信等第三方登录
"""

from src.auth.oauth.github import GitHubOAuthService
from src.auth.oauth.wechat import WeChatOAuthService
from src.auth.oauth.state import OAuthStateManager, state_manager
from src.auth.oauth.exceptions import (
    OAuthError,
    OAuthStateError,
    OAuthTokenError,
    OAuthUserError
)

__all__ = [
    "GitHubOAuthService",
    "WeChatOAuthService",
    "OAuthStateManager",
    "state_manager",
    "OAuthError",
    "OAuthStateError",
    "OAuthTokenError",
    "OAuthUserError"
]